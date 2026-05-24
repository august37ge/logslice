"""Checkpoint support: persist and resume log processing position."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

_CHECKPOINT_DIR = Path.home() / ".logslice" / "checkpoints"


@dataclass
class Checkpoint:
    file_path: str
    byte_offset: int
    line_number: int
    last_timestamp: Optional[str] = None


def _checkpoint_path(log_path: str) -> Path:
    """Return the checkpoint file path for a given log file."""
    _CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    name = Path(log_path).name
    safe = name.replace("/", "_").replace("\\", "_")
    return _CHECKPOINT_DIR / f"{safe}.checkpoint.json"


def save_checkpoint(checkpoint: Checkpoint) -> Path:
    """Persist a checkpoint to disk. Returns the path written."""
    path = _checkpoint_path(checkpoint.file_path)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(asdict(checkpoint), fh, indent=2)
    return path


def load_checkpoint(log_path: str) -> Optional[Checkpoint]:
    """Load a checkpoint for the given log file, or None if not found."""
    path = _checkpoint_path(log_path)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Checkpoint(**data)


def clear_checkpoint(log_path: str) -> bool:
    """Delete the checkpoint for a log file. Returns True if deleted."""
    path = _checkpoint_path(log_path)
    if path.exists():
        os.remove(path)
        return True
    return False


def checkpoint_exists(log_path: str) -> bool:
    """Return True if a checkpoint exists for the given log file."""
    return _checkpoint_path(log_path).exists()
