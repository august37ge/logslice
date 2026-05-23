"""Tests for logslice.redact."""

import pytest
from datetime import datetime, timezone

from logslice.parser import LogEntry
from logslice.redact import (
    RedactConfig,
    REDACT_PLACEHOLDER,
    redact_message,
    redact_entry,
    redact_entries,
)


def _entry(message: str) -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        severity="INFO",
        message=message,
        raw=f"2024-01-01T12:00:00Z INFO {message}",
    )


def test_redact_message_password():
    result = redact_message("user login password=secret123")
    assert "secret123" not in result
    assert REDACT_PLACEHOLDER in result


def test_redact_message_token():
    result = redact_message("auth token=abc.def.ghi")
    assert "abc.def.ghi" not in result
    assert REDACT_PLACEHOLDER in result


def test_redact_message_email():
    result = redact_message("user user@example.com logged in")
    assert "user@example.com" not in result
    assert REDACT_PLACEHOLDER in result


def test_redact_message_credit_card():
    result = redact_message("charged card 4111 1111 1111 1111 ok")
    assert "4111" not in result
    assert REDACT_PLACEHOLDER in result


def test_redact_message_no_sensitive_data():
    original = "Server started on port 8080"
    result = redact_message(original)
    assert result == original


def test_redact_message_custom_placeholder():
    config = RedactConfig(placeholder="***")
    result = redact_message("token=xyz", config)
    assert "***" in result
    assert REDACT_PLACEHOLDER not in result


def test_redact_message_custom_pattern():
    config = RedactConfig(patterns=[r"order_id=\d+"], use_defaults=False)
    result = redact_message("processed order_id=99887", config)
    assert "99887" not in result
    assert REDACT_PLACEHOLDER in result


def test_redact_message_no_defaults():
    config = RedactConfig(use_defaults=False)
    original = "password=should_stay"
    result = redact_message(original, config)
    assert result == original


def test_redact_message_invalid_pattern_raises():
    config = RedactConfig(patterns=[r"["], use_defaults=False)
    with pytest.raises(ValueError, match="Invalid redaction pattern"):
        redact_message("anything", config)


def test_redact_entry_returns_new_entry():
    entry = _entry("password=hunter2")
    result = redact_entry(entry)
    assert result is not entry
    assert "hunter2" not in result.message
    assert result.severity == entry.severity
    assert result.timestamp == entry.timestamp


def test_redact_entry_preserves_raw():
    entry = _entry("token=abc")
    result = redact_entry(entry)
    assert result.raw == entry.raw


def test_redact_entries_all_processed():
    entries = [
        _entry("password=one"),
        _entry("no sensitive data here"),
        _entry("secret=two"),
    ]
    results = redact_entries(entries)
    assert len(results) == 3
    assert "one" not in results[0].message
    assert results[1].message == "no sensitive data here"
    assert "two" not in results[2].message
