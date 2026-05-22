"""Utilities for handling rotated log files (e.g. .log.1, .log.gz)."""

from __future__ import annotations

import gzip
import os
from pathlib import Path
from typing import Iterator, List


ROTATED_SUFFIXES = (".gz", ".1", ".2", ".3", ".4", ".5")


def find_rotated(base_path: str | Path) -> List[Path]:
    """Return rotated log files related to *base_path*, sorted oldest-first.

    Looks for files like ``app.log.1``, ``app.log.2``, ``app.log.gz`` in the
    same directory as *base_path*.
    """
    base = Path(base_path)
    directory = base.parent
    candidates: List[Path] = []

    for entry in sorted(directory.iterdir()):
        name = entry.name
        if name == base.name:
            continue
        if name.startswith(base.name + ".") or name.startswith(base.stem + "."):
            candidates.append(entry)

    # Sort numerically where possible (.1 before .2), gz last
    def _sort_key(p: Path) -> tuple:
        suffix = p.name[len(base.name):]
        try:
            return (0, int(suffix.lstrip(".")))
        except ValueError:
            return (1, suffix)

    candidates.sort(key=_sort_key, reverse=True)  # oldest rotation first
    return candidates


def open_rotated(path: Path):
    """Open a (possibly gzip-compressed) log file for reading as text."""
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def iter_rotated_lines(base_path: str | Path) -> Iterator[str]:
    """Yield lines from rotated files oldest-first, then from *base_path*."""
    base = Path(base_path)
    rotated = find_rotated(base)
    for rpath in rotated:
        with open_rotated(rpath) as fh:
            yield from fh
    if base.exists():
        with open_rotated(base) as fh:
            yield from fh
