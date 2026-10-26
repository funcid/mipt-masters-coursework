"""Dense and sparse optical flow metrics."""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np


def endpoint_error(flow_pred: np.ndarray, flow_gt: np.ndarray, valid: Optional[np.ndarray] = None) -> np.ndarray:
    """Per-pixel EPE. flow_*: HxWx2."""
    err = np.linalg.norm(flow_pred - flow_gt, axis=-1)
    if valid is not None:
        err = np.where(valid.astype(bool), err, np.nan)
    return err


def dense_metrics(
    flow_pred: np.ndarray,
    flow_gt: np.ndarray,
    valid: Optional[np.ndarray] = None,
    fl_threshold: float = 3.0,
    fl_relative: float = 0.05,
) -> Dict[str, float]:
    """EPE, % pixels under 1/3/5 px, KITTI-style Fl-all."""
    epe_map = endpoint_error(flow_pred, flow_gt, valid=None)
    if valid is None:
        # KITTI: valid where magnitude of GT is finite and often >0 mask
        valid_mask = np.isfinite(flow_gt[..., 0]) & np.isfinite(flow_gt[..., 1])
    else:
        valid_mask = valid.astype(bool)

    epe_vals = epe_map[valid_mask]
    if epe_vals.size == 0:
        return {"epe": float("nan"), "px1": float("nan"), "px3": float("nan"), "px5": float("nan"), "fl_all": float("nan")}

    gt_mag = np.linalg.norm(flow_gt, axis=-1)[valid_mask]
    fl = (epe_vals > fl_threshold) & (epe_vals > fl_relative * gt_mag)

    return {
        "epe": float(np.mean(epe_vals)),
        "px1": float(np.mean(epe_vals < 1.0) * 100.0),
        "px3": float(np.mean(epe_vals < 3.0) * 100.0),
        "px5": float(np.mean(epe_vals < 5.0) * 100.0),
        "fl_all": float(np.mean(fl) * 100.0),
    }


def sparse_endpoint_metrics(
    points1: np.ndarray,
    points2_pred: np.ndarray,
    points2_gt: np.ndarray,
    status: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """Mean endpoint error on sparse tracks; success_rate = fraction with status==1."""
    p1 = np.asarray(points1, dtype=np.float64).reshape(-1, 2)
    p2p = np.asarray(points2_pred, dtype=np.float64).reshape(-1, 2)
    p2g = np.asarray(points2_gt, dtype=np.float64).reshape(-1, 2)

    if status is None:
        status = np.ones(len(p1), dtype=np.uint8)
    status = np.asarray(status).reshape(-1).astype(bool)

    n = len(p1)
    if n == 0:
        return {"endpoint_epe": float("nan"), "success_rate": float("nan"), "n_tracks": 0}

    success_rate = float(np.mean(status) * 100.0)
    if not np.any(status):
        return {"endpoint_epe": float("nan"), "success_rate": success_rate, "n_tracks": int(n)}

    err = np.linalg.norm(p2p[status] - p2g[status], axis=-1)
    return {
        "endpoint_epe": float(np.mean(err)),
        "success_rate": success_rate,
        "n_tracks": int(n),
    }


def sample_dense_at_points(flow_dense: np.ndarray, points: np.ndarray) -> np.ndarray:
    """Lookup dense flow at sparse points -> predicted points2 = points + flow."""
    pts = np.asarray(points, dtype=np.float32).reshape(-1, 2)
    h, w = flow_dense.shape[:2]
    xs = np.clip(np.round(pts[:, 0]).astype(int), 0, w - 1)
    ys = np.clip(np.round(pts[:, 1]).astype(int), 0, h - 1)
    return pts + flow_dense[ys, xs]


def sparse_gt_from_dense(flow_gt: np.ndarray, points1: np.ndarray) -> np.ndarray:
    return sample_dense_at_points(flow_gt, points1)
