"""Classify log entries into named categories based on message patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from logslice.parser import LogEntry


@dataclass
class ClassifyRule:
    """A single classification rule."""
    category: str
    pattern: str
    ignore_case: bool = True
    _compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        flags = re.IGNORECASE if self.ignore_case else 0
        self._compiled = re.compile(self.pattern, flags)

    def matches(self, entry: LogEntry) -> bool:
        return bool(self._compiled.search(entry.message))


@dataclass
class ClassifiedEntry:
    """A log entry with an assigned category."""
    entry: LogEntry
    category: str


def _first_match(
    entry: LogEntry,
    rules: List[ClassifyRule],
    default: str,
) -> str:
    for rule in rules:
        if rule.matches(entry):
            return rule.category
    return default


def classify_entries(
    entries: Iterable[LogEntry],
    rules: List[ClassifyRule],
    default: str = "uncategorized",
) -> Iterator[ClassifiedEntry]:
    """Yield ClassifiedEntry for each entry using the first matching rule."""
    for entry in entries:
        category = _first_match(entry, rules, default)
        yield ClassifiedEntry(entry=entry, category=category)


def category_counts(
    classified: Iterable[ClassifiedEntry],
) -> Dict[str, int]:
    """Return a mapping of category -> entry count."""
    counts: Dict[str, int] = {}
    for ce in classified:
        counts[ce.category] = counts.get(ce.category, 0) + 1
    return counts


def top_categories(
    counts: Dict[str, int],
    n: int = 5,
) -> List[Tuple[str, int]]:
    """Return the top *n* categories sorted by count descending."""
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:n]


def format_category_report(counts: Dict[str, int]) -> str:
    """Format category counts as a human-readable string."""
    if not counts:
        return "No entries classified."
    lines = ["Category Report:", "-" * 30]
    for cat, cnt in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"  {cat:<25} {cnt:>6}")
    return "\n".join(lines)
