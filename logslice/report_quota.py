"""Human-readable reports for quota enforcement results."""
from __future__ import annotations

from typing import List

from logslice.quota import QuotaResult


def format_quota_report(result: QuotaResult, *, title: str = "Quota Report") -> str:
    """Return a multi-line text report summarising *result*."""
    lines: List[str] = [
        f"=== {title} ===",
        f"Emitted : {result.emitted}",
        f"Dropped : {result.dropped}",
    ]

    if result.dropped_by_severity:
        lines.append("Dropped by severity:")
        for sev in sorted(result.dropped_by_severity):
            lines.append(f"  {sev:<12} {result.dropped_by_severity[sev]}")

    if result.dropped_by_source:
        lines.append("Dropped by source:")
        for src in sorted(result.dropped_by_source):
            label = src if src else "<unknown>"
            lines.append(f"  {label:<20} {result.dropped_by_source[src]}")

    return "\n".join(lines)


def drop_rate(result: QuotaResult) -> float:
    """Return fraction of entries dropped (0.0 – 1.0)."""
    total = result.emitted + result.dropped
    if total == 0:
        return 0.0
    return result.dropped / total


def quota_summary(result: QuotaResult) -> dict:
    """Return a plain dict suitable for JSON serialisation."""
    return {
        "emitted": result.emitted,
        "dropped": result.dropped,
        "drop_rate": round(drop_rate(result), 4),
        "dropped_by_severity": dict(result.dropped_by_severity),
        "dropped_by_source": dict(result.dropped_by_source),
    }
