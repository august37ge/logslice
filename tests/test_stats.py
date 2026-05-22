"""Tests for logslice.stats module."""
from datetime import datetime, timezone
from collections import Counter

import pytest

from logslice.parser import LogEntry
from logslice.stats import SliceStats, compute_stats, format_stats


def _make_entry(ts: str, severity: str, message: str = "msg") -> LogEntry:
    dt = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    return LogEntry(timestamp=dt, severity=severity, message=message, raw=f"{ts} {severity} {message}")


def test_compute_stats_empty():
    stats = compute_stats([])
    assert stats.total_entries == 0
    assert stats.earliest is None
    assert stats.latest is None
    assert stats.skipped_lines == 0


def test_compute_stats_counts_entries():
    entries = [
        _make_entry("2024-01-01T10:00:00", "INFO"),
        _make_entry("2024-01-01T11:00:00", "ERROR"),
        _make_entry("2024-01-01T12:00:00", "INFO"),
    ]
    stats = compute_stats(entries)
    assert stats.total_entries == 3
    assert stats.severity_counts["INFO"] == 2
    assert stats.severity_counts["ERROR"] == 1


def test_compute_stats_earliest_latest():
    entries = [
        _make_entry("2024-01-01T10:00:00", "DEBUG"),
        _make_entry("2024-01-01T08:00:00", "INFO"),
        _make_entry("2024-01-01T12:00:00", "WARN"),
    ]
    stats = compute_stats(entries)
    assert "08:00:00" in stats.earliest
    assert "12:00:00" in stats.latest


def test_compute_stats_skipped_lines():
    stats = compute_stats([], skipped=7)
    assert stats.skipped_lines == 7


def test_slice_stats_to_dict():
    stats = SliceStats(
        total_entries=5,
        severity_counts=Counter({"INFO": 3, "ERROR": 2}),
        earliest="2024-01-01T08:00:00",
        latest="2024-01-01T18:00:00",
        skipped_lines=1,
    )
    d = stats.to_dict()
    assert d["total_entries"] == 5
    assert d["severity_counts"] == {"INFO": 3, "ERROR": 2}
    assert d["skipped_lines"] == 1


def test_format_stats_contains_key_fields():
    entries = [
        _make_entry("2024-03-15T09:00:00", "INFO", "started"),
        _make_entry("2024-03-15T10:00:00", "ERROR", "failed"),
    ]
    stats = compute_stats(entries, skipped=3)
    text = format_stats(stats)
    assert "Total entries" in text
    assert "2" in text
    assert "Skipped lines" in text
    assert "INFO" in text
    assert "ERROR" in text


def test_format_stats_na_when_no_entries():
    stats = compute_stats([])
    text = format_stats(stats)
    assert "N/A" in text
