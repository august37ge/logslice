"""Tests for logslice.replay."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from logslice.parser import LogEntry
from logslice.replay import replay_entries, replay_summary, _to_utc


def _entry(ts: str, msg: str = "hello") -> LogEntry:
    dt = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    return LogEntry(timestamp=dt, severity="INFO", message=msg, raw=f"{ts} INFO {msg}")


# ---------------------------------------------------------------------------
# _to_utc
# ---------------------------------------------------------------------------

def test_to_utc_naive_gets_utc():
    naive = datetime(2024, 1, 1, 12, 0, 0)
    result = _to_utc(naive)
    assert result.tzinfo == timezone.utc


def test_to_utc_aware_stays_utc():
    aware = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = _to_utc(aware)
    assert result == aware


# ---------------------------------------------------------------------------
# replay_entries
# ---------------------------------------------------------------------------

def test_replay_invalid_speed_raises():
    with pytest.raises(ValueError, match="speed must be positive"):
        list(replay_entries([], speed=0))


def test_replay_negative_speed_raises():
    with pytest.raises(ValueError):
        list(replay_entries([], speed=-1.0))


def test_replay_empty_yields_nothing():
    result = list(replay_entries([], speed=1.0))
    assert result == []


def test_replay_yields_all_entries():
    entries = [
        _entry("2024-01-01T00:00:00"),
        _entry("2024-01-01T00:00:01"),
        _entry("2024-01-01T00:00:02"),
    ]
    with patch("logslice.replay.time.sleep"):
        result = list(replay_entries(entries, speed=1000.0))
    assert len(result) == 3


def test_replay_calls_on_entry_callback():
    entries = [_entry("2024-01-01T00:00:00"), _entry("2024-01-01T00:00:01")]
    callback = MagicMock()
    with patch("logslice.replay.time.sleep"):
        list(replay_entries(entries, speed=1000.0, on_entry=callback))
    assert callback.call_count == 2


def test_replay_single_entry_no_sleep():
    entries = [_entry("2024-01-01T00:00:00")]
    with patch("logslice.replay.time.sleep") as mock_sleep:
        list(replay_entries(entries, speed=1.0))
    mock_sleep.assert_not_called()


def test_replay_preserves_order():
    entries = [
        _entry("2024-01-01T00:00:00", "first"),
        _entry("2024-01-01T00:00:05", "second"),
        _entry("2024-01-01T00:00:10", "third"),
    ]
    with patch("logslice.replay.time.sleep"):
        result = list(replay_entries(entries, speed=9999.0))
    assert [e.message for e in result] == ["first", "second", "third"]


# ---------------------------------------------------------------------------
# replay_summary
# ---------------------------------------------------------------------------

def test_replay_summary_empty():
    summary = replay_summary([], speed=1.0)
    assert summary["count"] == 0
    assert summary["duration_seconds"] == 0.0


def test_replay_summary_count():
    entries = [
        _entry("2024-01-01T00:00:00"),
        _entry("2024-01-01T00:01:00"),
    ]
    summary = replay_summary(entries, speed=1.0)
    assert summary["count"] == 2


def test_replay_summary_log_duration():
    entries = [
        _entry("2024-01-01T00:00:00"),
        _entry("2024-01-01T00:00:10"),
    ]
    summary = replay_summary(entries, speed=1.0)
    assert summary["log_duration_seconds"] == pytest.approx(10.0)


def test_replay_summary_wall_duration_scaled():
    entries = [
        _entry("2024-01-01T00:00:00"),
        _entry("2024-01-01T00:00:20"),
    ]
    summary = replay_summary(entries, speed=4.0)
    assert summary["wall_duration_seconds"] == pytest.approx(5.0)


def test_replay_summary_speed_stored():
    entries = [_entry("2024-01-01T00:00:00")]
    summary = replay_summary(entries, speed=2.5)
    assert summary["speed"] == 2.5
