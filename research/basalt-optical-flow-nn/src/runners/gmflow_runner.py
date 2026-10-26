"""GMFlow dense optical flow via haofeixu/gmflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np
import torch
import torch.nn.functional as F

from .base import FlowResult, OpticalFlowRunner
from ._third_party import ROOT, ensure_path, purge_modules

GMFLOW_ROOT = ROOT / "third_party" / "gmflow"
DEFAULT_WEIGHTS = ROOT / "weights" / "gmflow_sintel-0c07dcb3.pth"


def _to_rgb_uint8(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def _InputPadder(dims, mode: str = "sintel"):
    """Minimal padder (divisible by 8), same convention as GMFlow/RAFT."""

    class P:
        def __init__(self) -> None:
            self.ht, self.wd = int(dims[-2]), int(dims[-1])
            pad_ht = (((self.ht // 8) + 1) * 8 - self.ht) % 8
            pad_wd = (((self.wd // 8) + 1) * 8 - self.wd) % 8
            if mode == "sintel":
                self._pad = [pad_wd // 2, pad_wd - pad_wd // 2, pad_ht // 2, pad_ht - pad_ht // 2]
            else:
                self._pad = [pad_wd // 2, pad_wd - pad_wd // 2, 0, pad_ht]

        def pad(self, *inputs):
            return [F.pad(x, self._pad, mode="replicate") for x in inputs]

        def unpad(self, x):
            ht, wd = x.shape[-2:]
            c = [self._pad[2], ht - self._pad[3], self._pad[0], wd - self._pad[1]]
            return x[..., c[0] : c[1], c[2] : c[3]]

    return P()


class GMFlowRunner(OpticalFlowRunner):
    kind = "dense"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        weights = self.config.get("weights") or DEFAULT_WEIGHTS
        self.weights_path = Path(weights)
        if not self.weights_path.is_absolute():
            self.weights_path = ROOT / self.weights_path
        self.device = str(self.config.get("device", "cuda"))
        if self.device.startswith("cuda") and not torch.cuda.is_available():
            self.device = "cpu"
        # Defaults match scripts for sintel with refinement off (basic) or with
        self.num_scales = int(self.config.get("num_scales", 1))
        self.attn_splits_list = list(self.config.get("attn_splits_list", [2]))
        self.corr_radius_list = list(self.config.get("corr_radius_list", [-1]))
        self.prop_radius_list = list(self.config.get("prop_radius_list", [-1]))
        self._model: Optional[torch.nn.Module] = None

    def _ensure_model(self) -> torch.nn.Module:
        if self._model is not None:
            return self._model
        if not GMFLOW_ROOT.is_dir():
            raise NotImplementedError(
                f"GMFlow not found at {GMFLOW_ROOT}. "
                "Clone https://github.com/haofeixu/gmflow into third_party/gmflow"
            )
        if not self.weights_path.is_file():
            raise NotImplementedError(
                f"GMFlow weights missing: {self.weights_path}. "
                "Download pretrained models from the GMFlow Google Drive zip."
            )

        purge_modules(("gmflow",))
        ensure_path(GMFLOW_ROOT)

        from gmflow.gmflow import GMFlow  # type: ignore

        model = GMFlow(
            feature_channels=128,
            num_scales=self.num_scales,
            upsample_factor=8,
            num_head=1,
            attention_type="swin",
            ffn_dim_expansion=4,
            num_transformer_layers=6,
        )
        ckpt = torch.load(self.weights_path, map_location=self.device, weights_only=False)
        weights = ckpt["model"] if isinstance(ckpt, dict) and "model" in ckpt else ckpt
        model.load_state_dict(weights, strict=False)
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
            results = model(
                t1,
                t2,
                attn_splits_list=self.attn_splits_list,
                corr_radius_list=self.corr_radius_list,
                prop_radius_list=self.prop_radius_list,
                pred_bidir_flow=False,
            )
            flow = results["flow_preds"][-1]
            flow = padder.unpad(flow)

        flow_np = flow[0].permute(1, 2, 0).detach().cpu().numpy().astype(np.float32)
        if flow_np.shape[0] != h or flow_np.shape[1] != w:
            flow_np = cv2.resize(flow_np, (w, h), interpolation=cv2.INTER_LINEAR)

        result = FlowResult(
            kind="dense",
            flow_dense=flow_np,
            meta={"runner": "gmflow", "device": self.device},
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
        purge_modules(("gmflow",))
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
