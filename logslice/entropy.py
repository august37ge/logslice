"""Entropy-based anomaly detection for log entries.

Computes message entropy to flag statistically unusual log lines.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List

from logslice.parser import LogEntry


@dataclass
class EntropyResult:
    entry: LogEntry
    entropy: float
    is_anomaly: bool


def _shannon_entropy(text: str) -> float:
    """Return Shannon entropy (bits) of *text*."""
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    return -sum(
        (c / total) * math.log2(c / total) for c in counts.values()
    )


def score_entries(
    entries: Iterable[LogEntry],
) -> List[EntropyResult]:
    """Compute entropy for every entry; anomaly flag is set later by threshold."""
    return [
        EntropyResult(entry=e, entropy=_shannon_entropy(e.message), is_anomaly=False)
        for e in entries
    ]


def mark_anomalies(
    results: List[EntropyResult],
    threshold: float | None = None,
    z_score_cutoff: float = 2.0,
) -> List[EntropyResult]:
    """Mark entries whose entropy exceeds *threshold*.

    If *threshold* is None, derive it automatically using mean + z_score_cutoff * std.
    """
    if not results:
        return results

    if threshold is None:
        values = [r.entropy for r in results]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)
        threshold = mean + z_score_cutoff * std

    for r in results:
        r.is_anomaly = r.entropy > threshold
    return results


def anomalous_entries(
    entries: Iterable[LogEntry],
    threshold: float | None = None,
    z_score_cutoff: float = 2.0,
) -> Iterator[EntropyResult]:
    """Yield only anomalous entries from *entries*."""
    results = score_entries(entries)
    mark_anomalies(results, threshold=threshold, z_score_cutoff=z_score_cutoff)
    return (r for r in results if r.is_anomaly)


def format_entropy_report(results: List[EntropyResult]) -> str:
    """Return a human-readable summary of entropy results."""
    lines: List[str] = []
    anomalies = [r for r in results if r.is_anomaly]
    lines.append(f"Entries analysed : {len(results)}")
    lines.append(f"Anomalies found  : {len(anomalies)}")
    if results:
        avg = sum(r.entropy for r in results) / len(results)
        lines.append(f"Average entropy  : {avg:.3f} bits")
    for r in anomalies:
        ts = r.entry.timestamp.isoformat()
        lines.append(f"  [{ts}] ({r.entropy:.3f}) {r.entry.message[:80]}")
    return "\n".join(lines)
