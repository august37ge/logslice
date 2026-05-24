"""Tests for logslice.aggregate."""

from __future__ import annotations

from datetime import datetime

import pytest

from logslice.aggregate import (
    AggregateWindow,
    _floor_to_window,
    aggregate_entries,
    format_aggregate,
)
from logslice.parser import LogEntry


def _entry(ts: str, severity: str = "INFO", source: str = "app") -> LogEntry:
    return LogEntry(
        timestamp=datetime.fromisoformat(ts),
        severity=severity,
        message="msg",
        source=source,
        raw=f"{ts} [{severity}] msg",
    )


# ---------------------------------------------------------------------------
# _floor_to_window
# ---------------------------------------------------------------------------

def test_floor_to_window_5min_on_boundary():
    dt = datetime(2024, 1, 1, 12, 0, 30)
    result = _floor_to_window(dt, 5)
    assert result == datetime(2024, 1, 1, 12, 0, 0)


def test_floor_to_window_5min_mid_bucket():
    dt = datetime(2024, 1, 1, 12, 7, 45)
    result = _floor_to_window(dt, 5)
    assert result == datetime(2024, 1, 1, 12, 5, 0)


def test_floor_to_window_60min():
    dt = datetime(2024, 1, 1, 14, 37, 0)
    result = _floor_to_window(dt, 60)
    assert result == datetime(2024, 1, 1, 14, 0, 0)


# ---------------------------------------------------------------------------
# aggregate_entries
# ---------------------------------------------------------------------------

def test_aggregate_entries_empty_returns_empty_list():
    result = aggregate_entries([])
    assert result == []


def test_aggregate_entries_invalid_window_raises():
    with pytest.raises(ValueError):
        aggregate_entries([], window_minutes=0)


def test_aggregate_entries_single_entry():
    entries = [_entry("2024-01-01T10:03:00")]
    windows = aggregate_entries(entries, window_minutes=5)
    assert len(windows) == 1
    assert windows[0].total == 1


def test_aggregate_entries_groups_into_correct_buckets():
    entries = [
        _entry("2024-01-01T10:01:00"),
        _entry("2024-01-01T10:03:00"),
        _entry("2024-01-01T10:06:00"),
    ]
    windows = aggregate_entries(entries, window_minutes=5)
    assert len(windows) == 2
    assert windows[0].total == 2
    assert windows[1].total == 1


def test_aggregate_entries_counts_by_severity():
    entries = [
        _entry("2024-01-01T10:01:00", severity="INFO"),
        _entry("2024-01-01T10:02:00", severity="ERROR"),
        _entry("2024-01-01T10:03:00", severity="INFO"),
    ]
    windows = aggregate_entries(entries, window_minutes=5)
    assert len(windows) == 1
    assert windows[0].by_severity["INFO"] == 2
    assert windows[0].by_severity["ERROR"] == 1


def test_aggregate_entries_counts_by_source():
    entries = [
        _entry("2024-01-01T10:01:00", source="web"),
        _entry("2024-01-01T10:02:00", source="db"),
        _entry("2024-01-01T10:03:00", source="web"),
    ]
    windows = aggregate_entries(entries, window_minutes=5)
    assert windows[0].by_source["web"] == 2
    assert windows[0].by_source["db"] == 1


def test_aggregate_entries_sorted_by_window_start():
    entries = [
        _entry("2024-01-01T10:11:00"),
        _entry("2024-01-01T10:01:00"),
        _entry("2024-01-01T10:06:00"),
    ]
    windows = aggregate_entries(entries, window_minutes=5)
    starts = [w.window_start for w in windows]
    assert starts == sorted(starts)


def test_aggregate_entries_window_end_correct():
    entries = [_entry("2024-01-01T10:01:00")]
    windows = aggregate_entries(entries, window_minutes=10)
    assert (windows[0].window_end - windows[0].window_start).seconds == 600


# ---------------------------------------------------------------------------
# format_aggregate
# ---------------------------------------------------------------------------

def test_format_aggregate_empty_returns_no_data():
    assert format_aggregate([]) == "No data."


def test_format_aggregate_contains_window_start():
    entries = [_entry("2024-01-01T10:01:00")]
    windows = aggregate_entries(entries, window_minutes=5)
    output = format_aggregate(windows)
    assert "2024-01-01 10:00:00" in output


def test_format_aggregate_contains_total():
    entries = [_entry("2024-01-01T10:01:00")] * 3
    windows = aggregate_entries(entries, window_minutes=5)
    output = format_aggregate(windows)
    assert "3" in output
