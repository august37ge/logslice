"""Entry scoring: assign a numeric priority score to log entries based on
severity, recency, and optional keyword boosts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, List, Optional

from logslice.parser import LogEntry, severity_level

# Base scores per severity (higher = more important)
_SEVERITY_BASE: dict[str, float] = {
    "DEBUG": 1.0,
    "INFO": 2.0,
    "WARNING": 3.0,
    "ERROR": 5.0,
    "CRITICAL": 8.0,
}


@dataclass
class ScoredEntry:
    entry: LogEntry
    score: float
    reasons: List[str] = field(default_factory=list)


def _severity_score(entry: LogEntry) -> tuple[float, str]:
    """Return (score, reason) based on severity."""
    level = entry.severity.upper()
    base = _SEVERITY_BASE.get(level, 1.0)
    return base, f"severity:{level}"


def _recency_score(
    entry: LogEntry,
    now: Optional[datetime] = None,
    half_life_hours: float = 24.0,
) -> tuple[float, str]:
    """Decay score based on age; entries older than half_life_hours lose half their bonus."""
    if now is None:
        now = datetime.now(timezone.utc)
    ts = entry.timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age_hours = max((now - ts).total_seconds() / 3600.0, 0.0)
    bonus = 1.0 / (1.0 + age_hours / half_life_hours)
    return round(bonus, 4), f"recency:{age_hours:.1f}h"


def _keyword_score(entry: LogEntry, keywords: List[str]) -> tuple[float, str]:
    """Add +1.0 for each keyword found in the message (case-insensitive)."""
    msg = entry.message.lower()
    hits = [kw for kw in keywords if kw.lower() in msg]
    return float(len(hits)), f"keywords:{','.join(hits)}" if hits else "keywords:none"


def score_entry(
    entry: LogEntry,
    keywords: Optional[List[str]] = None,
    now: Optional[datetime] = None,
    half_life_hours: float = 24.0,
) -> ScoredEntry:
    """Compute a composite score for a single entry."""
    sev_score, sev_reason = _severity_score(entry)
    rec_score, rec_reason = _recency_score(entry, now=now, half_life_hours=half_life_hours)
    kw_score, kw_reason = _keyword_score(entry, keywords or [])
    total = round(sev_score + rec_score + kw_score, 4)
    return ScoredEntry(entry=entry, score=total, reasons=[sev_reason, rec_reason, kw_reason])


def score_entries(
    entries: Iterable[LogEntry],
    keywords: Optional[List[str]] = None,
    now: Optional[datetime] = None,
    half_life_hours: float = 24.0,
) -> List[ScoredEntry]:
    """Score all entries and return them sorted by descending score."""
    scored = [
        score_entry(e, keywords=keywords, now=now, half_life_hours=half_life_hours)
        for e in entries
    ]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored


def format_scored(scored: ScoredEntry) -> str:
    """Return a human-readable line for a scored entry."""
    ts = scored.entry.timestamp.isoformat()
    sev = scored.entry.severity
    msg = scored.entry.message
    reasons = " | ".join(scored.reasons)
    return f"[{scored.score:6.3f}] {ts} [{sev}] {msg}  ({reasons})"
