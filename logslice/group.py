"""Group log entries by a chosen field for batch processing."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Literal

from logslice.parser import LogEntry

GroupKey = Literal["severity", "date", "hour", "source"]


def _key_for(entry: LogEntry, by: GroupKey) -> str:
    """Derive a grouping key from *entry*."""
    if by == "severity":
        return entry.severity.upper()
    if by == "date":
        return entry.timestamp.strftime("%Y-%m-%d")
    if by == "hour":
        return entry.timestamp.strftime("%Y-%m-%dT%H")
    if by == "source":
        return entry.extra.get("source", "unknown")
    raise ValueError(f"Unknown group key: {by!r}")


def group_entries(
    entries: Iterable[LogEntry],
    by: GroupKey = "severity",
) -> Dict[str, List[LogEntry]]:
    """Return a dict mapping each key value to the list of matching entries."""
    groups: Dict[str, List[LogEntry]] = defaultdict(list)
    for entry in entries:
        groups[_key_for(entry, by)].append(entry)
    return dict(groups)


def group_counts(
    entries: Iterable[LogEntry],
    by: GroupKey = "severity",
) -> Dict[str, int]:
    """Return a dict mapping each key value to the count of matching entries."""
    counts: Dict[str, int] = defaultdict(int)
    for entry in entries:
        counts[_key_for(entry, by)] += 1
    return dict(counts)


def top_groups(
    entries: Iterable[LogEntry],
    by: GroupKey = "severity",
    n: int = 5,
) -> List[tuple]:
    """Return the top-*n* groups by entry count as (key, count) tuples."""
    counts = group_counts(entries, by)
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:n]
