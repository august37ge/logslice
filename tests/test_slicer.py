"""Tests for logslice.slicer — time-range and severity filtering."""

from datetime import datetime

import pytest

from logslice.slicer import slice_logs

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

SAMPLE_LINES = [
    "2024-01-15 08:00:00 DEBUG    Starting up",
    "2024-01-15 09:00:00 INFO     Service ready",
    "2024-01-15 10:00:00 WARNING  High memory usage",
    "2024-01-15 11:00:00 ERROR    Connection refused",
    "2024-01-15 12:00:00 CRITICAL Disk full",
    "this line is not a valid log entry",
]


def _collect(lines, **kwargs):
    return list(slice_logs(iter(lines), **kwargs))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_no_filters_returns_all_valid_entries():
    results = _collect(SAMPLE_LINES)
    assert len(results) == 5


def test_invalid_lines_are_skipped():
    results = _collect(SAMPLE_LINES)
    assert all(r is not None for r in results)


def test_start_filter_excludes_earlier_entries():
    start = datetime(2024, 1, 15, 10, 0, 0)
    results = _collect(SAMPLE_LINES, start=start)
    assert len(results) == 3
    assert results[0].severity == "WARNING"


def test_end_filter_excludes_later_entries():
    end = datetime(2024, 1, 15, 10, 0, 0)
    results = _collect(SAMPLE_LINES, end=end)
    assert len(results) == 3
    assert results[-1].severity == "WARNING"


def test_start_and_end_filter_combined():
    start = datetime(2024, 1, 15, 9, 0, 0)
    end = datetime(2024, 1, 15, 11, 0, 0)
    results = _collect(SAMPLE_LINES, start=start, end=end)
    assert len(results) == 3
    severities = [r.severity for r in results]
    assert severities == ["INFO", "WARNING", "ERROR"]


def test_min_severity_filters_below_threshold():
    results = _collect(SAMPLE_LINES, min_severity="ERROR")
    assert len(results) == 2
    assert all(r.severity in {"ERROR", "CRITICAL"} for r in results)


def test_min_severity_debug_returns_all():
    results = _collect(SAMPLE_LINES, min_severity="DEBUG")
    assert len(results) == 5


def test_combined_time_and_severity_filter():
    start = datetime(2024, 1, 15, 9, 0, 0)
    results = _collect(SAMPLE_LINES, start=start, min_severity="WARNING")
    assert len(results) == 3
    assert results[0].severity == "WARNING"


def test_empty_input_returns_no_entries():
    results = _collect([])
    assert results == []


def test_timestamps_on_boundary_are_inclusive():
    start = datetime(2024, 1, 15, 8, 0, 0)
    end = datetime(2024, 1, 15, 12, 0, 0)
    results = _collect(SAMPLE_LINES, start=start, end=end)
    assert len(results) == 5
