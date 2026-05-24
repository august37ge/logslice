"""Replay log entries at their original timing or a scaled rate."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Callable, Generator, Iterable, Optional

from logslice.parser import LogEntry


def _to_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware (UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def replay_entries(
    entries: Iterable[LogEntry],
    speed: float = 1.0,
    on_entry: Optional[Callable[[LogEntry], None]] = None,
) -> Generator[LogEntry, None, None]:
    """Yield entries with real-time delays proportional to their timestamps.

    Args:
        entries: Iterable of LogEntry objects sorted by timestamp.
        speed: Playback multiplier. 2.0 = twice as fast, 0.5 = half speed.
        on_entry: Optional callback invoked just before each entry is yielded.

    Yields:
        LogEntry objects in original order.
    """
    if speed <= 0:
        raise ValueError(f"speed must be positive, got {speed}")

    prev_log_time: Optional[datetime] = None
    prev_wall_time: Optional[float] = None

    for entry in entries:
        log_time = _to_utc(entry.timestamp)

        if prev_log_time is not None and prev_wall_time is not None:
            log_delta = (log_time - prev_log_time).total_seconds()
            wall_delay = log_delta / speed
            if wall_delay > 0:
                elapsed = time.monotonic() - prev_wall_time
                sleep_for = wall_delay - elapsed
                if sleep_for > 0:
                    time.sleep(sleep_for)

        prev_log_time = log_time
        prev_wall_time = time.monotonic()

        if on_entry is not None:
            on_entry(entry)

        yield entry


def replay_summary(entries: Iterable[LogEntry], speed: float = 1.0) -> dict:
    """Return metadata about a replay run without actually sleeping."""
    entry_list = list(entries)
    if not entry_list:
        return {"count": 0, "duration_seconds": 0.0, "speed": speed}

    first = _to_utc(entry_list[0].timestamp)
    last = _to_utc(entry_list[-1].timestamp)
    log_duration = (last - first).total_seconds()
    wall_duration = log_duration / speed if speed > 0 else 0.0

    return {
        "count": len(entry_list),
        "log_duration_seconds": log_duration,
        "wall_duration_seconds": wall_duration,
        "speed": speed,
    }
