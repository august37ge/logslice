"""Keyword and regex search support for log entries."""

import re
from typing import Iterable, Iterator, Optional, Pattern

from logslice.parser import LogEntry


def _compile_pattern(keyword: str, ignore_case: bool = False) -> Pattern:
    """Compile a keyword or regex pattern."""
    flags = re.IGNORECASE if ignore_case else 0
    try:
        return re.compile(keyword, flags)
    except re.error as exc:
        raise ValueError(f"Invalid regex pattern {keyword!r}: {exc}") from exc


def matches_entry(entry: LogEntry, pattern: Pattern) -> bool:
    """Return True if the log entry message matches the pattern."""
    return bool(pattern.search(entry.message))


def search_entries(
    entries: Iterable[LogEntry],
    keyword: Optional[str] = None,
    ignore_case: bool = False,
    invert: bool = False,
) -> Iterator[LogEntry]:
    """Filter entries by keyword/regex match against the message field.

    Args:
        entries:     Iterable of LogEntry objects.
        keyword:     Regex or plain keyword to search for.  If None, all
                     entries are yielded unchanged.
        ignore_case: Perform case-insensitive matching.
        invert:      Yield entries that do NOT match (grep -v behaviour).

    Yields:
        LogEntry objects that satisfy the search criteria.
    """
    if keyword is None:
        yield from entries
        return

    pattern = _compile_pattern(keyword, ignore_case=ignore_case)
    for entry in entries:
        hit = matches_entry(entry, pattern)
        if invert:
            hit = not hit
        if hit:
            yield entry
