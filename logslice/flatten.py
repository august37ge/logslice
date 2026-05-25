"""Flatten nested/repeated log entries into a single stream with sequence numbers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List

from logslice.parser import LogEntry


@dataclass
class FlatEntry:
    """A log entry decorated with a global sequence number and source label."""

    entry: LogEntry
    sequence: int
    source: str = ""

    @property
    def timestamp(self):
        return self.entry.timestamp

    @property
    def severity(self):
        return self.entry.severity

    @property
    def message(self):
        return self.entry.message


def flatten(
    streams: Iterable[Iterable[LogEntry]],
    labels: Iterable[str] | None = None,
    start: int = 1,
) -> Iterator[FlatEntry]:
    """Consume multiple entry streams and yield FlatEntry objects in arrival order.

    Parameters
    ----------
    streams:
        An iterable of iterables of LogEntry objects.
    labels:
        Optional source labels aligned with *streams*.  If omitted or shorter
        than *streams*, missing labels default to an empty string.
    start:
        Starting sequence number (default 1).
    """
    label_list: List[str] = list(labels) if labels is not None else []
    seq = start
    for idx, stream in enumerate(streams):
        source = label_list[idx] if idx < len(label_list) else ""
        for entry in stream:
            yield FlatEntry(entry=entry, sequence=seq, source=source)
            seq += 1


def flatten_to_list(
    streams: Iterable[Iterable[LogEntry]],
    labels: Iterable[str] | None = None,
    start: int = 1,
) -> List[FlatEntry]:
    """Convenience wrapper that materialises :func:`flatten` into a list."""
    return list(flatten(streams, labels=labels, start=start))


def resequence(entries: Iterable[FlatEntry], start: int = 1) -> Iterator[FlatEntry]:
    """Return new FlatEntry objects with contiguous sequence numbers.

    Useful after filtering to restore a gapless sequence.
    """
    for seq, fe in enumerate(entries, start=start):
        yield FlatEntry(entry=fe.entry, sequence=seq, source=fe.source)
