"""Sliding window analysis over log entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, Iterator, List

from logslice.parser import LogEntry


@dataclass
class WindowSlice:
    """A single sliding-window bucket."""
    window_start: datetime
    window_end: datetime
    entries: List[LogEntry] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.entries)

    @property
    def severity_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self.entries:
            counts[e.severity] = counts.get(e.severity, 0) + 1
        return counts


def sliding_windows(
    entries: Iterable[LogEntry],
    window_size: timedelta,
    step: timedelta,
) -> Iterator[WindowSlice]:
    """Yield WindowSlice objects using a sliding window over *entries*.

    Both *window_size* and *step* must be positive.  Entries are assumed to
    arrive in ascending timestamp order.
    """
    if window_size <= timedelta(0):
        raise ValueError("window_size must be positive")
    if step <= timedelta(0):
        raise ValueError("step must be positive")

    buffered: List[LogEntry] = list(entries)
    if not buffered:
        return

    start = buffered[0].timestamp
    end_ts = buffered[-1].timestamp

    current = start
    while current <= end_ts:
        window_end = current + window_size
        bucket = [
            e for e in buffered
            if current <= e.timestamp < window_end
        ]
        yield WindowSlice(
            window_start=current,
            window_end=window_end,
            entries=bucket,
        )
        current += step


def format_window_summary(slices: Iterable[WindowSlice]) -> str:
    """Return a human-readable table of window slices."""
    lines: List[str] = []
    for s in slices:
        sev = ", ".join(
            f"{k}:{v}" for k, v in sorted(s.severity_counts.items())
        )
        lines.append(
            f"{s.window_start.isoformat()} -> {s.window_end.isoformat()} "
            f"| count={s.count} | {sev}"
        )
    return "\n".join(lines)
