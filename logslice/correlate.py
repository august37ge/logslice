"""Correlate log entries across streams by time proximity and severity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogEntry, severity_level


@dataclass
class CorrelatedGroup:
    """A group of log entries that are temporally correlated."""
    anchor: LogEntry
    related: List[LogEntry] = field(default_factory=list)

    @property
    def all_entries(self) -> List[LogEntry]:
        return [self.anchor] + self.related

    @property
    def max_severity(self) -> str:
        levels = [severity_level(e.severity) for e in self.all_entries]
        severities = [e.severity for e in self.all_entries]
        return severities[levels.index(max(levels))]

    @property
    def time_span_seconds(self) -> float:
        """Return the total time span (in seconds) covered by all entries in the group.

        Returns 0.0 if the group contains only the anchor entry.
        """
        if not self.related:
            return 0.0
        timestamps = [e.timestamp for e in self.all_entries]
        return (max(timestamps) - min(timestamps)).total_seconds()


def _within_window(anchor: LogEntry, candidate: LogEntry, window_seconds: float) -> bool:
    delta = abs((candidate.timestamp - anchor.timestamp).total_seconds())
    return delta <= window_seconds


def correlate_entries(
    anchors: Iterable[LogEntry],
    candidates: Iterable[LogEntry],
    window_seconds: float = 5.0,
    min_severity: Optional[str] = None,
) -> Iterator[CorrelatedGroup]:
    """For each anchor entry, find candidate entries within a time window.

    Args:
        anchors: Primary entries to correlate against.
        candidates: Pool of entries to search for related events.
        window_seconds: Maximum time delta (seconds) to consider related.
        min_severity: If set, only include candidates at or above this severity.
    """
    candidate_list = list(candidates)
    min_level = severity_level(min_severity) if min_severity else 0

    for anchor in anchors:
        related = [
            c for c in candidate_list
            if c is not anchor
            and _within_window(anchor, c, window_seconds)
            and severity_level(c.severity) >= min_level
        ]
        related.sort(key=lambda e: e.timestamp)
        yield CorrelatedGroup(anchor=anchor, related=related)


def format_correlated_group(group: CorrelatedGroup, indent: str = "  ") -> str:
    """Return a human-readable string for a correlated group."""
    lines = [f"[{group.anchor.timestamp}] ({group.anchor.severity}) {group.anchor.message}"]
    for entry in group.related:
        lines.append(f"{indent}-> [{entry.timestamp}] ({entry.severity}) {entry.message}")
    return "\n".join(lines)
