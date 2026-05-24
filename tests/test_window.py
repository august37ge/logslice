"""Tests for logslice.window sliding-window analysis."""
from datetime import datetime, timedelta, timezone

import pytest

from logslice.parser import LogEntry
from logslice.window import (
    WindowSlice,
    format_window_summary,
    sliding_windows,
)


def _entry(minute: int, severity: str = "INFO", message: str = "msg") -> LogEntry:
    ts = datetime(2024, 1, 1, 0, minute, 0, tzinfo=timezone.utc)
    return LogEntry(timestamp=ts, severity=severity, message=message, raw=message)


# ---------------------------------------------------------------------------
# sliding_windows
# ---------------------------------------------------------------------------

def test_sliding_windows_empty_yields_nothing():
    result = list(sliding_windows([], timedelta(minutes=5), timedelta(minutes=1)))
    assert result == []


def test_sliding_windows_raises_on_zero_window():
    with pytest.raises(ValueError, match="window_size"):
        list(sliding_windows([_entry(0)], timedelta(0), timedelta(minutes=1)))


def test_sliding_windows_raises_on_zero_step():
    with pytest.raises(ValueError, match="step"):
        list(sliding_windows([_entry(0)], timedelta(minutes=5), timedelta(0)))


def test_sliding_windows_single_entry_one_bucket():
    entries = [_entry(0)]
    slices = list(sliding_windows(entries, timedelta(minutes=5), timedelta(minutes=5)))
    assert len(slices) == 1
    assert slices[0].count == 1


def test_sliding_windows_non_overlapping_buckets():
    entries = [_entry(0), _entry(5), _entry(10)]
    slices = list(sliding_windows(entries, timedelta(minutes=5), timedelta(minutes=5)))
    # windows: [0,5), [5,10), [10,15)
    assert slices[0].count == 1
    assert slices[1].count == 1
    assert slices[2].count == 1


def test_sliding_windows_overlapping_entries_counted_in_multiple_windows():
    entries = [_entry(0), _entry(2), _entry(4)]
    slices = list(sliding_windows(entries, timedelta(minutes=5), timedelta(minutes=2)))
    # window [0,5): minutes 0,2,4 -> 3 entries
    assert slices[0].count == 3
    # window [2,7): minutes 2,4 -> 2 entries
    assert slices[1].count == 2


def test_sliding_windows_window_start_and_end_set_correctly():
    entries = [_entry(3)]
    size = timedelta(minutes=10)
    step = timedelta(minutes=10)
    slices = list(sliding_windows(entries, size, step))
    assert slices[0].window_end == slices[0].window_start + size


# ---------------------------------------------------------------------------
# WindowSlice helpers
# ---------------------------------------------------------------------------

def test_window_slice_severity_counts():
    entries = [
        _entry(0, "ERROR"),
        _entry(1, "ERROR"),
        _entry(2, "INFO"),
    ]
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    ws = WindowSlice(window_start=ts, window_end=ts + timedelta(minutes=5), entries=entries)
    counts = ws.severity_counts
    assert counts["ERROR"] == 2
    assert counts["INFO"] == 1


def test_window_slice_count_matches_entries_length():
    entries = [_entry(i) for i in range(7)]
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    ws = WindowSlice(window_start=ts, window_end=ts + timedelta(minutes=10), entries=entries)
    assert ws.count == 7


# ---------------------------------------------------------------------------
# format_window_summary
# ---------------------------------------------------------------------------

def test_format_window_summary_empty():
    assert format_window_summary([]) == ""


def test_format_window_summary_contains_count():
    entries = [_entry(0, "WARN")]
    slices = list(sliding_windows(entries, timedelta(minutes=5), timedelta(minutes=5)))
    summary = format_window_summary(slices)
    assert "count=1" in summary
    assert "WARN:1" in summary


def test_format_window_summary_multiple_lines():
    entries = [_entry(0), _entry(10)]
    slices = list(sliding_windows(entries, timedelta(minutes=5), timedelta(minutes=5)))
    summary = format_window_summary(slices)
    assert summary.count("\n") >= 1
