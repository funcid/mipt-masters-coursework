"""Basalt SE2 core (Pattern51 IC) shared by native runner and Docker."""
from __future__ import annotations

import math
from typing import List, Tuple

import cv2
import numpy as np

_PATTERN52 = np.array(
    [
        [-3, 7], [-1, 7], [1, 7], [3, 7],
        [-5, 5], [-3, 5], [-1, 5], [1, 5], [3, 5], [5, 5],
        [-7, 3], [-5, 3], [-3, 3], [-1, 3], [1, 3], [3, 3], [5, 3], [7, 3],
        [-7, 1], [-5, 1], [-3, 1], [-1, 1], [1, 1], [3, 1], [5, 1], [7, 1],
        [-7, -1], [-5, -1], [-3, -1], [-1, -1], [1, -1], [3, -1], [5, -1], [7, -1],
        [-7, -3], [-5, -3], [-3, -3], [-1, -3], [1, -3], [3, -3], [5, -3], [7, -3],
        [-5, -5], [-3, -5], [-1, -5], [1, -5], [3, -5], [5, -5],
        [-3, -7], [-1, -7], [1, -7], [3, -7],
    ],
    dtype=np.float32,
)
PATTERN51 = 0.5 * _PATTERN52  # Nx2
PATTERN_SIZE = len(PATTERN51)


def _to_gray_u8(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def _to_u16(gray_u8: np.ndarray) -> np.ndarray:
    # Basalt typically stores 8-bit intensities in uint16 (<< 8).
    return (gray_u8.astype(np.uint16) << 8)


def _build_pyramid(img_u16: np.ndarray, levels: int) -> List[np.ndarray]:
    pyr = [img_u16]
    cur = img_u16
    for _ in range(levels):
        # Approx Basalt Gaussian×2 subsample via OpenCV pyrDown on float then back
        f = cur.astype(np.float32)
        down = cv2.pyrDown(f)
        pyr.append(np.clip(down, 0, 65535).astype(np.uint16))
        cur = pyr[-1]
    return pyr


def _interp(img: np.ndarray, x: float, y: float) -> float:
    h, w = img.shape
    if x < 1 or y < 1 or x >= w - 2 or y >= h - 2:
        return -1.0
    x0, y0 = int(math.floor(x)), int(math.floor(y))
    dx, dy = x - x0, y - y0
    v00 = float(img[y0, x0])
    v01 = float(img[y0, x0 + 1])
    v10 = float(img[y0 + 1, x0])
    v11 = float(img[y0 + 1, x0 + 1])
    return (1 - dy) * ((1 - dx) * v00 + dx * v01) + dy * ((1 - dx) * v10 + dx * v11)


def _interp_grad(img: np.ndarray, x: float, y: float) -> Tuple[float, float, float]:
    """Returns (value, dI/dx, dI/dy) or (-1,0,0) if OOB."""
    h, w = img.shape
    if x < 1 or y < 1 or x >= w - 2 or y >= h - 2:
        return -1.0, 0.0, 0.0
    val = _interp(img, x, y)
    # central differences via bilinear samples
    gx = 0.5 * (_interp(img, x + 1, y) - _interp(img, x - 1, y))
    gy = 0.5 * (_interp(img, x, y + 1) - _interp(img, x, y - 1))
    return val, gx, gy


def _se2_matrix(tx: float, ty: float, theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, -s, tx], [s, c, ty]], dtype=np.float64)


