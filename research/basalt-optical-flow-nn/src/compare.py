#!/usr/bin/env python3
"""Unified optical flow comparison entrypoint → CSV + Markdown.

Usage (from project root on the evaluation machine):

  python -m src.compare --config configs/default.yaml
  python -m src.compare --config configs/default.yaml --pair path/a.png path/b.png
  python -m src.compare --list-methods
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import yaml

from .metrics import dense_metrics, sample_dense_at_points, sparse_endpoint_metrics, sparse_gt_from_dense
from .runners import build_default_registry
from .runners.base import FlowResult, OpticalFlowRunner
from .runners.opencv_lk import OpenCVLucasKanadeRunner


ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def detect_shared_keypoints(img: np.ndarray, sparse_cfg: Dict[str, Any]) -> np.ndarray:
    runner = OpenCVLucasKanadeRunner(config=sparse_cfg)
    gray = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    pts = runner.detect_keypoints(gray)
    return pts.reshape(-1, 2)


def resize_pair(
    img1: np.ndarray, img2: np.ndarray, size: Tuple[int, int]
) -> Tuple[np.ndarray, np.ndarray]:
    w, h = size
    return cv2.resize(img1, (w, h)), cv2.resize(img2, (w, h))


def measure_latency(
    runner: OpticalFlowRunner,
    img1: np.ndarray,
    img2: np.ndarray,
    keypoints: Optional[np.ndarray],
    warmup: int,
    measure: int,
) -> float:
    for _ in range(warmup):
        runner.predict(img1, img2, keypoints=keypoints)
    times: List[float] = []
    for _ in range(measure):
        t0 = time.perf_counter()
        runner.predict(img1, img2, keypoints=keypoints)
        times.append(time.perf_counter() - t0)
    return float(np.mean(times) * 1000.0)  # ms


def result_to_sparse_pred(result: FlowResult, keypoints: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    if result.points1 is not None and result.points2 is not None:
        status = result.status if result.status is not None else np.ones(len(result.points1), dtype=np.uint8)
        return result.points1, result.points2, status
    if result.flow_dense is not None:
        p2 = sample_dense_at_points(result.flow_dense, keypoints)
        return keypoints, p2, np.ones(len(keypoints), dtype=np.uint8)
    raise ValueError(f"Runner returned neither sparse tracks nor dense flow (kind={result.kind})")


def evaluate_pair(
    runner: OpticalFlowRunner,
    img1: np.ndarray,
    img2: np.ndarray,
    keypoints: np.ndarray,
    flow_gt: Optional[np.ndarray],
    valid: Optional[np.ndarray],
    latency_cfg: Dict[str, Any],
) -> Dict[str, Any]:
    row: Dict[str, Any] = {"method": runner.method_id, "kind": runner.kind}

    t0 = time.perf_counter()
    result = runner.predict(img1, img2, keypoints=keypoints)
    row["infer_ms"] = (time.perf_counter() - t0) * 1000.0

    if latency_cfg.get("latency"):
        row["latency_ms"] = measure_latency(
            runner,
            img1,
            img2,
            keypoints,
            warmup=int(latency_cfg.get("warmup_frames", 5)),
            measure=int(latency_cfg.get("measure_frames", 50)),
        )

    if flow_gt is not None and result.flow_dense is not None:
        dm = dense_metrics(result.flow_dense, flow_gt, valid=valid)
        row.update(dm)

    if flow_gt is not None and len(keypoints) > 0:
        p1, p2, status = result_to_sparse_pred(result, keypoints)
        p2_gt = sparse_gt_from_dense(flow_gt, p1)
        sm = sparse_endpoint_metrics(p1, p2, p2_gt, status=status)
        row.update(sm)

    return row


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: List[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: List[Dict[str, Any]], path: Path) -> None:
    if not rows:
        path.write_text("_No results._\n", encoding="utf-8")
        return
    keys: List[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    lines = [
        "| " + " | ".join(keys) + " |",
        "| " + " | ".join("---" for _ in keys) + " |",
    ]
    for r in rows:
        cells = []
        for k in keys:
            v = r.get(k, "")
            if isinstance(v, float):
                cells.append(f"{v:.4f}" if np.isfinite(v) else "nan")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_flow_flo(path: Path) -> np.ndarray:
    """Middlebury .flo reader."""
    with path.open("rb") as f:
        magic = np.frombuffer(f.read(4), dtype=np.float32)[0]
        if abs(magic - 202021.25) > 1e-3:
            raise ValueError(f"Invalid .flo magic in {path}")
        w = np.frombuffer(f.read(4), dtype=np.int32)[0]
        h = np.frombuffer(f.read(4), dtype=np.int32)[0]
        data = np.frombuffer(f.read(), dtype=np.float32)
    flow = data.reshape(h, w, 2).copy()
    # Middlebury invalid
    invalid = (np.abs(flow) > 1e9).any(axis=-1)
    flow[invalid] = np.nan
    return flow


def try_load_sintel_pair(root: Path) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, None]]:
    """Pick first available Sintel training pair if dataset is present."""
    for pass_name in ("clean", "final"):
        img_root = root / f"training/{pass_name}"
        flow_root = root / "training/flow"
        if not img_root.is_dir() or not flow_root.is_dir():
            continue
        scenes = sorted([p for p in img_root.iterdir() if p.is_dir()])
        if not scenes:
            continue
        frames = sorted(scenes[0].glob("*.png"))
        if len(frames) < 2:
            continue
        f0, f1 = frames[0], frames[1]
        flow_path = flow_root / scenes[0].name / (f0.stem + ".flo")
        if not flow_path.exists():
            continue
        img1 = cv2.imread(str(f0), cv2.IMREAD_COLOR)
        img2 = cv2.imread(str(f1), cv2.IMREAD_COLOR)
        flow = load_flow_flo(flow_path)
        return img1, img2, flow, None
    return None


def synthetic_pair(h: int = 480, w: int = 640, dx: float = 4.0, dy: float = -2.0):
    """Fallback when no dataset is present — constant shift."""
    img1 = np.zeros((h, w, 3), dtype=np.uint8)
    cv2.randn(img1, 64, 40)
    # textured patches
    for i in range(20):
        x, y = np.random.randint(20, w - 20), np.random.randint(20, h - 20)
        cv2.circle(img1, (x, y), 8, (int(200 * np.random.rand()),) * 3, -1)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    img2 = cv2.warpAffine(img1, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    flow_gt = np.zeros((h, w, 2), dtype=np.float32)
    flow_gt[..., 0] = dx
    flow_gt[..., 1] = dy
    return img1, img2, flow_gt, np.ones((h, w), dtype=bool)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Unified optical flow comparison")
    parser.add_argument("--config", type=Path, default=ROOT / "configs/default.yaml")
    parser.add_argument("--pair", nargs=2, metavar=("IMG1", "IMG2"), help="Optional image pair")
    parser.add_argument("--flow-gt", type=Path, help="Optional .flo GT for --pair")
    parser.add_argument("--list-methods", action="store_true")
    parser.add_argument("--synthetic", action="store_true", help="Force synthetic pair")
    args = parser.parse_args(argv)

    registry = build_default_registry()
    if args.list_methods:
        print("Registered methods:", ", ".join(registry.available()))
        return 0

    cfg = load_config(args.config)
    sparse_cfg = cfg.get("sparse_protocol", {})
    metrics_cfg = cfg.get("metrics", {})
    out_cfg = cfg.get("output", {})
    results_dir = ROOT / out_cfg.get("results_dir", "results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Load images
    flow_gt: Optional[np.ndarray] = None
    valid: Optional[np.ndarray] = None
    if args.pair:
        img1 = cv2.imread(args.pair[0], cv2.IMREAD_COLOR)
        img2 = cv2.imread(args.pair[1], cv2.IMREAD_COLOR)
        if img1 is None or img2 is None:
            print("Failed to read --pair images", file=sys.stderr)
            return 1
        if args.flow_gt:
            flow_gt = load_flow_flo(args.flow_gt)
    elif args.synthetic:
        img1, img2, flow_gt, valid = synthetic_pair()
    else:
        sintel_root = Path(cfg.get("datasets", {}).get("sintel", {}).get("root", "data/sintel"))
        if not sintel_root.is_absolute():
            sintel_root = ROOT / sintel_root
        loaded = try_load_sintel_pair(sintel_root) if sintel_root.exists() else None
        if loaded is not None:
            img1, img2, flow_gt, valid = loaded
            print(f"Using Sintel pair from {sintel_root}")
        else:
            print("No dataset found — using synthetic constant-shift pair (smoke test)")
            img1, img2, flow_gt, valid = synthetic_pair()

    resolutions = cfg.get("experiment", {}).get("resolutions", [[img1.shape[1], img1.shape[0]]])
    method_cfgs = [m for m in cfg.get("methods", []) if m.get("enabled", False)]

    rows: List[Dict[str, Any]] = []
    for res in resolutions:
        w, h = int(res[0]), int(res[1])
        i1, i2 = resize_pair(img1, img2, (w, h))
        gt_r = None
        valid_r = None
        if flow_gt is not None:
            # Nearest resize of flow vectors (approximate; for smoke / protocol)
            gt_r = cv2.resize(flow_gt, (w, h), interpolation=cv2.INTER_NEAREST)
            sx, sy = w / flow_gt.shape[1], h / flow_gt.shape[0]
            gt_r = gt_r.copy()
            gt_r[..., 0] *= sx
            gt_r[..., 1] *= sy
        if valid is not None:
            valid_r = cv2.resize(valid.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)

        keypoints = detect_shared_keypoints(i1, sparse_cfg)
        print(f"Resolution {w}x{h}: {len(keypoints)} keypoints")

        for mcfg in method_cfgs:
            mid = mcfg["id"]
            runner_cfg = {**sparse_cfg, **{k: v for k, v in mcfg.items() if k not in ("id", "enabled", "kind")}}
            try:
                runner = registry.create(mid, config=runner_cfg)
            except KeyError as e:
                print(f"Skip {mid}: {e}")
                continue
            try:
                row = evaluate_pair(runner, i1, i2, keypoints, gt_r, valid_r, metrics_cfg)
                row["resolution"] = f"{w}x{h}"
                rows.append(row)
                print(f"  {mid}: {row}")
            except NotImplementedError as e:
                print(f"  {mid}: SKIP ({e})")
                rows.append(
                    {
                        "method": mid,
                        "kind": mcfg.get("kind", ""),
                        "resolution": f"{w}x{h}",
                        "status": "not_implemented",
                        "detail": str(e)[:200],
                    }
                )
            finally:
                runner.close()

    csv_path = results_dir / out_cfg.get("csv_name", "comparison.csv")
    md_path = results_dir / out_cfg.get("markdown_name", "comparison.md")
    write_csv(rows, csv_path)
    write_markdown(rows, md_path)
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
