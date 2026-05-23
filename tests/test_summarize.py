"""Tests for logslice.summarize."""

from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.summarize import (
    BucketSummary,
    _floor_to_bucket,
    format_summary,
    summarize_by_severity,
    summarize_by_time,
)


def _entry(severity: str, ts: datetime) -> LogEntry:
    return LogEntry(timestamp=ts, severity=severity, message="msg", raw="raw")


DT = datetime(2024, 3, 15, 10, 7, 0)


# --- _floor_to_bucket ---

def test_floor_to_bucket_5min():
    dt = datetime(2024, 1, 1, 10, 7, 45)
    result = _floor_to_bucket(dt, 5)
    assert result == datetime(2024, 1, 1, 10, 5, 0)


def test_floor_to_bucket_already_on_boundary():
    dt = datetime(2024, 1, 1, 10, 10, 0)
    result = _floor_to_bucket(dt, 10)
    assert result == datetime(2024, 1, 1, 10, 10, 0)


def test_floor_to_bucket_60min():
    dt = datetime(2024, 1, 1, 14, 59, 59)
    result = _floor_to_bucket(dt, 60)
    assert result == datetime(2024, 1, 1, 14, 0, 0)


# --- summarize_by_severity ---

def test_summarize_by_severity_empty():
    assert summarize_by_severity([]) == {}


def test_summarize_by_severity_counts():
    entries = [
        _entry("ERROR", DT),
        _entry("INFO", DT),
        _entry("ERROR", DT),
        _entry("WARNING", DT),
    ]
    result = summarize_by_severity(entries)
    assert result == {"ERROR": 2, "INFO": 1, "WARNING": 1}


def test_summarize_by_severity_single_level():
    entries = [_entry("DEBUG", DT)] * 5
    result = summarize_by_severity(entries)
    assert result == {"DEBUG": 5}


# --- summarize_by_time ---

def test_summarize_by_time_empty():
    assert summarize_by_time([]) == []


def test_summarize_by_time_invalid_bucket_raises():
    with pytest.raises(ValueError):
        summarize_by_time([], bucket_minutes=0)


def test_summarize_by_time_groups_correctly():
    entries = [
        _entry("INFO", datetime(2024, 1, 1, 10, 1)),
        _entry("ERROR", datetime(2024, 1, 1, 10, 3)),
        _entry("INFO", datetime(2024, 1, 1, 10, 6)),
    ]
    result = summarize_by_time(entries, bucket_minutes=5)
    assert len(result) == 2
    assert result[0].bucket_start == datetime(2024, 1, 1, 10, 0)
    assert result[0].counts == {"INFO": 1, "ERROR": 1}
    assert result[0].total == 2
    assert result[1].bucket_start == datetime(2024, 1, 1, 10, 5)
    assert result[1].total == 1


def test_summarize_by_time_skips_none_timestamps():
    entries = [LogEntry(timestamp=None, severity="INFO", message="x", raw="x")]
    result = summarize_by_time(entries, bucket_minutes=5)
    assert result == []


# --- format_summary ---

def test_format_summary_empty():
    assert format_summary([]) == "No entries to summarize."


def test_format_summary_contains_timestamp_and_total():
    s = BucketSummary(
        bucket_start=datetime(2024, 3, 15, 10, 5),
        counts={"INFO": 3, "ERROR": 1},
        total=4,
    )
    output = format_summary([s])
    assert "2024-03-15 10:05" in output
    assert "4" in output
    assert "INFO=3" in output
    assert "ERROR=1" in output
