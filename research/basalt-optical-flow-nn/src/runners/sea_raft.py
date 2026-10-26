"""SEA-RAFT dense optical flow via princeton-vl/SEA-RAFT (HuggingFace weights)."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np
import torch
import torch.nn.functional as F

from .base import FlowResult, OpticalFlowRunner
from ._third_party import ROOT, ensure_path, purge_raft_family

SEA_ROOT = ROOT / "third_party" / "SEA-RAFT"
SEA_CORE = SEA_ROOT / "core"
DEFAULT_CFG = SEA_ROOT / "config" / "eval" / "sintel-M.json"
DEFAULT_HF = "MemorySlices/Tartan-C-T-TSKH432x960-M"


def _to_rgb_uint8(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def _load_cfg(path: Path) -> Namespace:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    args = Namespace(**data)
    return args


class SeaRaftRunner(OpticalFlowRunner):
    kind = "dense"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        cfg_path = self.config.get("cfg") or DEFAULT_CFG
        self.cfg_path = Path(cfg_path)
        if not self.cfg_path.is_absolute():
            self.cfg_path = ROOT / self.cfg_path
        self.hf_url = str(self.config.get("hf_url") or self.config.get("weights") or DEFAULT_HF)
        self.device = str(self.config.get("device", "cuda"))
        if self.device.startswith("cuda") and not torch.cuda.is_available():
            self.device = "cpu"
        self._model: Optional[torch.nn.Module] = None
        self._args: Optional[Namespace] = None

    def _ensure_model(self) -> tuple[torch.nn.Module, Namespace]:
        if self._model is not None and self._args is not None:
            return self._model, self._args
        if not SEA_CORE.is_dir():
            raise NotImplementedError(
                f"SEA-RAFT not found at {SEA_CORE}. "
                "Clone https://github.com/princeton-vl/SEA-RAFT into third_party/SEA-RAFT"
            )
        if not self.cfg_path.is_file():
            raise NotImplementedError(f"SEA-RAFT cfg missing: {self.cfg_path}")

        purge_raft_family()
        ensure_path(SEA_CORE)
        ensure_path(SEA_ROOT)

        from raft import RAFT  # type: ignore

        args = _load_cfg(self.cfg_path)
        args.path = None
        args.url = self.hf_url
        args.device = self.device
        if self.config.get("iters") is not None:
            args.iters = int(self.config["iters"])

        model = RAFT.from_pretrained(self.hf_url, args=args)
        model = model.to(self.device)
        model.eval()
        self._model = model
        self._args = args
        return model, args

    def predict(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        keypoints: Optional[np.ndarray] = None,
    ) -> FlowResult:
        model, args = self._ensure_model()
        rgb1 = _to_rgb_uint8(img1)
        rgb2 = _to_rgb_uint8(img2)
        h, w = rgb1.shape[:2]

        t1 = torch.from_numpy(rgb1).permute(2, 0, 1).float()[None].to(self.device)
        t2 = torch.from_numpy(rgb2).permute(2, 0, 1).float()[None].to(self.device)

        scale = float(getattr(args, "scale", 0))
        with torch.no_grad():
            if scale != 0:
                t1s = F.interpolate(t1, scale_factor=2**scale, mode="bilinear", align_corners=False)
                t2s = F.interpolate(t2, scale_factor=2**scale, mode="bilinear", align_corners=False)
            else:
                t1s, t2s = t1, t2
            out = model(t1s, t2s, iters=int(args.iters), test_mode=True)
            flow = out["flow"][-1]
            if scale != 0:
                flow = F.interpolate(flow, scale_factor=0.5**scale, mode="bilinear", align_corners=False) * (
                    0.5**scale
                )

        flow_np = flow[0].permute(1, 2, 0).detach().cpu().numpy().astype(np.float32)
        if flow_np.shape[0] != h or flow_np.shape[1] != w:
            flow_np = cv2.resize(flow_np, (w, h), interpolation=cv2.INTER_LINEAR)

        result = FlowResult(
            kind="dense",
            flow_dense=flow_np,
            meta={"runner": "sea_raft", "hf_url": self.hf_url, "device": self.device},
        )
        if keypoints is not None and len(keypoints) > 0:
            pts = np.asarray(keypoints, dtype=np.float32).reshape(-1, 2)
            xs = np.clip(np.round(pts[:, 0]).astype(int), 0, w - 1)
            ys = np.clip(np.round(pts[:, 1]).astype(int), 0, h - 1)
            disp = flow_np[ys, xs]
            result.points1 = pts
            result.points2 = pts + disp
            result.status = np.ones(len(pts), dtype=np.uint8)
        return result

    def close(self) -> None:
        self._model = None
        self._args = None
        purge_raft_family()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
