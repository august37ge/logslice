"""Tests for logslice.report_baseline."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from logslice.baseline import BaselineDiff, BaselineSnapshot, save_baseline
from logslice.parser import LogEntry
from logslice.report_baseline import (
    build_and_compare,
    format_baseline_report,
    regression_detected,
)


def _entry(ts: str, severity: str, message: str = "msg") -> LogEntry:
    return LogEntry(
        timestamp=datetime.fromisoformat(ts).replace(tzinfo=timezone.utc),
        severity=severity,
        message=message,
        raw=f"{ts} {severity} {message}",
    )


_ENTRIES = [
    _entry("2024-01-01T00:00:00", "INFO"),
    _entry("2024-01-01T00:01:00", "ERROR"),
    _entry("2024-01-01T00:02:00", "INFO"),
]


def test_first_run_returns_none(tmp_path):
    p = tmp_path / "baseline.json"
    result = build_and_compare(iter(_ENTRIES), p)
    assert result is None


def test_first_run_creates_file(tmp_path):
    p = tmp_path / "baseline.json"
    build_and_compare(iter(_ENTRIES), p)
    assert p.exists()


def test_second_run_returns_diff(tmp_path):
    p = tmp_path / "baseline.json"
    build_and_compare(iter(_ENTRIES), p)
    diff = build_and_compare(iter(_ENTRIES), p)
    assert diff is not None
    assert diff.total_delta == 0


def test_update_flag_refreshes_baseline(tmp_path):
    p = tmp_path / "baseline.json"
    build_and_compare(iter(_ENTRIES), p)
    new_entries = _ENTRIES + [_entry("2024-01-01T00:03:00", "CRITICAL")]
    build_and_compare(iter(new_entries), p, update=True)
    # Third run should compare against the updated baseline
    diff = build_and_compare(iter(new_entries), p)
    assert diff is not None
    assert diff.total_delta == 0


def test_format_none_diff_plain():
    result = format_baseline_report(None, fmt="plain")
    assert "Baseline created" in result


def test_format_none_diff_json():
    result = format_baseline_report(None, fmt="json")
    data = json.loads(result)
    assert data["status"] == "baseline_created"


def test_format_diff_plain_contains_delta():
    diff = BaselineDiff(total_delta=3, added_severities={}, removed_severities={}, changed_severities={})
    result = format_baseline_report(diff, fmt="plain")
    assert "+3" in result or "3" in result


def test_format_diff_json_is_valid():
    diff = BaselineDiff(
        total_delta=1,
        added_severities={"CRITICAL": 1},
        removed_severities={},
        changed_severities={},
    )
    result = format_baseline_report(diff, fmt="json")
    data = json.loads(result)
    assert data["total_delta"] == 1
    assert data["added_severities"]["CRITICAL"] == 1


def test_regression_detected_on_added_error():
    diff = BaselineDiff(
        total_delta=2,
        added_severities={"ERROR": 2},
        removed_severities={},
        changed_severities={},
    )
    assert regression_detected(diff, severity="ERROR") is True


def test_regression_not_detected_when_error_unchanged():
    diff = BaselineDiff(
        total_delta=0,
        added_severities={},
        removed_severities={},
        changed_severities={},
    )
    assert regression_detected(diff, severity="ERROR") is False


def test_regression_not_detected_on_none():
    assert regression_detected(None) is False


def test_regression_detected_on_changed_severity():
    diff = BaselineDiff(
        total_delta=5,
        added_severities={},
        removed_severities={},
        changed_severities={"CRITICAL": 5},
    )
    assert regression_detected(diff, severity="CRITICAL") is True
