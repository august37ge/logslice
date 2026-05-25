"""Heatmap: build a time-vs-severity frequency grid from log entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Tuple

from logslice.parser import LogEntry, severity_level

SEVERITY_ORDER = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@dataclass
class HeatmapCell:
    window_start: datetime
    severity: str
    count: int = 0


@dataclass
class Heatmap:
    bucket_minutes: int
    # rows keyed by window_start, columns by severity
    grid: Dict[datetime, Dict[str, int]] = field(default_factory=dict)
    severities: List[str] = field(default_factory=list)


def _floor_to_bucket(dt: datetime, minutes: int) -> datetime:
    total_minutes = dt.hour * 60 + dt.minute
    floored = (total_minutes // minutes) * minutes
    return dt.replace(hour=floored // 60, minute=floored % 60, second=0, microsecond=0)


def build_heatmap(
    entries: Iterable[LogEntry],
    bucket_minutes: int = 60,
    severities: List[str] | None = None,
) -> Heatmap:
    """Aggregate entries into a time-bucket x severity grid."""
    if bucket_minutes <= 0:
        raise ValueError("bucket_minutes must be positive")

    hm = Heatmap(bucket_minutes=bucket_minutes)
    seen_severities: set[str] = set()

    for entry in entries:
        bucket = _floor_to_bucket(entry.timestamp, bucket_minutes)
        sev = (entry.severity or "UNKNOWN").upper()
        seen_severities.add(sev)
        if bucket not in hm.grid:
            hm.grid[bucket] = {}
        hm.grid[bucket][sev] = hm.grid[bucket].get(sev, 0) + 1

    if severities is not None:
        hm.severities = [s.upper() for s in severities]
    else:
        hm.severities = sorted(
            seen_severities,
            key=lambda s: severity_level(s),
        )

    return hm


def format_heatmap(hm: Heatmap, col_width: int = 8) -> str:
    """Render the heatmap as a plain-text table."""
    if not hm.grid:
        return "(no data)"

    cols = hm.severities or SEVERITY_ORDER
    header = f"{'TIME':<19}" + "".join(f"{s:>{col_width}}" for s in cols)
    rows: List[str] = [header, "-" * len(header)]

    for bucket in sorted(hm.grid):
        ts = bucket.strftime("%Y-%m-%d %H:%M")
        cells = "".join(
            f"{hm.grid[bucket].get(sev, 0):>{col_width}}" for sev in cols
        )
        rows.append(f"{ts:<19}{cells}")

    return "\n".join(rows)
