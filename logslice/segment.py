"""Segment log entries into contiguous time-based chunks with gap detection."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Iterator, List

from logslice.parser import LogEntry


@dataclass
class Segment:
    """A contiguous group of log entries with no gap exceeding *max_gap*."""

    entries: List[LogEntry] = field(default_factory=list)

    @property
    def start(self) -> datetime | None:
        return self.entries[0].timestamp if self.entries else None

    @property
    def end(self) -> datetime | None:
        return self.entries[-1].timestamp if self.entries else None

    @property
    def duration_seconds(self) -> float:
        if self.start is None or self.end is None:
            return 0.0
        return (self.end - self.start).total_seconds()

    @property
    def count(self) -> int:
        return len(self.entries)


def segment_entries(
    entries: Iterable[LogEntry],
    max_gap: timedelta = timedelta(minutes=5),
) -> Iterator[Segment]:
    """Yield Segments split wherever consecutive timestamps exceed *max_gap*."""
    if max_gap.total_seconds() <= 0:
        raise ValueError("max_gap must be positive")

    current: Segment = Segment()
    prev_ts: datetime | None = None

    for entry in entries:
        ts = entry.timestamp
        if prev_ts is not None and (ts - prev_ts) > max_gap:
            if current.entries:
                yield current
            current = Segment()
        current.entries.append(entry)
        prev_ts = ts

    if current.entries:
        yield current


def format_segment_report(segments: List[Segment]) -> str:
    """Return a human-readable summary of a list of segments."""
    if not segments:
        return "No segments found."

    lines: List[str] = [f"Segments: {len(segments)}"]
    for i, seg in enumerate(segments, 1):
        lines.append(
            f"  [{i}] {seg.start} -> {seg.end}  "
            f"entries={seg.count}  duration={seg.duration_seconds:.1f}s"
        )
    return "\n".join(lines)
