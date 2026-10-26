"""Pyramidal Lucas–Kanade (sparse) via OpenCV."""

from __future__ import annotations

from typing import Any, Dict, Optional

import cv2
import numpy as np

from .base import FlowResult, OpticalFlowRunner


def _to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


class OpenCVLucasKanadeRunner(OpticalFlowRunner):
    kind = "sparse"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.lk_params = dict(
            winSize=tuple(self.config.get("win_size", [21, 21])),
            maxLevel=int(self.config.get("max_level", 3)),
            criteria=(
                cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                int(self.config.get("max_iter", 30)),
                float(self.config.get("eps", 0.01)),
            ),
        )
        self.detector = self.config.get("detector", "shi_tomasi")
        self.max_corners = int(self.config.get("max_corners", 500))
        self.quality_level = float(self.config.get("quality_level", 0.01))
        self.min_distance = float(self.config.get("min_distance", 8))
        self.block_size = int(self.config.get("block_size", 7))

    def detect_keypoints(self, gray: np.ndarray) -> np.ndarray:
        if self.detector == "fast":
            fast = cv2.FastFeatureDetector_create(
                threshold=int(self.config.get("fast_threshold", 20))
            )
            kps = fast.detect(gray, None)
            if not kps:
                return np.zeros((0, 1, 2), dtype=np.float32)
            pts = np.array([kp.pt for kp in kps], dtype=np.float32)
            if len(pts) > self.max_corners:
                pts = pts[: self.max_corners]
            return pts.reshape(-1, 1, 2)

        pts = cv2.goodFeaturesToTrack(
            gray,
            maxCorners=self.max_corners,
            qualityLevel=self.quality_level,
            minDistance=self.min_distance,
            blockSize=self.block_size,
        )
        if pts is None:
            return np.zeros((0, 1, 2), dtype=np.float32)
        return pts

    def predict(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        keypoints: Optional[np.ndarray] = None,
    ) -> FlowResult:
        g1 = _to_gray(img1)
        g2 = _to_gray(img2)

        if keypoints is None:
            p0 = self.detect_keypoints(g1)
        else:
            p0 = np.asarray(keypoints, dtype=np.float32).reshape(-1, 1, 2)

        if p0.shape[0] == 0:
            return FlowResult(
                kind="sparse",
                points1=np.zeros((0, 2), dtype=np.float32),
                points2=np.zeros((0, 2), dtype=np.float32),
                status=np.zeros((0,), dtype=np.uint8),
            )

        p1, st, _err = cv2.calcOpticalFlowPyrLK(g1, g2, p0, None, **self.lk_params)
        status = st.reshape(-1).astype(np.uint8)
        return FlowResult(
            kind="sparse",
            points1=p0.reshape(-1, 2),
            points2=p1.reshape(-1, 2),
            status=status,
            meta={"runner": "opencv_lk"},
        )
