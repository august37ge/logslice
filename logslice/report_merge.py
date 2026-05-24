"""Human-readable reporting utilities for merged log streams."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Iterable, List, Optional

from logslice.parser import LogEntry


def merge_report_header(stream_count: int) -> str:
    """Return a one-line header describing the merge operation."""
    return f"Merged {stream_count} stream(s)"


def severity_distribution(entries: Iterable[LogEntry]) -> Counter:
    """Count entries grouped by severity."""
    counts: Counter = Counter()
    for entry in entries:
        counts[entry.severity.upper()] += 1
    return counts


def time_span(
    entries: Iterable[LogEntry],
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Return (earliest, latest) timestamps from *entries*.

    Returns (None, None) when the iterable is empty.
    """
    earliest: Optional[datetime] = None
    latest: Optional[datetime] = None
    for entry in entries:
        if earliest is None or entry.timestamp < earliest:
            earliest = entry.timestamp
        if latest is None or entry.timestamp > latest:
            latest = entry.timestamp
    return earliest, latest


def format_merge_report(
    entries: List[LogEntry],
    stream_count: int,
    *,
    show_distribution: bool = True,
) -> str:
    """Build a multi-line text report summarising a merged result set."""
    lines: List[str] = []
    lines.append(merge_report_header(stream_count))
    lines.append(f"Total entries : {len(entries)}")

    earliest, latest = time_span(entries)
    if earliest and latest:
        lines.append(f"Time range    : {earliest.isoformat()} – {latest.isoformat()}")
    else:
        lines.append("Time range    : (empty)")

    if show_distribution:
        dist = severity_distribution(entries)
        if dist:
            lines.append("Severity breakdown:")
            for sev, count in sorted(dist.items()):
                lines.append(f"  {sev:<10} {count}")
        else:
            lines.append("Severity breakdown: (none)")

    return "\n".join(lines)
