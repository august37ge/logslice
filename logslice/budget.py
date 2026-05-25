"""Log budget: cap the number of entries emitted per severity per time window."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, Iterator, Optional

from logslice.parser import LogEntry, severity_level


@dataclass
class BudgetConfig:
    """Maximum entries allowed per severity within *window_minutes* minutes."""

    max_per_severity: int = 100
    window_minutes: int = 60
    # Optional per-severity overrides, e.g. {"DEBUG": 10, "ERROR": 500}
    overrides: Dict[str, int] = field(default_factory=dict)

    def limit_for(self, severity: str) -> int:
        return self.overrides.get(severity.upper(), self.max_per_severity)


@dataclass
class BudgetResult:
    allowed: list[LogEntry] = field(default_factory=list)
    dropped: int = 0
    dropped_by_severity: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


def _window_start(ts: datetime, window_minutes: int) -> datetime:
    """Floor *ts* to the nearest *window_minutes* boundary."""
    total_seconds = int(ts.timestamp())
    window_seconds = window_minutes * 60
    floored = (total_seconds // window_seconds) * window_seconds
    return datetime.utcfromtimestamp(floored).replace(tzinfo=ts.tzinfo)


def apply_budget(
    entries: Iterable[LogEntry],
    config: Optional[BudgetConfig] = None,
) -> BudgetResult:
    """Filter *entries* so that no severity exceeds its configured budget
    within any rolling time window.

    Entries are processed in arrival order; once a bucket is full the
    remaining entries for that (window, severity) pair are dropped.
    """
    if config is None:
        config = BudgetConfig()

    result = BudgetResult()
    # counts[(window_start, severity)] -> int
    counts: Dict[tuple, int] = defaultdict(int)

    for entry in entries:
        sev = entry.severity.upper()
        ws = _window_start(entry.timestamp, config.window_minutes)
        key = (ws, sev)
        limit = config.limit_for(sev)
        if counts[key] < limit:
            counts[key] += 1
            result.allowed.append(entry)
        else:
            result.dropped += 1
            result.dropped_by_severity[sev] += 1

    return result


def iter_budget(
    entries: Iterable[LogEntry],
    config: Optional[BudgetConfig] = None,
) -> Iterator[LogEntry]:
    """Yield only entries that pass the budget, discarding the rest silently."""
    result = apply_budget(entries, config)
    yield from result.allowed


def format_budget_report(result: BudgetResult) -> str:
    lines = [f"Allowed : {len(result.allowed)}", f"Dropped : {result.dropped}"]
    if result.dropped_by_severity:
        lines.append("Dropped by severity:")
        for sev in sorted(result.dropped_by_severity):
            lines.append(f"  {sev:<10} {result.dropped_by_severity[sev]}")
    return "\n".join(lines)
