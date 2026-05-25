"""Reporting helpers for scored log entries."""

from __future__ import annotations

from typing import List

from logslice.score import ScoredEntry


def top_n(scored: List[ScoredEntry], n: int = 10) -> List[ScoredEntry]:
    """Return the top-n highest-scored entries (list already sorted desc)."""
    return scored[:n]


def score_distribution(scored: List[ScoredEntry], buckets: int = 5) -> dict[str, int]:
    """Divide the score range into equal buckets and count entries per bucket."""
    if not scored:
        return {}
    scores = [s.score for s in scored]
    lo, hi = min(scores), max(scores)
    if lo == hi:
        label = f"{lo:.2f}-{hi:.2f}"
        return {label: len(scored)}
    step = (hi - lo) / buckets
    dist: dict[str, int] = {}
    for i in range(buckets):
        bucket_lo = lo + i * step
        bucket_hi = bucket_lo + step
        label = f"{bucket_lo:.2f}-{bucket_hi:.2f}"
        count = sum(1 for s in scores if bucket_lo <= s < bucket_hi)
        dist[label] = count
    # last bucket is inclusive on right
    last_label = list(dist.keys())[-1]
    dist[last_label] += sum(1 for s in scores if s == hi)
    return dist


def format_score_report(scored: List[ScoredEntry], top: int = 10) -> str:
    """Return a formatted text report of the top scored entries."""
    from logslice.score import format_scored

    lines: List[str] = []
    lines.append(f"=== Score Report (top {top} of {len(scored)} entries) ===")
    for s in top_n(scored, top):
        lines.append(format_scored(s))
    lines.append("")
    lines.append("Score distribution:")
    for label, cnt in score_distribution(scored).items():
        bar = "#" * min(cnt, 40)
        lines.append(f"  {label:>18}  {bar} ({cnt})")
    return "\n".join(lines)


def average_score(scored: List[ScoredEntry]) -> float:
    """Return the mean score, or 0.0 for an empty list."""
    if not scored:
        return 0.0
    return round(sum(s.score for s in scored) / len(scored), 4)
