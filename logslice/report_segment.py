"""High-level helpers for building and rendering segment reports."""
from __future__ import annotations

from datetime import timedelta
from typing import Iterable, List

from logslice.parser import LogEntry
from logslice.segment import Segment, format_segment_report, segment_entries


def build_segment_report(
    entries: Iterable[LogEntry],
    max_gap: timedelta = timedelta(minutes=5),
) -> str:
    """Segment *entries* and return a formatted report string."""
    segs: List[Segment] = list(segment_entries(entries, max_gap=max_gap))
    return format_segment_report(segs)


def largest_segment(segments: List[Segment]) -> Segment | None:
    """Return the segment with the most entries, or *None* if the list is empty."""
    if not segments:
        return None
    return max(segments, key=lambda s: s.count)


def longest_segment(segments: List[Segment]) -> Segment | None:
    """Return the segment with the greatest time duration."""
    if not segments:
        return None
    return max(segments, key=lambda s: s.duration_seconds)


def segment_summary(segments: List[Segment]) -> dict:
    """Return a plain dict summary suitable for JSON serialisation."""
    if not segments:
        return {
            "total_segments": 0,
            "total_entries": 0,
            "largest_segment_entries": 0,
            "longest_segment_seconds": 0.0,
        }

    big = largest_segment(segments)
    long_ = longest_segment(segments)
    return {
        "total_segments": len(segments),
        "total_entries": sum(s.count for s in segments),
        "largest_segment_entries": big.count if big else 0,
        "longest_segment_seconds": long_.duration_seconds if long_ else 0.0,
    }
