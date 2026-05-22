"""Statistics collection for log slicing operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from typing import Iterable

from logslice.parser import LogEntry


@dataclass
class SliceStats:
    """Aggregated statistics over a collection of log entries."""

    total_entries: int = 0
    severity_counts: Counter = field(default_factory=Counter)
    earliest: str | None = None
    latest: str | None = None
    skipped_lines: int = 0

    def to_dict(self) -> dict:
        return {
            "total_entries": self.total_entries,
            "severity_counts": dict(self.severity_counts),
            "earliest": self.earliest,
            "latest": self.latest,
            "skipped_lines": self.skipped_lines,
        }


def compute_stats(entries: Iterable[LogEntry], skipped: int = 0) -> SliceStats:
    """Compute statistics from an iterable of LogEntry objects."""
    stats = SliceStats(skipped_lines=skipped)
    for entry in entries:
        stats.total_entries += 1
        stats.severity_counts[entry.severity] += 1
        ts = entry.timestamp.isoformat()
        if stats.earliest is None or ts < stats.earliest:
            stats.earliest = ts
        if stats.latest is None or ts > stats.latest:
            stats.latest = ts
    return stats


def format_stats(stats: SliceStats) -> str:
    """Return a human-readable summary of SliceStats."""
    lines = [
        f"Total entries : {stats.total_entries}",
        f"Skipped lines : {stats.skipped_lines}",
        f"Earliest      : {stats.earliest or 'N/A'}",
        f"Latest        : {stats.latest or 'N/A'}",
        "Severity breakdown:",
    ]
    for sev, count in sorted(stats.severity_counts.items()):
        lines.append(f"  {sev:<10} {count}")
    return "\n".join(lines)
