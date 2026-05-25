"""Rank log entries by a composite score across multiple dimensions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from logslice.parser import LogEntry, severity_level

_SEVERITY_WEIGHT = 0.5
_RECENCY_WEIGHT = 0.3
_FREQUENCY_PENALTY_WEIGHT = 0.2


@dataclass(frozen=True)
class RankedEntry:
    entry: LogEntry
    severity_score: float
    recency_score: float
    frequency_score: float
    rank_score: float
    rank: int = field(default=0, compare=False)


def _severity_score(entry: LogEntry) -> float:
    """Normalise severity to [0, 1]; higher is more severe."""
    level = severity_level(entry.severity)
    # severity_level returns 0-50 range (DEBUG=10 … CRITICAL=50)
    return min(level / 50.0, 1.0)


def _recency_score(
    entry: LogEntry,
    earliest_ts: float,
    latest_ts: float,
) -> float:
    """Entries closer to *latest_ts* score higher."""
    span = latest_ts - earliest_ts
    if span == 0:
        return 1.0
    ts = entry.timestamp.timestamp()
    return (ts - earliest_ts) / span


def _frequency_score(entry: LogEntry, freq_map: dict[str, int], total: int) -> float:
    """Messages that appear less often score higher (rarer = more interesting)."""
    if total == 0:
        return 1.0
    count = freq_map.get(entry.message, 1)
    # inverse frequency, normalised
    return 1.0 - (count / total)


def rank_entries(
    entries: Iterable[LogEntry],
    *,
    severity_weight: float = _SEVERITY_WEIGHT,
    recency_weight: float = _RECENCY_WEIGHT,
    frequency_weight: float = _FREQUENCY_PENALTY_WEIGHT,
    top_n: Optional[int] = None,
) -> List[RankedEntry]:
    """Return *entries* sorted by composite rank score (descending)."""
    items: List[LogEntry] = list(entries)
    if not items:
        return []

    timestamps = [e.timestamp.timestamp() for e in items]
    earliest, latest = min(timestamps), max(timestamps)

    freq_map: dict[str, int] = {}
    for e in items:
        freq_map[e.message] = freq_map.get(e.message, 0) + 1
    total = len(items)

    ranked: List[RankedEntry] = []
    for entry in items:
        ss = _severity_score(entry)
        rs = _recency_score(entry, earliest, latest)
        fs = _frequency_score(entry, freq_map, total)
        score = (
            severity_weight * ss
            + recency_weight * rs
            + frequency_weight * fs
        )
        ranked.append(RankedEntry(
            entry=entry,
            severity_score=ss,
            recency_score=rs,
            frequency_score=fs,
            rank_score=score,
        ))

    ranked.sort(key=lambda r: r.rank_score, reverse=True)
    ranked = [
        RankedEntry(
            entry=r.entry,
            severity_score=r.severity_score,
            recency_score=r.recency_score,
            frequency_score=r.frequency_score,
            rank_score=r.rank_score,
            rank=i + 1,
        )
        for i, r in enumerate(ranked)
    ]
    if top_n is not None:
        ranked = ranked[:top_n]
    return ranked
