"""RAFT dense optical flow via princeton-vl/RAFT (third_party)."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn.functional as F

from .base import FlowResult, OpticalFlowRunner

ROOT = Path(__file__).resolve().parents[2]
RAFT_CORE = ROOT / "third_party" / "RAFT" / "core"


class _InputPadder:
    """Pad H/W to multiples of 8 (same convention as RAFT sintel mode)."""

    def __init__(self, dims: Tuple[int, ...]) -> None:
        self.ht, self.wd = int(dims[-2]), int(dims[-1])
        pad_ht = (((self.ht // 8) + 1) * 8 - self.ht) % 8
        pad_wd = (((self.wd // 8) + 1) * 8 - self.wd) % 8
        self._pad = [pad_wd // 2, pad_wd - pad_wd // 2, pad_ht // 2, pad_ht - pad_ht // 2]

    def pad(self, *inputs: torch.Tensor) -> list[torch.Tensor]:
        return [F.pad(x, self._pad, mode="replicate") for x in inputs]

    def unpad(self, x: torch.Tensor) -> torch.Tensor:
        ht, wd = x.shape[-2:]
        c = [self._pad[2], ht - self._pad[3], self._pad[0], wd - self._pad[1]]
        return x[..., c[0] : c[1], c[2] : c[3]]


def _to_rgb_uint8(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    # OpenCV paths in this project feed BGR
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


class RaftRunner(OpticalFlowRunner):
    """Official RAFT forward → dense HxWx2 flow (pixels, img1→img2)."""

    kind = "dense"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        weights = self.config.get("weights")
        if not weights:
            raise NotImplementedError(
                "RAFT requires methods[].weights (e.g. weights/raft-sintel.pth)"
            )
        self.weights_path = Path(weights)
        if not self.weights_path.is_absolute():
            self.weights_path = ROOT / self.weights_path
        self.device = str(self.config.get("device", "cuda"))
        if self.device.startswith("cuda") and not torch.cuda.is_available():
            self.device = "cpu"
        self.iters = int(self.config.get("iters", 20))
        self.mixed_precision = bool(self.config.get("mixed_precision", False))
        self.small = bool(self.config.get("small", False))
        self._model: Optional[torch.nn.Module] = None

    def _ensure_model(self) -> torch.nn.Module:
        if self._model is not None:
            return self._model
        if not RAFT_CORE.is_dir():
            raise NotImplementedError(
                f"RAFT core not found at {RAFT_CORE}. "
                "Clone https://github.com/princeton-vl/RAFT into third_party/RAFT"
            )
        if not self.weights_path.is_file():
            raise NotImplementedError(f"RAFT weights missing: {self.weights_path}")

        core_str = str(RAFT_CORE)
        if core_str not in sys.path:
            sys.path.insert(0, core_str)

        # Inline import required: RAFT core is added to sys.path only after
        # verifying third_party/RAFT exists (not a fixed installable package).
        from raft import RAFT  # type: ignore

        args = Namespace(
            small=self.small,
            mixed_precision=self.mixed_precision,
            alternate_corr=False,
            dropout=0,
        )
        model = torch.nn.DataParallel(RAFT(args))
        state = torch.load(self.weights_path, map_location=self.device, weights_only=False)
        model.load_state_dict(state)
        model = model.module
        model.to(self.device)
        model.eval()
        self._model = model
        return model

    def predict(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        keypoints: Optional[np.ndarray] = None,
    ) -> FlowResult:
        model = self._ensure_model()
        rgb1 = _to_rgb_uint8(img1)
        rgb2 = _to_rgb_uint8(img2)
        h, w = rgb1.shape[:2]

        t1 = torch.from_numpy(rgb1).permute(2, 0, 1).float()[None].to(self.device)
        t2 = torch.from_numpy(rgb2).permute(2, 0, 1).float()[None].to(self.device)

        padder = _InputPadder(t1.shape)
        t1, t2 = padder.pad(t1, t2)

        with torch.no_grad():
            _flow_low, flow_up = model(t1, t2, iters=self.iters, test_mode=True)
            flow_up = padder.unpad(flow_up)

        flow = flow_up[0].permute(1, 2, 0).detach().cpu().numpy().astype(np.float32)
        if flow.shape[0] != h or flow.shape[1] != w:
            flow = cv2.resize(flow, (w, h), interpolation=cv2.INTER_LINEAR)
            # vectors already in pixel units of padded/unpadded grid — size match only

        result = FlowResult(
            kind="dense",
            flow_dense=flow,
            meta={"runner": "raft", "iters": self.iters, "device": self.device},
        )
        if keypoints is not None and len(keypoints) > 0:
            pts = np.asarray(keypoints, dtype=np.float32).reshape(-1, 2)
            xs = np.clip(np.round(pts[:, 0]).astype(int), 0, w - 1)
            ys = np.clip(np.round(pts[:, 1]).astype(int), 0, h - 1)
            disp = flow[ys, xs]
            result.points1 = pts
            result.points2 = pts + disp
            result.status = np.ones(len(pts), dtype=np.uint8)
        return result

    def close(self) -> None:
        self._model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
