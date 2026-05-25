"""Split a stream of log entries into multiple output buckets by a key."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List

from logslice.parser import LogEntry

# Built-in key functions

def key_by_severity(entry: LogEntry) -> str:
    """Bucket key: normalised severity string."""
    return (entry.severity or "UNKNOWN").upper()


def key_by_date(entry: LogEntry) -> str:
    """Bucket key: ISO date (YYYY-MM-DD)."""
    return entry.timestamp.strftime("%Y-%m-%d")


def key_by_hour(entry: LogEntry) -> str:
    """Bucket key: ISO hour (YYYY-MM-DDTHH)."""
    return entry.timestamp.strftime("%Y-%m-%dT%H")


def key_by_source(entry: LogEntry) -> str:
    """Bucket key: source field (falls back to empty string)."""
    return entry.source or ""


# ---------------------------------------------------------------------------

@dataclass
class SplitResult:
    """Container returned by :func:`split_entries`."""
    buckets: Dict[str, List[LogEntry]] = field(default_factory=dict)

    @property
    def keys(self) -> List[str]:
        """Sorted list of bucket keys."""
        return sorted(self.buckets.keys())

    def get(self, key: str) -> List[LogEntry]:
        """Return the entries for *key*, or an empty list."""
        return self.buckets.get(key, [])

    def total(self) -> int:
        """Total number of entries across all buckets."""
        return sum(len(v) for v in self.buckets.values())


def split_entries(
    entries: Iterable[LogEntry],
    key_fn: Callable[[LogEntry], str],
) -> SplitResult:
    """Partition *entries* into buckets determined by *key_fn*.

    Args:
        entries: Iterable of :class:`~logslice.parser.LogEntry` objects.
        key_fn:  Callable that maps an entry to a bucket key string.

    Returns:
        A :class:`SplitResult` whose ``buckets`` dict maps each key to the
        ordered list of entries that belong to it.
    """
    buckets: Dict[str, List[LogEntry]] = defaultdict(list)
    for entry in entries:
        buckets[key_fn(entry)].append(entry)
    return SplitResult(buckets=dict(buckets))


_KEY_FUNCTIONS: Dict[str, Callable[[LogEntry], str]] = {
    "severity": key_by_severity,
    "date": key_by_date,
    "hour": key_by_hour,
    "source": key_by_source,
}


def get_key_fn(name: str) -> Callable[[LogEntry], str]:
    """Return a built-in key function by *name*.

    Raises:
        KeyError: if *name* is not a recognised key function.
    """
    if name not in _KEY_FUNCTIONS:
        raise KeyError(f"Unknown split key '{name}'. Choose from: {sorted(_KEY_FUNCTIONS)}.")
    return _KEY_FUNCTIONS[name]