def _se2_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compose 2x3 affine compact transforms (linear|t)."""
    A = np.eye(3)
    B = np.eye(3)
    A[:2, :] = a
    B[:2, :] = b
    C = A @ B
    return C[:2, :]


def _se2_exp(inc: np.ndarray) -> np.ndarray:
    """Sophus-like SE2::exp on [tx, ty, theta] -> 2x3."""
    tx, ty, theta = float(inc[0]), float(inc[1]), float(inc[2])
    return _se2_matrix(tx, ty, theta)


class _Patch:
    def __init__(self, img: np.ndarray, pos: np.ndarray) -> None:
        self.pos = pos.astype(np.float64)
        self.data = np.zeros(PATTERN_SIZE, dtype=np.float64)
        self.H_inv_JT = np.zeros((3, PATTERN_SIZE), dtype=np.float64)
        self.mean = 0.0
        self.valid = False
        self._build(img)

    def _build(self, img: np.ndarray) -> None:
        data = np.zeros(PATTERN_SIZE, dtype=np.float64)
        J = np.zeros((PATTERN_SIZE, 3), dtype=np.float64)
        grad_sum = np.zeros(3, dtype=np.float64)
        s = 0.0
        n_valid = 0
        for i, (px, py) in enumerate(PATTERN51):
            x = self.pos[0] + float(px)
            y = self.pos[1] + float(py)
            # Jw_se2: d(warp)/d(tx,ty,theta); theta column = [-py, px]
            jw = np.array([[1.0, 0.0, -float(py)], [0.0, 1.0, float(px)]], dtype=np.float64)
            val, gx, gy = _interp_grad(img, x, y)
            if val < 0:
                data[i] = -1.0
                continue
            data[i] = val
            s += val
            n_valid += 1
            g = np.array([gx, gy], dtype=np.float64)
            J[i] = g @ jw
            grad_sum += J[i]
        if n_valid == 0 or s <= 1e-12:
            self.valid = False
            return
        mean = s / n_valid
        mean_inv = n_valid / s
        for i in range(PATTERN_SIZE):
            if data[i] >= 0:
                J[i] -= grad_sum * (data[i] / s)
                data[i] *= mean_inv
            else:
                J[i] = 0.0
        J *= mean_inv
        H = J.T @ J
        try:
            H_inv = np.linalg.inv(H + 1e-8 * np.eye(3))
        except np.linalg.LinAlgError:
            self.valid = False
            return
        self.data = data
        self.mean = mean
        self.H_inv_JT = H_inv @ J.T
        self.valid = (
            mean > 1e-12
            and np.isfinite(self.H_inv_JT).all()
            and np.isfinite(self.data).all()
        )

    def residual(self, img: np.ndarray, transformed: np.ndarray) -> Tuple[bool, np.ndarray]:
        res = np.zeros(PATTERN_SIZE, dtype=np.float64)
        s = 0.0
        n_valid = 0
        for i in range(PATTERN_SIZE):
            x, y = float(transformed[0, i]), float(transformed[1, i])
            v = _interp(img, x, y)
            if v < 0:
                res[i] = -1.0
            else:
                res[i] = v
                s += v
                n_valid += 1
        if s <= 1e-12:
            return False, np.zeros(PATTERN_SIZE)
        n_res = 0
        for i in range(PATTERN_SIZE):
            if res[i] >= 0 and self.data[i] >= 0:
                res[i] = n_valid * res[i] / s - self.data[i]
                n_res += 1
            else:
                res[i] = 0.0
        return n_res > PATTERN_SIZE / 2, res


def _track_at_level(
    img2: np.ndarray,
    patch: _Patch,
    transform: np.ndarray,
    max_iters: int,
) -> Tuple[bool, np.ndarray]:
    ok = True
    T = transform.copy()
    for _ in range(max_iters):
        R = T[:, :2]
        t = T[:, 2]
        transformed = R @ PATTERN51.T + t.reshape(2, 1)
        valid, res = patch.residual(img2, transformed)
        if not valid:
            ok = False
            break
        inc = -patch.H_inv_JT @ res
        if not np.isfinite(inc).all() or np.linalg.norm(inc, ord=np.inf) >= 1e6:
            ok = False
            break
        T = _se2_mul(T, _se2_exp(inc))
        tx, ty = float(T[0, 2]), float(T[1, 2])
        h, w = img2.shape
        if tx < 2 or ty < 2 or tx >= w - 2 or ty >= h - 2:
            ok = False
            break
    return ok, T


def _track_point(
    pyr1: List[np.ndarray],
    pyr2: List[np.ndarray],
    pos0: np.ndarray,
    levels: int,
    max_iters: int,
) -> Tuple[bool, np.ndarray, float]:
    """Returns success, translation in level-0 pixels, theta."""
    T = np.array([[1.0, 0.0, float(pos0[0])], [0.0, 1.0, float(pos0[1])]], dtype=np.float64)
    # linear part identity at start of each track (as in Basalt trackPoint)
    T[:2, :2] = np.eye(2)
    ok = True
    for level in range(levels, -1, -1):
        scale = float(1 << level)
        T[:, 2] /= scale
        pos_lvl = np.array([float(pos0[0]) / scale, float(pos0[1]) / scale])
        patch = _Patch(pyr1[level], pos_lvl)
        if not patch.valid:
            ok = False
            break
        ok, T = _track_at_level(pyr2[level], patch, T, max_iters)
        T[:, 2] *= scale
        if not ok:
            break
    theta = math.atan2(T[1, 0], T[0, 0])
    return ok, T[:, 2].copy(), theta


def track_se2_pair(
    img1_bgr: np.ndarray,
    img2_bgr: np.ndarray,
    keypoints: np.ndarray,
    levels: int = 3,
    max_iters: int = 5,
    max_recovered_dist2: float = 0.04,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    g1 = _to_u16(_to_gray_u8(img1_bgr))
    g2 = _to_u16(_to_gray_u8(img2_bgr))
    pyr1 = _build_pyramid(g1, levels)
    pyr2 = _build_pyramid(g2, levels)
    pts = np.asarray(keypoints, dtype=np.float64).reshape(-1, 2)
    p1 = pts.copy()
    p2 = np.zeros_like(p1)
    status = np.zeros(len(pts), dtype=np.uint8)
    se2 = np.zeros((len(pts), 3), dtype=np.float64)
    for i, pt in enumerate(pts):
        ok_f, t_f, th_f = _track_point(pyr1, pyr2, pt, levels, max_iters)
        if not ok_f:
            continue
        ok_b, t_b, _th_b = _track_point(pyr2, pyr1, t_f, levels, max_iters)
        if not ok_b:
            continue
        dist2 = float(np.sum((pt - t_b) ** 2))
        if dist2 >= max_recovered_dist2:
            continue
        p2[i] = t_f
        status[i] = 1
        se2[i] = [t_f[0] - pt[0], t_f[1] - pt[1], th_f]
    return p1, p2, status, se2

