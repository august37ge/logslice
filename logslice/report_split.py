"""Formatting helpers for :class:`~logslice.split.SplitResult`."""
from __future__ import annotations

from typing import List

from logslice.split import SplitResult


def bucket_counts(result: SplitResult) -> List[tuple[str, int]]:
    """Return ``(key, count)`` pairs sorted by key."""
    return [(k, len(result.buckets[k])) for k in result.keys]


def largest_bucket(result: SplitResult) -> str | None:
    """Return the key of the bucket with the most entries, or *None* if empty."""
    if not result.buckets:
        return None
    return max(result.buckets, key=lambda k: len(result.buckets[k]))


def format_split_report(result: SplitResult, title: str = "Split Report") -> str:
    """Render a human-readable split summary.

    Example output::

        Split Report
        ============
        Total entries : 42
        Buckets       : 3

        ERROR    : 20 (47.6%)
        WARNING  : 15 (35.7%)
        INFO     :  7 (16.7%)

    Args:
        result: A :class:`~logslice.split.SplitResult`.
        title:  Heading text.

    Returns:
        A multi-line string ready for printing.
    """
    total = result.total()
    lines: List[str] = [
        title,
        "=" * len(title),
        f"Total entries : {total}",
        f"Buckets       : {len(result.buckets)}",
        "",
    ]

    counts = bucket_counts(result)
    if not counts:
        lines.append("(no entries)")
        return "\n".join(lines)

    key_width = max(len(k) for k, _ in counts)
    for key, cnt in counts:
        pct = (cnt / total * 100) if total else 0.0
        lines.append(f"{key:<{key_width}} : {cnt:>6} ({pct:5.1f}%)")

    return "\n".join(lines)
