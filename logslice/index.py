"""Byte-offset index for fast seeking into large log files by timestamp."""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from logslice.parser import parse_line


@dataclass
class IndexEntry:
    offset: int
    timestamp_iso: str


def build_index(log_path: str, sample_every: int = 500) -> List[IndexEntry]:
    """Scan *log_path* and record byte offsets every *sample_every* valid lines.

    Returns a list of IndexEntry objects sorted by offset (ascending).
    """
    entries: List[IndexEntry] = []
    valid_count = 0

    with open(log_path, "rb") as fh:
        while True:
            offset = fh.tell()
            raw = fh.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace")
            entry = parse_line(line)
            if entry is None:
                continue
            valid_count += 1
            if valid_count == 1 or valid_count % sample_every == 0:
                entries.append(
                    IndexEntry(
                        offset=offset,
                        timestamp_iso=entry.timestamp.isoformat(),
                    )
                )

    return entries


def _index_path(log_path: str) -> Path:
    cache_dir = Path.home() / ".cache" / "logslice" / "index"
    cache_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(log_path).name
    size = os.path.getsize(log_path)
    mtime = int(os.path.getmtime(log_path))
    tag = f"{stem}_{size}_{mtime}"
    return cache_dir / f"{tag}.json"


def save_index(log_path: str, index: List[IndexEntry]) -> Path:
    """Persist *index* to a JSON file and return its path."""
    path = _index_path(log_path)
    data = [asdict(e) for e in index]
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def load_index(log_path: str) -> Optional[List[IndexEntry]]:
    """Load a previously saved index for *log_path*, or return None."""
    path = _index_path(log_path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [IndexEntry(**e) for e in data]
    except (json.JSONDecodeError, TypeError, KeyError):
        return None


def seek_to_start(fh, index: List[IndexEntry], start_iso: str) -> None:
    """Seek *fh* to the latest index offset whose timestamp <= *start_iso*.

    Falls back to the beginning of the file if no suitable entry is found.
    """
    best_offset = 0
    for entry in index:
        if entry.timestamp_iso <= start_iso:
            best_offset = entry.offset
        else:
            break
    fh.seek(best_offset)
