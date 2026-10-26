"""Stub for neural dense optical flow (RAFT / SEA-RAFT / GMFlow / …).

Replace `predict` with a real forward pass after installing the official
repo and weights on the GPU evaluation machine. See README.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np

from .base import FlowResult, OpticalFlowRunner


class RaftStubRunner(OpticalFlowRunner):
    """Placeholder: raises until wired to a real model."""

    kind = "dense"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.weights = self.config.get("weights")
        self.device = self.config.get("device", "cuda")
        self._model = None

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        raise NotImplementedError(
            f"Neural runner '{self.method_id}' is a stub. "
            "On the GPU machine: install the official implementation, "
            "set methods[].weights in configs/default.yaml, and implement "
            "loading in RaftStubRunner._ensure_model / predict. "
            f"Expected weights path: {self.weights!r}, device={self.device!r}."
        )

    def predict(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        keypoints: Optional[np.ndarray] = None,
    ) -> FlowResult:
        self._ensure_model()
        # Unreachable until stub is replaced:
        h, w = img1.shape[:2]
        flow = np.zeros((h, w, 2), dtype=np.float32)
        return FlowResult(kind="dense", flow_dense=flow)
