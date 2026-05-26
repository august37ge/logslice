"""Timestamp drift detection: flag entries whose timestamps deviate
from a monotonically-increasing sequence by more than a threshold."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogEntry


@dataclass
class DriftEntry:
    entry: LogEntry
    previous_ts: Optional[datetime]
    delta_seconds: float  # negative means backwards drift
    is_drift: bool


def detect_drift(
    entries: Iterable[LogEntry],
    threshold_seconds: float = 0.0,
) -> Iterator[DriftEntry]:
    """Yield DriftEntry for every log entry.

    An entry is flagged when its timestamp is earlier than the previous
    timestamp by more than *threshold_seconds*.
    """
    previous: Optional[datetime] = None
    for entry in entries:
        if previous is None:
            yield DriftEntry(
                entry=entry,
                previous_ts=None,
                delta_seconds=0.0,
                is_drift=False,
            )
        else:
            delta = (entry.timestamp - previous).total_seconds()
            is_drift = delta < -abs(threshold_seconds)
            yield DriftEntry(
                entry=entry,
                previous_ts=previous,
                delta_seconds=delta,
                is_drift=is_drift,
            )
        previous = entry.timestamp


def drift_only(entries: Iterable[LogEntry], threshold_seconds: float = 0.0) -> List[DriftEntry]:
    """Return only the entries that are flagged as drifts."""
    return [d for d in detect_drift(entries, threshold_seconds) if d.is_drift]


def format_drift_report(drifts: List[DriftEntry]) -> str:
    """Return a human-readable summary of detected drifts."""
    if not drifts:
        return "No timestamp drift detected."
    lines = [f"Timestamp drift detected: {len(drifts)} occurrence(s)"]
    for d in drifts:
        prev = d.previous_ts.isoformat() if d.previous_ts else "N/A"
        lines.append(
            f"  [{d.entry.timestamp.isoformat()}] delta={d.delta_seconds:.3f}s "
            f"(prev={prev}) | {d.entry.message[:60]}"
        )
    return "\n".join(lines)
