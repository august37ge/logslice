"""Tests for logslice.group."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.group import group_entries, group_counts, top_groups
from logslice.parser import LogEntry


def _entry(
    severity: str = "INFO",
    ts: datetime = None,
    source: str = "",
) -> LogEntry:
    if ts is None:
        ts = datetime(2024, 6, 15, 10, 30, tzinfo=timezone.utc)
    return LogEntry(
        timestamp=ts,
        severity=severity,
        message="msg",
        raw="raw",
        extra={"source": source} if source else {},
    )


# --- group_entries ---

def test_group_entries_by_severity():
    entries = [_entry("INFO"), _entry("ERROR"), _entry("INFO")]
    groups = group_entries(entries, by="severity")
    assert set(groups.keys()) == {"INFO", "ERROR"}
    assert len(groups["INFO"]) == 2
    assert len(groups["ERROR"]) == 1


def test_group_entries_by_date():
    entries = [
        _entry(ts=datetime(2024, 1, 1, tzinfo=timezone.utc)),
        _entry(ts=datetime(2024, 1, 1, tzinfo=timezone.utc)),
        _entry(ts=datetime(2024, 1, 2, tzinfo=timezone.utc)),
    ]
    groups = group_entries(entries, by="date")
    assert "2024-01-01" in groups
    assert "2024-01-02" in groups
    assert len(groups["2024-01-01"]) == 2


def test_group_entries_by_hour():
    entries = [
        _entry(ts=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)),
        _entry(ts=datetime(2024, 1, 1, 9, 45, tzinfo=timezone.utc)),
        _entry(ts=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)),
    ]
    groups = group_entries(entries, by="hour")
    assert len(groups["2024-01-01T09"]) == 2
    assert len(groups["2024-01-01T10"]) == 1


def test_group_entries_by_source():
    entries = [
        _entry(source="api"),
        _entry(source="worker"),
        _entry(source="api"),
    ]
    groups = group_entries(entries, by="source")
    assert len(groups["api"]) == 2
    assert len(groups["worker"]) == 1


def test_group_entries_unknown_source_key():
    entries = [_entry()]  # no source in extra
    groups = group_entries(entries, by="source")
    assert "unknown" in groups


def test_group_entries_invalid_key_raises():
    with pytest.raises(ValueError, match="Unknown group key"):
        group_entries([_entry()], by="bogus")  # type: ignore[arg-type]


# --- group_counts ---

def test_group_counts_returns_integers():
    entries = [_entry("DEBUG"), _entry("DEBUG"), _entry("INFO")]
    counts = group_counts(entries, by="severity")
    assert counts["DEBUG"] == 2
    assert counts["INFO"] == 1


def test_group_counts_empty_input():
    assert group_counts([], by="severity") == {}


# --- top_groups ---

def test_top_groups_returns_sorted_desc():
    entries = (
        [_entry("ERROR")] * 5
        + [_entry("INFO")] * 3
        + [_entry("DEBUG")] * 1
    )
    top = top_groups(entries, by="severity", n=2)
    assert top[0] == ("ERROR", 5)
    assert top[1] == ("INFO", 3)


def test_top_groups_n_larger_than_groups():
    entries = [_entry("INFO"), _entry("ERROR")]
    top = top_groups(entries, by="severity", n=10)
    assert len(top) == 2
