"""Tests for logslice.baseline."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from logslice.baseline import (
    BaselineSnapshot,
    capture,
    compare,
    format_diff,
    load_baseline,
    save_baseline,
)
from logslice.parser import LogEntry


def _entry(ts: str, severity: str, message: str = "msg") -> LogEntry:
    return LogEntry(
        timestamp=datetime.fromisoformat(ts).replace(tzinfo=timezone.utc),
        severity=severity,
        message=message,
        raw=f"{ts} {severity} {message}",
    )


def test_capture_empty_returns_zero_total():
    snap = capture([])
    assert snap.total == 0
    assert snap.severity_counts == {}
    assert snap.earliest is None
    assert snap.latest is None


def test_capture_counts_total():
    entries = [_entry("2024-01-01T00:00:00", "INFO") for _ in range(5)]
    snap = capture(entries)
    assert snap.total == 5


def test_capture_severity_counts():
    entries = [
        _entry("2024-01-01T00:00:00", "INFO"),
        _entry("2024-01-01T00:01:00", "ERROR"),
        _entry("2024-01-01T00:02:00", "info"),  # lowercase normalised
    ]
    snap = capture(entries)
    assert snap.severity_counts["INFO"] == 2
    assert snap.severity_counts["ERROR"] == 1


def test_capture_earliest_latest():
    entries = [
        _entry("2024-01-01T01:00:00", "INFO"),
        _entry("2024-01-01T00:00:00", "INFO"),
        _entry("2024-01-01T02:00:00", "INFO"),
    ]
    snap = capture(entries)
    assert "00:00:00" in snap.earliest
    assert "02:00:00" in snap.latest


def test_compare_total_delta():
    old = BaselineSnapshot(total=10, severity_counts={"INFO": 10})
    new = BaselineSnapshot(total=15, severity_counts={"INFO": 15})
    diff = compare(old, new)
    assert diff.total_delta == 5


def test_compare_added_severity():
    old = BaselineSnapshot(total=5, severity_counts={"INFO": 5})
    new = BaselineSnapshot(total=7, severity_counts={"INFO": 5, "ERROR": 2})
    diff = compare(old, new)
    assert "ERROR" in diff.added_severities
    assert diff.added_severities["ERROR"] == 2


def test_compare_removed_severity():
    old = BaselineSnapshot(total=7, severity_counts={"INFO": 5, "WARN": 2})
    new = BaselineSnapshot(total=5, severity_counts={"INFO": 5})
    diff = compare(old, new)
    assert "WARN" in diff.removed_severities


def test_compare_changed_severity():
    old = BaselineSnapshot(total=10, severity_counts={"INFO": 10})
    new = BaselineSnapshot(total=6, severity_counts={"INFO": 6})
    diff = compare(old, new)
    assert diff.changed_severities["INFO"] == -4


def test_save_and_load_roundtrip(tmp_path):
    snap = BaselineSnapshot(total=3, severity_counts={"DEBUG": 3}, earliest="2024-01-01T00:00:00", latest="2024-01-01T01:00:00")
    p = tmp_path / "baseline.json"
    save_baseline(snap, p)
    loaded = load_baseline(p)
    assert loaded.total == snap.total
    assert loaded.severity_counts == snap.severity_counts
    assert loaded.earliest == snap.earliest


def test_save_creates_parent_dirs(tmp_path):
    snap = BaselineSnapshot(total=1, severity_counts={"INFO": 1})
    p = tmp_path / "nested" / "dir" / "baseline.json"
    save_baseline(snap, p)
    assert p.exists()


def test_format_diff_no_changes():
    old = BaselineSnapshot(total=5, severity_counts={"INFO": 5})
    new = BaselineSnapshot(total=5, severity_counts={"INFO": 5})
    diff = compare(old, new)
    result = format_diff(diff)
    assert "No severity changes" in result
    assert "0" in result


def test_format_diff_shows_added():
    old = BaselineSnapshot(total=5, severity_counts={"INFO": 5})
    new = BaselineSnapshot(total=7, severity_counts={"INFO": 5, "CRITICAL": 2})
    diff = compare(old, new)
    result = format_diff(diff)
    assert "CRITICAL" in result
    assert "new" in result
