"""Pattern frequency analysis: counts how often each message pattern appears."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, List

from logslice.parser import LogEntry

# Tokens replaced when normalising a message into a pattern
_REPLACEMENTS = [
    (re.compile(r'\b\d{1,3}(?:\.\d{1,3}){3}\b'), '<IP>'),        # IPv4
    (re.compile(r'\b[0-9a-fA-F]{8,}\b'), '<HEX>'),               # hex ids
    (re.compile(r'\b\d+\b'), '<NUM>'),                            # integers
    (re.compile(r'"[^"]*"'), '<STR>'),                            # quoted strings
    (re.compile(r"'[^']*'"), '<STR>'),                            # single-quoted
    (re.compile(r'\s+'), ' '),                                     # collapse whitespace
]


def message_pattern(message: str) -> str:
    """Reduce *message* to a normalised pattern string."""
    text = message
    for pattern, replacement in _REPLACEMENTS:
        text = pattern.sub(replacement, text)
    return text.strip()


@dataclass
class PatternFrequency:
    pattern: str
    count: int
    example: str
    severities: Counter = field(default_factory=Counter)


def count_patterns(
    entries: Iterable[LogEntry],
) -> List[PatternFrequency]:
    """Aggregate *entries* by normalised message pattern.

    Returns a list of :class:`PatternFrequency` objects sorted by count
    descending.
    """
    counts: Counter = Counter()
    examples: dict[str, str] = {}
    severities: dict[str, Counter] = {}

    for entry in entries:
        pat = message_pattern(entry.message)
        counts[pat] += 1
        if pat not in examples:
            examples[pat] = entry.message
        severities.setdefault(pat, Counter())[entry.severity] += 1

    results = [
        PatternFrequency(
            pattern=pat,
            count=cnt,
            example=examples[pat],
            severities=severities[pat],
        )
        for pat, cnt in counts.most_common()
    ]
    return results


def format_pattern_report(frequencies: List[PatternFrequency], top: int = 10) -> str:
    """Return a human-readable report of the *top* most frequent patterns."""
    lines: List[str] = ["Pattern Frequency Report", "=" * 40]
    for i, pf in enumerate(frequencies[:top], 1):
        sev_str = ", ".join(f"{s}:{c}" for s, c in pf.severities.most_common())
        lines.append(f"{i:>3}. [{pf.count:>6}] {pf.pattern}")
        lines.append(f"       severities: {sev_str}")
        lines.append(f"       example   : {pf.example[:80]}")
    if not frequencies:
        lines.append("(no entries)")
    return "\n".join(lines)
