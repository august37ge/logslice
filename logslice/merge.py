"""Merge multiple sorted log entry streams into a single time-ordered stream."""

from __future__ import annotations

import heapq
from typing import Iterable, Iterator, List, Tuple

from logslice.parser import LogEntry


def _entry_sort_key(entry: LogEntry) -> Tuple:
    """Return a sort key for a LogEntry based on its timestamp."""
    return (entry.timestamp,)


def merge_sorted(
    *streams: Iterable[LogEntry],
) -> Iterator[LogEntry]:
    """Merge multiple pre-sorted LogEntry iterables into one sorted stream.

    Each input stream must already be sorted by timestamp (ascending).
    Uses a min-heap for O(n log k) merging where k is the number of streams.
    """
    iterators = [iter(s) for s in streams]

    # heap items: (timestamp, stream_index, entry)
    heap: List[Tuple] = []
    for idx, it in enumerate(iterators):
        entry = next(it, None)
        if entry is not None:
            heapq.heappush(heap, (entry.timestamp, idx, entry))

    while heap:
        ts, idx, entry = heapq.heappop(heap)
        yield entry
        nxt = next(iterators[idx], None)
        if nxt is not None:
            heapq.heappush(heap, (nxt.timestamp, idx, nxt))


def merge_and_deduplicate(
    *streams: Iterable[LogEntry],
    window_seconds: float = 0.0,
) -> Iterator[LogEntry]:
    """Merge sorted streams and drop consecutive duplicate entries.

    Two entries are considered duplicates when they share the same severity
    and message and their timestamps differ by at most *window_seconds*.
    """
    from datetime import timedelta

    prev: LogEntry | None = None
    delta = timedelta(seconds=window_seconds)

    for entry in merge_sorted(*streams):
        if prev is not None:
            same_content = (
                entry.severity == prev.severity
                and entry.message == prev.message
            )
            within_window = (entry.timestamp - prev.timestamp) <= delta
            if same_content and within_window:
                continue
        yield entry
        prev = entry


def count_merged(entries: Iterable[LogEntry]) -> Tuple[int, int]:
    """Return (total_entries, unique_sources) from a flat iterable.

    Useful for quick stats after a merge; sources are identified by the
    optional *source* attribute when present, otherwise by object identity.
    """
    total = 0
    sources: set = set()
    for entry in entries:
        total += 1
        src = getattr(entry, "source", None)
        sources.add(src if src is not None else id(entry))
    return total, len(sources)
