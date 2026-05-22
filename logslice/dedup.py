"""Deduplication utilities for log entries."""

from __future__ import annotations

import hashlib
from typing import Iterable, Iterator

from logslice.parser import LogEntry


def _entry_key(entry: LogEntry) -> str:
    """Return a stable hash key for a log entry based on its content."""
    raw = f"{entry.severity}|{entry.message}"
    return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()


def deduplicate(
    entries: Iterable[LogEntry],
    *,
    consecutive_only: bool = False,
) -> Iterator[LogEntry]:
    """Yield entries with duplicates removed.

    Parameters
    ----------
    entries:
        Source iterable of :class:`~logslice.parser.LogEntry` objects.
    consecutive_only:
        When *True*, only consecutive duplicate entries are suppressed
        (similar to ``uniq``).  When *False* (default), any previously
        seen entry is suppressed regardless of position.
    """
    seen: set[str] = set()
    last_key: str | None = None

    for entry in entries:
        key = _entry_key(entry)

        if consecutive_only:
            if key == last_key:
                continue
            last_key = key
            yield entry
        else:
            if key in seen:
                continue
            seen.add(key)
            yield entry


def count_duplicates(
    entries: Iterable[LogEntry],
    *,
    consecutive_only: bool = False,
) -> tuple[list[LogEntry], int]:
    """Return deduplicated entries and the number of suppressed duplicates.

    Parameters
    ----------
    entries:
        Source iterable of :class:`~logslice.parser.LogEntry` objects.
    consecutive_only:
        Passed through to :func:`deduplicate`.

    Returns
    -------
    tuple
        ``(unique_entries, duplicate_count)``
    """
    source = list(entries)
    unique = list(deduplicate(source, consecutive_only=consecutive_only))
    return unique, len(source) - len(unique)
