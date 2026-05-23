"""Tests for logslice.normalize."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.normalize import (
    normalize_entries,
    normalize_entry,
    normalize_message,
    normalize_severity,
)
from logslice.parser import LogEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(severity: str, message: str) -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        severity=severity,
        message=message,
        raw=f"2024-01-01T12:00:00Z [{severity}] {message}",
    )


# ---------------------------------------------------------------------------
# normalize_severity
# ---------------------------------------------------------------------------

def test_normalize_severity_warn_to_warning():
    assert normalize_severity("warn") == "WARNING"


def test_normalize_severity_err_to_error():
    assert normalize_severity("err") == "ERROR"


def test_normalize_severity_fatal_to_critical():
    assert normalize_severity("fatal") == "CRITICAL"


def test_normalize_severity_trace_to_debug():
    assert normalize_severity("trace") == "DEBUG"


def test_normalize_severity_already_canonical_info():
    assert normalize_severity("INFO") == "INFO"


def test_normalize_severity_unknown_returns_uppercased():
    assert normalize_severity("verbose") == "VERBOSE"


def test_normalize_severity_strips_whitespace():
    assert normalize_severity("  warn  ") == "WARNING"


# ---------------------------------------------------------------------------
# normalize_message
# ---------------------------------------------------------------------------

def test_normalize_message_strips_leading_trailing():
    assert normalize_message("  hello world  ") == "hello world"


def test_normalize_message_collapses_internal_spaces():
    assert normalize_message("too   many   spaces") == "too many spaces"


def test_normalize_message_empty_string():
    assert normalize_message("") == ""


def test_normalize_message_already_clean():
    assert normalize_message("clean message") == "clean message"


# ---------------------------------------------------------------------------
# normalize_entry
# ---------------------------------------------------------------------------

def test_normalize_entry_severity_is_normalized():
    entry = _entry("warn", "something happened")
    result = normalize_entry(entry)
    assert result.severity == "WARNING"


def test_normalize_entry_message_is_cleaned():
    entry = _entry("INFO", "  lots   of   spaces  ")
    result = normalize_entry(entry)
    assert result.message == "lots of spaces"


def test_normalize_entry_preserves_timestamp():
    entry = _entry("debug", "msg")
    result = normalize_entry(entry)
    assert result.timestamp == entry.timestamp


def test_normalize_entry_preserves_raw():
    entry = _entry("debug", "msg")
    result = normalize_entry(entry)
    assert result.raw == entry.raw


# ---------------------------------------------------------------------------
# normalize_entries
# ---------------------------------------------------------------------------

def test_normalize_entries_yields_all():
    entries = [_entry("warn", "a"), _entry("err", "b"), _entry("info", "c")]
    results = list(normalize_entries(entries))
    assert len(results) == 3


def test_normalize_entries_all_severities_normalized():
    entries = [_entry("warn", "x"), _entry("err", "y")]
    results = list(normalize_entries(entries))
    assert results[0].severity == "WARNING"
    assert results[1].severity == "ERROR"


def test_normalize_entries_empty_input():
    assert list(normalize_entries([])) == []
