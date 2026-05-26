"""High-level drift reporting: build a drift report from a list of LogEntry
objects and return structured results suitable for CLI or pipeline use."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Tuple

from logslice.drift import DriftEntry, detect_drift, format_drift_report
from logslice.parser import LogEntry


@dataclass
class DriftReport:
    total_entries: int
    drift_count: int
    max_drift_seconds: float  # most negative delta seen
    first_drift_ts: Optional[datetime]
    details: List[DriftEntry]

    @property
    def has_drift(self) -> bool:
        return self.drift_count > 0

    @property
    def drift_rate(self) -> float:
        if self.total_entries == 0:
            return 0.0
        return self.drift_count / self.total_entries


def build_drift_report(
    entries: Iterable[LogEntry],
    threshold_seconds: float = 0.0,
) -> DriftReport:
    """Consume *entries* once and return a DriftReport."""
    all_results: List[DriftEntry] = list(detect_drift(entries, threshold_seconds))
    drifts = [r for r in all_results if r.is_drift]

    max_drift = min((d.delta_seconds for d in drifts), default=0.0)
    first_ts = drifts[0].entry.timestamp if drifts else None

    return DriftReport(
        total_entries=len(all_results),
        drift_count=len(drifts),
        max_drift_seconds=max_drift,
        first_drift_ts=first_ts,
        details=drifts,
    )


def format_report(report: DriftReport, verbose: bool = False) -> str:
    """Return a printable string summarising the drift report."""
    lines: List[str] = [
        f"Entries scanned : {report.total_entries}",
        f"Drifts detected : {report.drift_count} "
        f"({report.drift_rate * 100:.1f}%)",
    ]
    if report.has_drift:
        lines.append(f"Largest backward drift : {report.max_drift_seconds:.3f}s")
        lines.append(f"First drift at         : {report.first_drift_ts.isoformat()}")
        if verbose:
            lines.append("")
            lines.append(format_drift_report(report.details))
    return "\n".join(lines)
