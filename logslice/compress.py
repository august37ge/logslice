"""Compress and decompress log entry streams using run-length encoding of repeated messages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List

from logslice.parser import LogEntry


@dataclass
class CompressedRun:
    """A run of identical (by key) log entries."""

    entry: LogEntry
    count: int = 1
    first_timestamp: object = field(default=None)
    last_timestamp: object = field(default=None)

    def __post_init__(self) -> None:
        if self.first_timestamp is None:
            self.first_timestamp = self.entry.timestamp
        if self.last_timestamp is None:
            self.last_timestamp = self.entry.timestamp


def _run_key(entry: LogEntry) -> tuple:
    """Key used to decide whether two adjacent entries form a run."""
    return (entry.severity.upper(), entry.message.strip())


def compress_entries(entries: Iterable[LogEntry]) -> List[CompressedRun]:
    """Collapse consecutive duplicate entries into CompressedRun objects."""
    runs: List[CompressedRun] = []
    current: CompressedRun | None = None

    for entry in entries:
        key = _run_key(entry)
        if current is not None and _run_key(current.entry) == key:
            current.count += 1
            current.last_timestamp = entry.timestamp
        else:
            if current is not None:
                runs.append(current)
            current = CompressedRun(
                entry=entry,
                count=1,
                first_timestamp=entry.timestamp,
                last_timestamp=entry.timestamp,
            )

    if current is not None:
        runs.append(current)

    return runs


def decompress_runs(runs: Iterable[CompressedRun]) -> Iterator[LogEntry]:
    """Expand CompressedRun objects back into individual LogEntry objects."""
    for run in runs:
        for _ in range(run.count):
            yield run.entry


def compression_ratio(original_count: int, compressed_count: int) -> float:
    """Return ratio of compressed size to original size (lower is better)."""
    if original_count == 0:
        return 0.0
    return compressed_count / original_count


def format_compressed_run(run: CompressedRun) -> str:
    """Human-readable representation of a compressed run."""
    ts_first = run.first_timestamp.isoformat() if hasattr(run.first_timestamp, "isoformat") else str(run.first_timestamp)
    ts_last = run.last_timestamp.isoformat() if hasattr(run.last_timestamp, "isoformat") else str(run.last_timestamp)
    if run.count == 1:
        return f"[{ts_first}] {run.entry.severity.upper()} {run.entry.message}"
    return (
        f"[{ts_first} .. {ts_last}] {run.entry.severity.upper()} "
        f"{run.entry.message}  (x{run.count})"
    )
