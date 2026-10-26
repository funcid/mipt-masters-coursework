"""Helpers for importing conflicting third_party optical-flow packages."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]


def purge_modules(prefixes: Iterable[str]) -> None:
    """Drop cached modules so RAFT / SEA-RAFT / GMFlow do not clash."""
    prefixes = tuple(prefixes)
    doomed = [
        name
        for name in list(sys.modules)
        if name in prefixes or any(name.startswith(p + ".") for p in prefixes)
    ]
    for name in doomed:
        sys.modules.pop(name, None)


def purge_raft_family() -> None:
    """Original RAFT and SEA-RAFT both expose top-level `raft`, `corr`, …"""
    purge_modules(
        (
            "raft",
            "update",
            "corr",
            "extractor",
            "layer",
            "utils",
            "datasets",
            "config",
        )
    )


def ensure_path(path: Path, first: bool = True) -> None:
    s = str(path)
    if s in sys.path:
        sys.path.remove(s)
    if first:
        sys.path.insert(0, s)
    else:
        sys.path.append(s)
