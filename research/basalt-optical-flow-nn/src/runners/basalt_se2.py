"""Basalt SE2 sparse optical flow (algorithm from Basalt open headers).

Ports Pattern51 + inverse-compositional SE(2) patch tracking from
https://gitlab.com/VladyslavUsenko/basalt. Stock `basalt_opt_flow` needs a
EuRoC-style dataset and does not export pair tracks; this runner provides the
same SE2 OF for our sparse protocol.

`backend: native` (default) — fair latency on the host.
`backend: docker` — same code inside image `basalt-of:local` (also ships
official Basalt binaries for EuRoC / T3).
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np

from .base import FlowResult, OpticalFlowRunner
from .basalt_se2_core import track_se2_pair


class BasaltSE2Runner(OpticalFlowRunner):
    kind = "sparse_se2"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.levels = int(self.config.get("optical_flow_levels", self.config.get("levels", 3)))
        self.max_iters = int(
            self.config.get("optical_flow_max_iterations", self.config.get("max_iters", 5))
        )
        self.max_recovered_dist2 = float(
            self.config.get(
                "optical_flow_max_recovered_dist2",
                self.config.get("max_recovered_dist2", 0.04),
            )
        )
        self.backend = str(self.config.get("backend", "native")).lower()
        self.docker_image = str(self.config.get("docker_image", "basalt-of:local"))

    def predict(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        keypoints: Optional[np.ndarray] = None,
    ) -> FlowResult:
        if keypoints is None or len(keypoints) == 0:
            raise ValueError("BasaltSE2Runner requires shared keypoints")

        if self.backend == "docker":
            return self._predict_docker(img1, img2, keypoints)

        p1, p2, status, se2 = track_se2_pair(
            img1,
            img2,
            keypoints,
            levels=self.levels,
            max_iters=self.max_iters,
            max_recovered_dist2=self.max_recovered_dist2,
        )
        return FlowResult(
            kind="sparse_se2",
            points1=p1.astype(np.float32),
            points2=p2.astype(np.float32),
            status=status,
            se2_params=se2.astype(np.float32),
            meta={
                "runner": "basalt_se2",
                "backend": "native",
                "note": "Basalt SE2 algorithm from open headers (Pattern51 IC)",
            },
        )

    def _predict_docker(
        self, img1: np.ndarray, img2: np.ndarray, keypoints: np.ndarray
    ) -> FlowResult:
        with tempfile.TemporaryDirectory() as tmp:
            tdir = Path(tmp)
            cv2.imwrite(str(tdir / "a.png"), img1)
            cv2.imwrite(str(tdir / "b.png"), img2)
            np.save(tdir / "kpts.npy", np.asarray(keypoints, dtype=np.float32))
            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{tdir}:/data",
                self.docker_image,
                "python3",
                "/opt/basalt_of/track_pair.py",
                "--img1",
                "/data/a.png",
                "--img2",
                "/data/b.png",
                "--keypoints",
                "/data/kpts.npy",
                "--out",
                "/data/out.npz",
                "--levels",
                str(self.levels),
                "--max-iters",
                str(self.max_iters),
            ]
            subprocess.run(cmd, check=True)
            data = np.load(tdir / "out.npz")
            return FlowResult(
                kind="sparse_se2",
                points1=data["points1"],
                points2=data["points2"],
                status=data["status"],
                se2_params=data["se2_params"],
                meta={"runner": "basalt_se2", "backend": "docker", "image": self.docker_image},
            )
