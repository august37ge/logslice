"""Tests for logslice.heatmap."""
from datetime import datetime, timezone

import pytest

from logslice.heatmap import (
    HeatmapCell,
    Heatmap,
    _floor_to_bucket,
    build_heatmap,
    format_heatmap,
)
from logslice.parser import LogEntry


def _entry(ts: datetime, severity: str, message: str = "msg") -> LogEntry:
    return LogEntry(timestamp=ts, severity=severity, message=message, raw=message)


def _dt(h: int, m: int = 0) -> datetime:
    return datetime(2024, 6, 1, h, m, 0, tzinfo=timezone.utc)


# --- _floor_to_bucket ---

def test_floor_to_bucket_on_boundary():
    dt = _dt(10, 0)
    assert _floor_to_bucket(dt, 60) == _dt(10, 0)


def test_floor_to_bucket_mid_hour():
    dt = _dt(10, 45)
    assert _floor_to_bucket(dt, 60) == _dt(10, 0)


def test_floor_to_bucket_30min():
    dt = _dt(10, 35)
    assert _floor_to_bucket(dt, 30) == _dt(10, 30)


def test_floor_to_bucket_5min():
    dt = _dt(10, 17)
    assert _floor_to_bucket(dt, 5) == _dt(10, 15)


# --- build_heatmap ---

def test_build_heatmap_empty_returns_empty_grid():
    hm = build_heatmap([])
    assert hm.grid == {}


def test_build_heatmap_single_entry():
    entries = [_entry(_dt(9, 10), "INFO")]
    hm = build_heatmap(entries, bucket_minutes=60)
    bucket = _dt(9, 0)
    assert bucket in hm.grid
    assert hm.grid[bucket]["INFO"] == 1


def test_build_heatmap_groups_into_buckets():
    entries = [
        _entry(_dt(9, 5), "ERROR"),
        _entry(_dt(9, 50), "ERROR"),
        _entry(_dt(10, 10), "ERROR"),
    ]
    hm = build_heatmap(entries, bucket_minutes=60)
    assert hm.grid[_dt(9, 0)]["ERROR"] == 2
    assert hm.grid[_dt(10, 0)]["ERROR"] == 1


def test_build_heatmap_counts_by_severity():
    entries = [
        _entry(_dt(8, 0), "INFO"),
        _entry(_dt(8, 0), "ERROR"),
        _entry(_dt(8, 0), "ERROR"),
    ]
    hm = build_heatmap(entries, bucket_minutes=60)
    bucket = _dt(8, 0)
    assert hm.grid[bucket]["INFO"] == 1
    assert hm.grid[bucket]["ERROR"] == 2


def test_build_heatmap_custom_severities_list():
    entries = [_entry(_dt(7, 0), "DEBUG")]
    hm = build_heatmap(entries, severities=["INFO", "ERROR"])
    assert hm.severities == ["INFO", "ERROR"]


def test_build_heatmap_raises_on_zero_bucket():
    with pytest.raises(ValueError):
        build_heatmap([], bucket_minutes=0)


def test_build_heatmap_raises_on_negative_bucket():
    with pytest.raises(ValueError):
        build_heatmap([], bucket_minutes=-5)


# --- format_heatmap ---

def test_format_heatmap_empty_returns_no_data():
    hm = Heatmap(bucket_minutes=60)
    assert format_heatmap(hm) == "(no data)"


def test_format_heatmap_contains_severity_header():
    entries = [_entry(_dt(10, 0), "INFO")]
    hm = build_heatmap(entries)
    output = format_heatmap(hm)
    assert "INFO" in output


def test_format_heatmap_contains_timestamp():
    entries = [_entry(_dt(14, 30), "WARNING")]
    hm = build_heatmap(entries, bucket_minutes=60)
    output = format_heatmap(hm)
    assert "2024-06-01 14:00" in output


def test_format_heatmap_multiple_rows():
    entries = [
        _entry(_dt(8, 0), "INFO"),
        _entry(_dt(9, 0), "ERROR"),
    ]
    hm = build_heatmap(entries, bucket_minutes=60)
    output = format_heatmap(hm)
    assert "2024-06-01 08:00" in output
    assert "2024-06-01 09:00" in output
