"""Stub for Basalt SE2 sparse optical flow (teacher).

Basalt is C++ (https://gitlab.com/VladyslavUsenko/basalt). Typical integration:
  1. Build Basalt on the evaluation machine.
  2. Export per-frame tracks via a small CLI or bind the optical_flow module.
  3. Point configs/default.yaml methods.basalt_se2.binary at that CLI.

This stub documents the expected FlowResult contract (sparse_se2).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from .base import FlowResult, OpticalFlowRunner


class BasaltSE2StubRunner(OpticalFlowRunner):
    kind = "sparse_se2"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.binary = self.config.get("binary")
        self.basalt_config = self.config.get("config")

    def predict(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        keypoints: Optional[np.ndarray] = None,
    ) -> FlowResult:
        if not self.binary:
            raise NotImplementedError(
                "Basalt SE2 runner: set methods.basalt_se2.binary in "
                "configs/default.yaml to a CLI that prints tracks, or replace "
                "this stub with a pybind/ctypes wrapper around Basalt optical_flow."
            )

        binary = Path(self.binary)
        if not binary.exists():
            raise FileNotFoundError(f"Basalt binary not found: {binary}")

        # Example contract for a future CLI:
        #   basalt_of --img1 a.png --img2 b.png [--keypoints pts.npy] -> NPZ
        # with arrays: points1, points2, status, se2_params
        raise NotImplementedError(
            "Basalt binary is set, but CLI I/O is not wired yet. "
            f"Implement subprocess protocol for {binary}. "
            f"Optional config: {self.basalt_config!r}."
        )

    def run_cli_example(self, img1_path: Path, img2_path: Path, out_npz: Path) -> None:
        """Reference shape of an external call (not used until CLI exists)."""
        cmd = [
            str(self.binary),
            "--img1",
            str(img1_path),
            "--img2",
            str(img2_path),
            "--out",
            str(out_npz),
        ]
        if self.basalt_config:
            cmd.extend(["--config", str(self.basalt_config)])
        subprocess.run(cmd, check=True)
