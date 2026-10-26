"""Common interface for optical flow runners."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type

import numpy as np


@dataclass
class FlowResult:
    """Unified output: dense flow and/or sparse tracks."""

    kind: str  # dense | sparse | sparse_se2
    # Dense: HxWx2 float32, flow in pixels (dx, dy) from img1 -> img2
    flow_dense: Optional[np.ndarray] = None
    # Sparse: Nx2 points in img1, Nx2 points in img2, Nx1 status (0/1)
    points1: Optional[np.ndarray] = None
    points2: Optional[np.ndarray] = None
    status: Optional[np.ndarray] = None
    # Optional SE(2) params per track: [tx, ty, theta] (and scale if any)
    se2_params: Optional[np.ndarray] = None
    meta: Dict[str, Any] = field(default_factory=dict)


class OpticalFlowRunner(ABC):
    """predict(img1, img2) -> FlowResult; optional keypoints for sparse protocol."""

    method_id: str = "base"
    kind: str = "dense"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}

    @abstractmethod
    def predict(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        keypoints: Optional[np.ndarray] = None,
    ) -> FlowResult:
        """img1/img2: BGR or gray uint8 HxWxC or HxW."""

    def close(self) -> None:
        """Release GPU / external process resources."""


class RunnerRegistry:
    def __init__(self) -> None:
        self._classes: Dict[str, Type[OpticalFlowRunner]] = {}

    def register(self, method_id: str, cls: Type[OpticalFlowRunner]) -> None:
        self._classes[method_id] = cls

    def create(self, method_id: str, config: Optional[Dict[str, Any]] = None) -> OpticalFlowRunner:
        if method_id not in self._classes:
            raise KeyError(
                f"Unknown method '{method_id}'. Registered: {sorted(self._classes)}"
            )
        runner = self._classes[method_id](config=config)
        runner.method_id = method_id
        return runner

    def available(self) -> list[str]:
        return sorted(self._classes)
