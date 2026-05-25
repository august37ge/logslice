"""Per-severity and per-source entry quota enforcement."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, Optional

from logslice.parser import LogEntry


@dataclass
class QuotaConfig:
    """Limits on how many entries to emit per key."""
    per_severity: Optional[int] = None   # max entries per severity level
    per_source: Optional[int] = None     # max entries per source field
    total: Optional[int] = None          # hard cap across all entries

    def __post_init__(self) -> None:
        for attr in ("per_severity", "per_source", "total"):
            val = getattr(self, attr)
            if val is not None and val < 0:
                raise ValueError(f"{attr} must be non-negative, got {val}")


@dataclass
class QuotaResult:
    """Summary produced after applying a quota."""
    emitted: int = 0
    dropped: int = 0
    dropped_by_severity: Dict[str, int] = field(default_factory=dict)
    dropped_by_source: Dict[str, int] = field(default_factory=dict)


def apply_quota(
    entries: Iterable[LogEntry],
    config: QuotaConfig,
) -> Iterator[tuple[LogEntry, bool]]:
    """Yield (entry, kept) pairs respecting *config* limits.

    Callers that only want kept entries can filter on the boolean flag.
    """
    severity_counts: Dict[str, int] = {}
    source_counts: Dict[str, int] = {}
    total_emitted = 0

    for entry in entries:
        sev = entry.severity.upper()
        src = entry.source or ""

        over_sev = (
            config.per_severity is not None
            and severity_counts.get(sev, 0) >= config.per_severity
        )
        over_src = (
            config.per_source is not None
            and source_counts.get(src, 0) >= config.per_source
        )
        over_total = (
            config.total is not None
            and total_emitted >= config.total
        )

        if over_sev or over_src or over_total:
            yield entry, False
        else:
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            source_counts[src] = source_counts.get(src, 0) + 1
            total_emitted += 1
            yield entry, True


def quota_entries(
    entries: Iterable[LogEntry],
    config: QuotaConfig,
) -> tuple[list[LogEntry], QuotaResult]:
    """Return (kept_entries, result) after enforcing *config*."""
    result = QuotaResult()
    kept: list[LogEntry] = []

    for entry, ok in apply_quota(entries, config):
        sev = entry.severity.upper()
        src = entry.source or ""
        if ok:
            kept.append(entry)
            result.emitted += 1
        else:
            result.dropped += 1
            result.dropped_by_severity[sev] = (
                result.dropped_by_severity.get(sev, 0) + 1
            )
            result.dropped_by_source[src] = (
                result.dropped_by_source.get(src, 0) + 1
            )

    return kept, result
