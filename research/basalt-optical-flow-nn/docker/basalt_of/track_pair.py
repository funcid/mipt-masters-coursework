#!/usr/bin/env python3
"""In-container pair tracker (Basalt SE2 algorithm)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

# Allow importing the host-mounted or image-bundled runner helpers
sys.path.insert(0, "/opt/basalt_of")
from se2_core import track_se2_pair  # type: ignore


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--img1", required=True)
    p.add_argument("--img2", required=True)
    p.add_argument("--keypoints", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--levels", type=int, default=3)
    p.add_argument("--max-iters", type=int, default=5)
    args = p.parse_args()

    img1 = cv2.imread(args.img1, cv2.IMREAD_COLOR)
    img2 = cv2.imread(args.img2, cv2.IMREAD_COLOR)
    kpts = np.load(args.keypoints)
    p1, p2, status, se2 = track_se2_pair(
        img1, img2, kpts, levels=args.levels, max_iters=args.max_iters
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        args.out,
        points1=p1.astype(np.float32),
        points2=p2.astype(np.float32),
        status=status.astype(np.uint8),
        se2_params=se2.astype(np.float32),
    )
    print(f"tracked {int(status.sum())}/{len(status)} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
