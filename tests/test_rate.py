"""Tests for logslice.rate."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.rate import RateWindow, rate_limit_entries, throttle_entries


def _entry(ts: str, severity: str = "INFO", message: str = "msg") -> LogEntry:
    return LogEntry(
        timestamp=datetime.fromisoformat(ts).replace(tzinfo=timezone.utc),
        severity=severity,
        message=message,
        raw=f"{ts} {severity} {message}",
    )


# --- RateWindow ---

def test_rate_window_allows_within_limit():
    w = RateWindow(window_seconds=60, max_entries=3)
    e = _entry("2024-01-01T00:00:00")
    assert w.allow(e) is True
    assert w.allow(e) is True
    assert w.allow(e) is True


def test_rate_window_blocks_over_limit():
    w = RateWindow(window_seconds=60, max_entries=2)
    e = _entry("2024-01-01T00:00:00")
    w.allow(e)
    w.allow(e)
    assert w.allow(e) is False


def test_rate_window_evicts_old_entries():
    w = RateWindow(window_seconds=10, max_entries=2)
    e1 = _entry("2024-01-01T00:00:00")
    e2 = _entry("2024-01-01T00:00:05")
    e3 = _entry("2024-01-01T00:00:11")  # outside window of e1
    w.allow(e1)
    w.allow(e2)
    # e1 is now outside the window relative to e3
    assert w.allow(e3) is True


def test_rate_window_current_count():
    w = RateWindow(window_seconds=60, max_entries=10)
    e = _entry("2024-01-01T00:00:30")
    w.allow(e)
    w.allow(e)
    assert w.current_count(e.timestamp) == 2


# --- rate_limit_entries ---

def test_rate_limit_entries_all_pass_under_limit():
    entries = [_entry(f"2024-01-01T00:0{i}:00") for i in range(3)]
    result = list(rate_limit_entries(iter(entries), window_seconds=60, max_entries=10))
    assert len(result) == 3


def test_rate_limit_entries_drops_excess():
    entries = [_entry("2024-01-01T00:00:00") for _ in range(5)]
    result = list(rate_limit_entries(iter(entries), window_seconds=60, max_entries=3))
    assert len(result) == 3


def test_rate_limit_entries_invalid_window_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        list(rate_limit_entries(iter([]), window_seconds=0, max_entries=5))


def test_rate_limit_entries_invalid_max_raises():
    with pytest.raises(ValueError, match="max_entries"):
        list(rate_limit_entries(iter([]), window_seconds=10, max_entries=0))


# --- throttle_entries ---

def test_throttle_entries_all_pass_when_gap_large():
    entries = [
        _entry("2024-01-01T00:00:00"),
        _entry("2024-01-01T00:01:00"),
        _entry("2024-01-01T00:02:00"),
    ]
    result = list(throttle_entries(iter(entries), min_gap_seconds=30))
    assert len(result) == 3


def test_throttle_entries_drops_too_close():
    entries = [
        _entry("2024-01-01T00:00:00"),
        _entry("2024-01-01T00:00:01"),  # only 1s gap, dropped
        _entry("2024-01-01T00:00:10"),
    ]
    result = list(throttle_entries(iter(entries), min_gap_seconds=5))
    assert len(result) == 2
    assert result[0].timestamp.second == 0
    assert result[1].timestamp.second == 10


def test_throttle_entries_zero_gap_passes_all():
    entries = [_entry("2024-01-01T00:00:00") for _ in range(4)]
    result = list(throttle_entries(iter(entries), min_gap_seconds=0))
    assert len(result) == 4


def test_throttle_entries_negative_gap_raises():
    with pytest.raises(ValueError, match="min_gap_seconds"):
        list(throttle_entries(iter([]), min_gap_seconds=-1))
