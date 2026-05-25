"""Reporting helpers for rate-limited log streams."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from logslice.parser import LogEntry


@dataclass
class RateReport:
    total_in: int
    total_out: int
    dropped: int
    drop_rate: float  # 0.0 – 1.0
    severity_dropped: dict[str, int]


def compute_rate_report(
    original: Iterable[LogEntry],
    filtered: Iterable[LogEntry],
) -> RateReport:
    """Compare *original* and *filtered* entry lists and produce a report.

    Args:
        original: The full, unfiltered sequence of log entries.
        filtered: The entries that survived rate-limiting.  Must be a subset
            of the *same* objects present in *original* (identity is used for
            matching, not equality).

    Returns:
        A :class:`RateReport` summarising how many entries were dropped and
        which severity levels were most affected.
    """
    orig_list = list(original)
    filt_set = {id(e) for e in filtered}

    severity_dropped: Counter[str] = Counter()
    for e in orig_list:
        if id(e) not in filt_set:
            severity_dropped[e.severity] += 1

    total_in = len(orig_list)
    total_out = len(filt_set)
    dropped = total_in - total_out
    drop_rate = dropped / total_in if total_in else 0.0

    return RateReport(
        total_in=total_in,
        total_out=total_out,
        dropped=dropped,
        drop_rate=drop_rate,
        severity_dropped=dict(severity_dropped),
    )


def format_rate_report(report: RateReport) -> str:
    """Return a human-readable string summarising *report*."""
    lines = [
        "Rate-limit report",
        f"  Entries in  : {report.total_in}",
        f"  Entries out : {report.total_out}",
        f"  Dropped     : {report.dropped} ({report.drop_rate:.1%})",
    ]
    if report.severity_dropped:
        lines.append("  Dropped by severity:")
        for sev, cnt in sorted(report.severity_dropped.items()):
            lines.append(f"    {sev:<10} {cnt}")
    return "\n".join(lines)


def top_dropped_severity(report: RateReport, n: int = 3) -> list[tuple[str, int]]:
    """Return the *n* severity levels with the highest drop counts.

    Args:
        report: A :class:`RateReport` previously produced by
            :func:`compute_rate_report`.
        n: Maximum number of entries to return.  Defaults to ``3``.

    Returns:
        A list of ``(severity, count)`` pairs ordered from most-dropped to
        least-dropped, capped at *n* items.
    """
    return sorted(
        report.severity_dropped.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:n]
