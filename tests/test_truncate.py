"""Tests for logslice.truncate."""

import pytest
from datetime import datetime, timezone
from logslice.parser import LogEntry
from logslice.truncate import (
    truncate_message,
    truncate_entry,
    truncate_entries,
    DEFAULT_MAX_LENGTH,
)


def _entry(message: str, severity: str = "INFO") -> LogEntry:
    ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    raw = f"2024-01-01T12:00:00Z {severity} {message}"
    return LogEntry(timestamp=ts, severity=severity, message=message, raw=raw)


def test_truncate_message_short_string_unchanged():
    assert truncate_message("hello", max_length=20) == "hello"


def test_truncate_message_exact_length_unchanged():
    msg = "a" * 20
    assert truncate_message(msg, max_length=20) == msg


def test_truncate_message_long_string_truncated():
    msg = "a" * 50
    result = truncate_message(msg, max_length=10)
    assert len(result) == 10
    assert result.endswith("...")


def test_truncate_message_uses_default_max_length():
    msg = "x" * (DEFAULT_MAX_LENGTH + 50)
    result = truncate_message(msg)
    assert len(result) == DEFAULT_MAX_LENGTH
    assert result.endswith("...")


def test_truncate_message_raises_when_max_too_small():
    with pytest.raises(ValueError):
        truncate_message("hello", max_length=2)


def test_truncate_entry_returns_new_entry_with_truncated_message():
    entry = _entry("w" * 300)
    result = truncate_entry(entry, max_length=50)
    assert len(result.message) == 50
    assert result.message.endswith("...")
    assert result.timestamp == entry.timestamp
    assert result.severity == entry.severity
    assert result.raw == entry.raw


def test_truncate_entry_short_message_unchanged():
    entry = _entry("short message")
    result = truncate_entry(entry, max_length=100)
    assert result.message == "short message"


def test_truncate_entries_truncates_long_messages():
    entries = [_entry("a" * 300), _entry("b" * 300)]
    results = truncate_entries(entries, max_length=20)
    assert all(len(e.message) == 20 for e in results)


def test_truncate_entries_leaves_short_messages_untouched():
    entries = [_entry("short"), _entry("also short")]
    results = truncate_entries(entries, max_length=100)
    assert results[0].message == "short"
    assert results[1].message == "also short"


def test_truncate_entries_only_if_longer_skips_entries_below_threshold():
    short = _entry("hello")
    long_msg = _entry("z" * 300)
    results = truncate_entries(
        [short, long_msg], max_length=50, only_if_longer=100
    )
    assert results[0].message == "hello"
    assert len(results[1].message) == 50


def test_truncate_entries_empty_list():
    assert truncate_entries([]) == []
