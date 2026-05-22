"""Simple file-based index cache for logslice.

Stores byte offsets for timestamps so repeated queries on the same
file can seek directly instead of scanning from the beginning.
"""

from __future__ import annotations

import json
import os
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


_CACHE_VERSION = 1


@dataclass
class CacheEntry:
    """Cached index for a single log file."""
    file_path: str
    file_size: int
    file_mtime: float
    version: int = _CACHE_VERSION
    # List of (iso_timestamp, byte_offset) pairs, sorted by offset
    index: List[Tuple[str, int]] = field(default_factory=list)


def _cache_path(log_path: str, cache_dir: Optional[str] = None) -> Path:
    """Return the path where the cache file for *log_path* should live."""
    digest = hashlib.sha1(os.path.abspath(log_path).encode()).hexdigest()[:12]
    base = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "logslice"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{digest}.json"


def _is_valid(entry: CacheEntry, log_path: str) -> bool:
    """Return True when the cached metadata still matches the file on disk."""
    try:
        stat = os.stat(log_path)
        return (
            entry.version == _CACHE_VERSION
            and entry.file_size == stat.st_size
            and abs(entry.file_mtime - stat.st_mtime) < 0.01
        )
    except OSError:
        return False


def load_cache(log_path: str, cache_dir: Optional[str] = None) -> Optional[CacheEntry]:
    """Load and validate a cache entry for *log_path*.

    Returns ``None`` if no valid cache exists.
    """
    path = _cache_path(log_path, cache_dir)
    if not path.exists():
        return None
    try:
        data: Dict = json.loads(path.read_text(encoding="utf-8"))
        entry = CacheEntry(
            file_path=data["file_path"],
            file_size=data["file_size"],
            file_mtime=data["file_mtime"],
            version=data.get("version", 0),
            index=[tuple(pair) for pair in data.get("index", [])],  # type: ignore[misc]
        )
        return entry if _is_valid(entry, log_path) else None
    except (KeyError, ValueError, OSError):
        return None


def save_cache(
    log_path: str,
    index: List[Tuple[str, int]],
    cache_dir: Optional[str] = None,
) -> None:
    """Persist *index* to disk for *log_path*."""
    try:
        stat = os.stat(log_path)
        entry = CacheEntry(
            file_path=os.path.abspath(log_path),
            file_size=stat.st_size,
            file_mtime=stat.st_mtime,
            index=index,
        )
        path = _cache_path(log_path, cache_dir)
        path.write_text(
            json.dumps(entry.__dict__, default=list),
            encoding="utf-8",
        )
    except OSError:
        pass  # Cache is best-effort; never crash the main pipeline.
