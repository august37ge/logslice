"""Tests for logslice.dedup."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.dedup import _entry_key, deduplicate, count_duplicates


def _entry(severity: str = "INFO", message: str = "hello") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        severity=severity,
        message=message,
        raw=f"2024-01-01T12:00:00Z {severity} {message}",
    )


# ---------------------------------------------------------------------------
# _entry_key
# ---------------------------------------------------------------------------

def test_entry_key_same_content_same_key():
    assert _entry_key(_entry()) == _entry_key(_entry())


def test_entry_key_different_message_different_key():
    assert _entry_key(_entry(message="a")) != _entry_key(_entry(message="b"))


def test_entry_key_different_severity_different_key():
    assert _entry_key(_entry(severity="INFO")) != _entry_key(_entry(severity="ERROR"))


def test_entry_key_ignores_timestamp():
    e1 = LogEntry(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        severity="INFO",
        message="msg",
        raw="raw1",
    )
    e2 = LogEntry(
        timestamp=datetime(2024, 6, 1, tzinfo=timezone.utc),
        severity="INFO",
        message="msg",
        raw="raw2",
    )
    assert _entry_key(e1) == _entry_key(e2)


# ---------------------------------------------------------------------------
# deduplicate — global mode
# ---------------------------------------------------------------------------

def test_deduplicate_empty():
    assert list(deduplicate([])) == []


def test_deduplicate_no_duplicates_returns_all():
    entries = [_entry(message="a"), _entry(message="b"), _entry(message="c")]
    assert list(deduplicate(entries)) == entries


def test_deduplicate_removes_global_duplicates():
    a = _entry(message="a")
    b = _entry(message="b")
    entries = [a, b, _entry(message="a"), b]
    result = list(deduplicate(entries))
    assert result == [a, b]


# ---------------------------------------------------------------------------
# deduplicate — consecutive mode
# ---------------------------------------------------------------------------

def test_deduplicate_consecutive_keeps_non_adjacent_duplicates():
    a = _entry(message="a")
    b = _entry(message="b")
    entries = [a, b, _entry(message="a")]
    result = list(deduplicate(entries, consecutive_only=True))
    assert len(result) == 3


def test_deduplicate_consecutive_removes_adjacent_duplicates():
    a = _entry(message="a")
    entries = [a, _entry(message="a"), _entry(message="a"), _entry(message="b")]
    result = list(deduplicate(entries, consecutive_only=True))
    assert len(result) == 2
    assert result[0].message == "a"
    assert result[1].message == "b"


# ---------------------------------------------------------------------------
# count_duplicates
# ---------------------------------------------------------------------------

def test_count_duplicates_returns_correct_count():
    entries = [_entry(message="x"), _entry(message="x"), _entry(message="y")]
    unique, count = count_duplicates(entries)
    assert count == 1
    assert len(unique) == 2


def test_count_duplicates_zero_when_all_unique():
    entries = [_entry(message="a"), _entry(message="b")]
    _, count = count_duplicates(entries)
    assert count == 0
