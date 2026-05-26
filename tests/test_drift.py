"""Tests for logslice.drift."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.drift import (
    DriftEntry,
    detect_drift,
    drift_only,
    format_drift_report,
)
from logslice.parser import LogEntry


def _entry(ts: datetime, message: str = "msg") -> LogEntry:
    return LogEntry(timestamp=ts, severity="INFO", message=message, raw=f"{ts} INFO {message}")


def _dt(hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, second, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# detect_drift
# ---------------------------------------------------------------------------

def test_detect_drift_single_entry_no_drift():
    entries = [_entry(_dt(10))]
    results = list(detect_drift(entries))
    assert len(results) == 1
    assert results[0].is_drift is False
    assert results[0].previous_ts is None
    assert results[0].delta_seconds == 0.0


def test_detect_drift_monotonic_no_drift():
    entries = [_entry(_dt(10)), _entry(_dt(10, 1)), _entry(_dt(10, 2))]
    results = list(detect_drift(entries))
    assert all(not r.is_drift for r in results)


def test_detect_drift_flags_backwards_jump():
    entries = [_entry(_dt(10, 5)), _entry(_dt(10, 0))]
    results = list(detect_drift(entries))
    assert results[0].is_drift is False
    assert results[1].is_drift is True
    assert results[1].delta_seconds == pytest.approx(-300.0)


def test_detect_drift_threshold_allows_small_backwards():
    entries = [_entry(_dt(10, 0, 5)), _entry(_dt(10, 0, 3))]
    # threshold of 3 seconds: delta is -2 s, within tolerance
    results = list(detect_drift(entries, threshold_seconds=3.0))
    assert results[1].is_drift is False


def test_detect_drift_threshold_exceeded():
    entries = [_entry(_dt(10, 0, 0)), _entry(_dt(9, 59, 50))]
    # delta = -10 s, threshold = 5 s
    results = list(detect_drift(entries, threshold_seconds=5.0))
    assert results[1].is_drift is True


def test_detect_drift_same_timestamp_not_drift():
    ts = _dt(10)
    entries = [_entry(ts), _entry(ts)]
    results = list(detect_drift(entries))
    assert results[1].is_drift is False
    assert results[1].delta_seconds == 0.0


def test_detect_drift_previous_ts_populated():
    t1, t2 = _dt(10), _dt(10, 1)
    entries = [_entry(t1), _entry(t2)]
    results = list(detect_drift(entries))
    assert results[1].previous_ts == t1


def test_detect_drift_empty_input():
    assert list(detect_drift([])) == []


# ---------------------------------------------------------------------------
# drift_only
# ---------------------------------------------------------------------------

def test_drift_only_returns_only_flagged():
    entries = [_entry(_dt(10)), _entry(_dt(10, 1)), _entry(_dt(9, 59))]
    result = drift_only(entries)
    assert len(result) == 1
    assert result[0].entry.timestamp == _dt(9, 59)


def test_drift_only_empty_when_no_drift():
    entries = [_entry(_dt(10)), _entry(_dt(10, 1))]
    assert drift_only(entries) == []


# ---------------------------------------------------------------------------
# format_drift_report
# ---------------------------------------------------------------------------

def test_format_drift_report_no_drifts():
    assert format_drift_report([]) == "No timestamp drift detected."


def test_format_drift_report_contains_count():
    entries = [_entry(_dt(10)), _entry(_dt(9, 50))]
    drifts = drift_only(entries)
    report = format_drift_report(drifts)
    assert "1 occurrence" in report


def test_format_drift_report_contains_delta():
    entries = [_entry(_dt(10)), _entry(_dt(9, 50))]
    drifts = drift_only(entries)
    report = format_drift_report(drifts)
    assert "delta=" in report
    assert "-600" in report
