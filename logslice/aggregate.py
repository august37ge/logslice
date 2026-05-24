"""Aggregate log entries into summary statistics over a time window."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional

from logslice.parser import LogEntry


@dataclass
class AggregateWindow:
    """Aggregated counts for a fixed time window."""

    window_start: datetime
    window_end: datetime
    total: int = 0
    by_severity: Dict[str, int] = field(default_factory=dict)
    by_source: Dict[str, int] = field(default_factory=dict)


def _floor_to_window(dt: datetime, minutes: int) -> datetime:
    """Floor *dt* to the nearest *minutes*-wide boundary."""
    total_minutes = dt.hour * 60 + dt.minute
    floored = (total_minutes // minutes) * minutes
    return dt.replace(hour=floored // 60, minute=floored % 60, second=0, microsecond=0)


def aggregate_entries(
    entries: Iterable[LogEntry],
    window_minutes: int = 5,
) -> List[AggregateWindow]:
    """Aggregate *entries* into fixed-width time windows.

    Args:
        entries: Iterable of parsed log entries.
        window_minutes: Width of each bucket in minutes (default 5).

    Returns:
        List of :class:`AggregateWindow` objects sorted by window start.
    """
    if window_minutes <= 0:
        raise ValueError("window_minutes must be a positive integer")

    buckets: Dict[datetime, AggregateWindow] = {}

    for entry in entries:
        key = _floor_to_window(entry.timestamp, window_minutes)
        if key not in buckets:
            buckets[key] = AggregateWindow(
                window_start=key,
                window_end=key + timedelta(minutes=window_minutes),
            )
        win = buckets[key]
        win.total += 1
        win.by_severity[entry.severity] = win.by_severity.get(entry.severity, 0) + 1
        src = entry.source or "<unknown>"
        win.by_source[src] = win.by_source.get(src, 0) + 1

    return sorted(buckets.values(), key=lambda w: w.window_start)


def format_aggregate(windows: List[AggregateWindow]) -> str:
    """Return a human-readable table of aggregated windows."""
    if not windows:
        return "No data."

    lines: List[str] = []
    header = f"{'Window Start':<22} {'Window End':<22} {'Total':>6}  Severity Breakdown"
    lines.append(header)
    lines.append("-" * len(header))

    for win in windows:
        sev_parts = ", ".join(
            f"{k}={v}" for k, v in sorted(win.by_severity.items())
        )
        lines.append(
            f"{win.window_start.strftime('%Y-%m-%d %H:%M:%S'):<22}"
            f" {win.window_end.strftime('%Y-%m-%d %H:%M:%S'):<22}"
            f" {win.total:>6}  {sev_parts}"
        )

    return "\n".join(lines)
