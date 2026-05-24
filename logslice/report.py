"""Generate human-readable annotation reports from annotated log entries."""

from __future__ import annotations

from collections import Counter
from typing import Iterable, List

from logslice.annotate import AnnotatedEntry


def tag_frequency(annotated: Iterable[AnnotatedEntry]) -> Counter:
    """Return a Counter mapping each tag to the number of entries that carry it."""
    counter: Counter = Counter()
    for ae in annotated:
        counter.update(ae.tags)
    return counter


def entries_without_tags(annotated: Iterable[AnnotatedEntry]) -> List[AnnotatedEntry]:
    """Return entries that have no tags attached."""
    return [ae for ae in annotated if not ae.tags]


def format_annotation_report(
    annotated: List[AnnotatedEntry],
    top_n: int = 10,
) -> str:
    """Render a short text report summarising annotation coverage."""
    total = len(annotated)
    untagged = len(entries_without_tags(annotated))
    tagged = total - untagged
    freq = tag_frequency(annotated)

    lines: List[str] = [
        "=== Annotation Report ===",
        f"Total entries : {total}",
        f"Tagged        : {tagged}",
        f"Untagged      : {untagged}",
        "",
        "Top tags:",
    ]

    if not freq:
        lines.append("  (none)")
    else:
        for tag, count in freq.most_common(top_n):
            lines.append(f"  {tag:<30} {count}")

    return "\n".join(lines)


def annotation_coverage(annotated: Iterable[AnnotatedEntry]) -> float:
    """Return the fraction of entries (0.0–1.0) that have at least one tag."""
    items = list(annotated)
    if not items:
        return 0.0
    tagged = sum(1 for ae in items if ae.tags)
    return tagged / len(items)
