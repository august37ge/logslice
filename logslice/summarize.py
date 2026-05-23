"""Summarize log entries by severity and time bucket."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, NamedTuple

from logslice.parser import LogEntry


class BucketSummary(NamedTuple):
    bucket_start: datetime
    counts: Dict[str, int]
    total: int


def _floor_to_bucket(dt: datetime, bucket_minutes: int) -> datetime:
    """Floor a datetime to the nearest bucket boundary."""
    total_minutes = dt.hour * 60 + dt.minute
    floored = (total_minutes // bucket_minutes) * bucket_minutes
    return dt.replace(
        hour=floored // 60,
        minute=floored % 60,
        second=0,
        microsecond=0,
    )


def summarize_by_severity(entries: Iterable[LogEntry]) -> Dict[str, int]:
    """Count log entries grouped by severity level."""
    counts: Dict[str, int] = defaultdict(int)
    for entry in entries:
        counts[entry.severity] += 1
    return dict(counts)


def summarize_by_time(
    entries: Iterable[LogEntry],
    bucket_minutes: int = 5,
) -> List[BucketSummary]:
    """Group log entries into time buckets and count by severity within each."""
    if bucket_minutes <= 0:
        raise ValueError("bucket_minutes must be a positive integer")

    buckets: Dict[datetime, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for entry in entries:
        if entry.timestamp is None:
            continue
        key = _floor_to_bucket(entry.timestamp, bucket_minutes)
        buckets[key][entry.severity] += 1

    result: List[BucketSummary] = []
    for bucket_start in sorted(buckets):
        counts = dict(buckets[bucket_start])
        result.append(
            BucketSummary(
                bucket_start=bucket_start,
                counts=counts,
                total=sum(counts.values()),
            )
        )
    return result


def format_summary(summaries: List[BucketSummary]) -> str:
    """Render a list of BucketSummary objects as a human-readable table."""
    if not summaries:
        return "No entries to summarize."

    lines = [f"{'Time':>20}  {'Total':>6}  Breakdown"]
    lines.append("-" * 60)
    for s in summaries:
        ts = s.bucket_start.strftime("%Y-%m-%d %H:%M")
        breakdown = "  ".join(f"{k}={v}" for k, v in sorted(s.counts.items()))
        lines.append(f"{ts:>20}  {s.total:>6}  {breakdown}")
    return "\n".join(lines)
