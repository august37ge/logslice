"""Resume log processing from a saved checkpoint."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional

from logslice.checkpoint import Checkpoint, load_checkpoint, save_checkpoint
from logslice.parser import LogEntry, parse_line


def iter_from_checkpoint(
    log_path: str,
    checkpoint: Optional[Checkpoint] = None,
) -> Iterator[LogEntry]:
    """Yield LogEntry objects starting from the byte offset in the checkpoint.

    If *checkpoint* is None the full file is read from the beginning.
    """
    offset = checkpoint.byte_offset if checkpoint else 0
    with open(log_path, "rb") as fh:
        fh.seek(offset)
        for raw in fh:
            line = raw.decode("utf-8", errors="replace")
            entry = parse_line(line)
            if entry is not None:
                yield entry


def process_with_checkpoint(
    log_path: str,
    *,
    resume: bool = True,
) -> tuple[list[LogEntry], Checkpoint]:
    """Read *log_path*, optionally resuming from a saved checkpoint.

    Returns a tuple of (entries, new_checkpoint).  The caller is responsible
    for calling ``save_checkpoint`` if they want to persist the position.
    """
    existing = load_checkpoint(log_path) if resume else None
    start_offset = existing.byte_offset if existing else 0
    start_line = existing.line_number if existing else 0

    entries: list[LogEntry] = []
    byte_offset = start_offset
    line_number = start_line
    last_ts: Optional[str] = None

    with open(log_path, "rb") as fh:
        fh.seek(start_offset)
        for raw in fh:
            line = raw.decode("utf-8", errors="replace")
            byte_offset += len(raw)
            line_number += 1
            entry = parse_line(line)
            if entry is not None:
                entries.append(entry)
                last_ts = entry.timestamp.isoformat()

    new_cp = Checkpoint(
        file_path=log_path,
        byte_offset=byte_offset,
        line_number=line_number,
        last_timestamp=last_ts,
    )
    return entries, new_cp
