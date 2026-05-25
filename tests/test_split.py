"""Tests for logslice.split and logslice.report_split."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.split import (
    SplitResult,
    get_key_fn,
    key_by_date,
    key_by_hour,
    key_by_severity,
    key_by_source,
    split_entries,
)
from logslice.report_split import (
    bucket_counts,
    format_split_report,
    largest_bucket,
)


def _entry(
    severity: str = "INFO",
    message: str = "msg",
    source: str = "",
    ts: datetime | None = None,
) -> LogEntry:
    if ts is None:
        ts = datetime(2024, 6, 15, 12, 30, 0, tzinfo=timezone.utc)
    return LogEntry(timestamp=ts, severity=severity, message=message, source=source)


# ---------------------------------------------------------------------------
# split_entries
# ---------------------------------------------------------------------------

def test_split_entries_empty_input_returns_empty_result():
    result = split_entries([], key_by_severity)
    assert result.buckets == {}
    assert result.total() == 0


def test_split_by_severity_groups_correctly():
    entries = [_entry("INFO"), _entry("ERROR"), _entry("INFO"), _entry("DEBUG")]
    result = split_entries(entries, key_by_severity)
    assert set(result.keys) == {"INFO", "ERROR", "DEBUG"}
    assert len(result.get("INFO")) == 2
    assert len(result.get("ERROR")) == 1
    assert len(result.get("DEBUG")) == 1


def test_split_total_equals_input_length():
    entries = [_entry() for _ in range(7)]
    result = split_entries(entries, key_by_severity)
    assert result.total() == 7


def test_split_by_date_uses_date_string():
    ts1 = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    ts2 = datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc)
    entries = [_entry(ts=ts1), _entry(ts=ts1), _entry(ts=ts2)]
    result = split_entries(entries, key_by_date)
    assert "2024-01-01" in result.keys
    assert "2024-01-02" in result.keys
    assert len(result.get("2024-01-01")) == 2


def test_split_by_hour():
    ts1 = datetime(2024, 1, 1, 9, 45, tzinfo=timezone.utc)
    ts2 = datetime(2024, 1, 1, 10, 5, tzinfo=timezone.utc)
    result = split_entries([_entry(ts=ts1), _entry(ts=ts2)], key_by_hour)
    assert "2024-01-01T09" in result.keys
    assert "2024-01-01T10" in result.keys


def test_split_by_source():
    entries = [_entry(source="app"), _entry(source="db"), _entry(source="app")]
    result = split_entries(entries, key_by_source)
    assert len(result.get("app")) == 2
    assert len(result.get("db")) == 1


def test_get_key_fn_returns_callable():
    fn = get_key_fn("severity")
    assert callable(fn)
    assert fn(_entry("WARNING")) == "WARNING"


def test_get_key_fn_raises_on_unknown():
    with pytest.raises(KeyError, match="Unknown split key"):
        get_key_fn("nonexistent")


# ---------------------------------------------------------------------------
# report_split
# ---------------------------------------------------------------------------

def test_bucket_counts_sorted_by_key():
    entries = [_entry("INFO"), _entry("ERROR"), _entry("INFO")]
    result = split_entries(entries, key_by_severity)
    counts = bucket_counts(result)
    keys = [k for k, _ in counts]
    assert keys == sorted(keys)


def test_largest_bucket_returns_correct_key():
    entries = [_entry("INFO"), _entry("INFO"), _entry("ERROR")]
    result = split_entries(entries, key_by_severity)
    assert largest_bucket(result) == "INFO"


def test_largest_bucket_empty_returns_none():
    assert largest_bucket(SplitResult()) is None


def test_format_split_report_contains_title():
    result = split_entries([_entry("INFO")], key_by_severity)
    report = format_split_report(result, title="My Report")
    assert "My Report" in report


def test_format_split_report_contains_counts():
    entries = [_entry("ERROR")] * 3 + [_entry("INFO")] * 2
    result = split_entries(entries, key_by_severity)
    report = format_split_report(result)
    assert "3" in report
    assert "2" in report


def test_format_split_report_empty_input():
    report = format_split_report(SplitResult())
    assert "(no entries)" in report
