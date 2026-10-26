"""Dense Farneback optical flow via OpenCV."""

from __future__ import annotations

from typing import Any, Dict, Optional

import cv2
import numpy as np

from .base import FlowResult, OpticalFlowRunner


def _to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


class OpenCVFarnebackRunner(OpticalFlowRunner):
    kind = "dense"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.fb_params = dict(
            pyr_scale=float(self.config.get("pyr_scale", 0.5)),
            levels=int(self.config.get("levels", 3)),
            winsize=int(self.config.get("winsize", 15)),
            iterations=int(self.config.get("iterations", 3)),
            poly_n=int(self.config.get("poly_n", 5)),
            poly_sigma=float(self.config.get("poly_sigma", 1.2)),
            flags=0,
        )

    def predict(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        keypoints: Optional[np.ndarray] = None,
    ) -> FlowResult:
        g1 = _to_gray(img1)
        g2 = _to_gray(img2)
        flow = cv2.calcOpticalFlowFarneback(g1, g2, None, **self.fb_params)
        # flow: HxWx2
        result = FlowResult(kind="dense", flow_dense=flow.astype(np.float32), meta={"runner": "farneback"})

        if keypoints is not None and len(keypoints) > 0:
            pts = np.asarray(keypoints, dtype=np.float32).reshape(-1, 2)
            h, w = flow.shape[:2]
            xs = np.clip(np.round(pts[:, 0]).astype(int), 0, w - 1)
            ys = np.clip(np.round(pts[:, 1]).astype(int), 0, h - 1)
            disp = flow[ys, xs]
            result.points1 = pts
            result.points2 = pts + disp
            result.status = np.ones(len(pts), dtype=np.uint8)

        return result
