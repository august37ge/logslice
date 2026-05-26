"""Span analysis: measure time gaps between consecutive log entries."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogEntry


@dataclass
class SpanEntry:
    """A pair of consecutive entries with the time gap between them."""
    before: LogEntry
    after: LogEntry
    gap: timedelta

    @property
    def gap_seconds(self) -> float:
        return self.gap.total_seconds()


def iter_spans(entries: Iterable[LogEntry]) -> Iterator[SpanEntry]:
    """Yield a SpanEntry for every consecutive pair of log entries."""
    prev: Optional[LogEntry] = None
    for entry in entries:
        if prev is not None:
            gap = entry.timestamp - prev.timestamp
            yield SpanEntry(before=prev, after=entry, gap=gap)
        prev = entry


def largest_gaps(spans: Iterable[SpanEntry], n: int = 5) -> List[SpanEntry]:
    """Return the *n* spans with the largest time gap, descending."""
    if n <= 0:
        return []
    all_spans = sorted(spans, key=lambda s: s.gap, reverse=True)
    return all_spans[:n]


def average_gap(spans: Iterable[SpanEntry]) -> Optional[timedelta]:
    """Return the mean gap across all spans, or None if there are none."""
    items = list(spans)
    if not items:
        return None
    total = sum((s.gap.total_seconds() for s in items), 0.0)
    return timedelta(seconds=total / len(items))


def format_span_report(spans: List[SpanEntry], top_n: int = 5) -> str:
    """Render a human-readable span report."""
    lines: List[str] = []
    if not spans:
        return "No spans to report."

    avg = average_gap(iter(spans))
    avg_str = f"{avg.total_seconds():.2f}s" if avg is not None else "n/a"
    lines.append(f"Total spans : {len(spans)}")
    lines.append(f"Average gap : {avg_str}")

    top = largest_gaps(iter(spans), n=top_n)
    if top:
        lines.append(f"\nTop {len(top)} largest gaps:")
        for i, sp in enumerate(top, 1):
            ts_before = sp.before.timestamp.strftime("%Y-%m-%dT%H:%M:%S")
            ts_after = sp.after.timestamp.strftime("%Y-%m-%dT%H:%M:%S")
            lines.append(
                f"  {i}. {ts_before} -> {ts_after}  ({sp.gap_seconds:.2f}s)"
            )
    return "\n".join(lines)
