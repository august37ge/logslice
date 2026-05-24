"""Rate limiting and throttling for log entry streams."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator

from logslice.parser import LogEntry


@dataclass
class RateWindow:
    """Tracks entry counts within a sliding time window."""
    window_seconds: int
    max_entries: int
    _timestamps: list[datetime] = field(default_factory=list, repr=False)

    def _evict_old(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=self.window_seconds)
        self._timestamps = [t for t in self._timestamps if t >= cutoff]

    def allow(self, entry: LogEntry) -> bool:
        """Return True if the entry is within the rate limit."""
        now = entry.timestamp
        self._evict_old(now)
        if len(self._timestamps) < self.max_entries:
            self._timestamps.append(now)
            return True
        return False

    def current_count(self, now: datetime) -> int:
        """Return number of entries currently tracked in the window."""
        self._evict_old(now)
        return len(self._timestamps)


def rate_limit_entries(
    entries: Iterator[LogEntry],
    window_seconds: int,
    max_entries: int,
) -> Iterator[LogEntry]:
    """Yield only entries that fall within the rate limit.

    Entries exceeding *max_entries* within any *window_seconds*-wide
    sliding window are dropped.
    """
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    if max_entries <= 0:
        raise ValueError("max_entries must be positive")

    window = RateWindow(window_seconds=window_seconds, max_entries=max_entries)
    for entry in entries:
        if window.allow(entry):
            yield entry


def throttle_entries(
    entries: Iterator[LogEntry],
    min_gap_seconds: float,
) -> Iterator[LogEntry]:
    """Yield entries ensuring a minimum time gap between consecutive entries.

    When two entries are closer than *min_gap_seconds* apart, the later
    one is dropped.
    """
    if min_gap_seconds < 0:
        raise ValueError("min_gap_seconds must be non-negative")

    last_ts: datetime | None = None
    gap = timedelta(seconds=min_gap_seconds)
    for entry in entries:
        if last_ts is None or (entry.timestamp - last_ts) >= gap:
            last_ts = entry.timestamp
            yield entry
