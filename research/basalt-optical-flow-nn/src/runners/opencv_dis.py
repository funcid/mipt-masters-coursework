"""Dense Inverse Search (DIS) optical flow via OpenCV."""

from __future__ import annotations

from typing import Any, Dict, Optional

import cv2
import numpy as np

from .base import FlowResult, OpticalFlowRunner


def _to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


_PRESETS = {
    "ultrafast": cv2.DISOPTICAL_FLOW_PRESET_ULTRAFAST,
    "fast": cv2.DISOPTICAL_FLOW_PRESET_FAST,
    "medium": cv2.DISOPTICAL_FLOW_PRESET_MEDIUM,
}


class OpenCVDISRunner(OpticalFlowRunner):
    kind = "dense"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        preset_name = str(self.config.get("preset", "medium")).lower()
        preset = _PRESETS.get(preset_name, cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        self._dis = cv2.DISOpticalFlow_create(preset)

    def predict(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        keypoints: Optional[np.ndarray] = None,
    ) -> FlowResult:
        g1 = _to_gray(img1)
        g2 = _to_gray(img2)
        flow = self._dis.calc(g1, g2, None)
        result = FlowResult(
            kind="dense",
            flow_dense=flow.astype(np.float32),
            meta={"runner": "dis"},
        )
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
