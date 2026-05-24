"""High-level helpers for rendering context-aware log reports."""

from __future__ import annotations

from typing import Callable, Iterable, Iterator, List

from logslice.context import ContextEntry, format_context_entry, with_context
from logslice.parser import LogEntry


def context_report(
    entries: Iterable[LogEntry],
    predicate: Callable[[LogEntry], bool],
    before: int = 2,
    after: int = 2,
    separator: str = "--",
) -> Iterator[str]:
    """Yield formatted lines for every matching entry with surrounding context.

    Args:
        entries:   Iterable of parsed log entries.
        predicate: Selects entries of interest (e.g. severity == ERROR).
        before:    Lines of context before each match.
        after:     Lines of context after each match.
        separator: String placed between consecutive match blocks.
    """
    for ctx in with_context(entries, predicate, before=before, after=after):
        yield from format_context_entry(ctx, separator=separator)


def severity_predicate(min_severity: str) -> Callable[[LogEntry], bool]:
    """Return a predicate that matches entries at or above *min_severity*."""
    from logslice.parser import severity_level

    threshold = severity_level(min_severity)

    def _pred(entry: LogEntry) -> bool:
        return severity_level(entry.severity) >= threshold

    return _pred


def keyword_predicate(keyword: str, case_sensitive: bool = False) -> Callable[[LogEntry], bool]:
    """Return a predicate that matches entries whose message contains *keyword*."""
    needle = keyword if case_sensitive else keyword.lower()

    def _pred(entry: LogEntry) -> bool:
        haystack = entry.message if case_sensitive else entry.message.lower()
        return needle in haystack

    return _pred


def combined_predicate(
    *predicates: Callable[[LogEntry], bool],
    require_all: bool = True,
) -> Callable[[LogEntry], bool]:
    """Combine multiple predicates with AND (default) or OR logic."""
    if require_all:
        return lambda e: all(p(e) for p in predicates)
    return lambda e: any(p(e) for p in predicates)


def count_context_matches(
    entries: Iterable[LogEntry],
    predicate: Callable[[LogEntry], bool],
) -> int:
    """Return the number of entries that satisfy *predicate*."""
    return sum(1 for e in entries if predicate(e))
