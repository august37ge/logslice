"""Tests for logslice.pattern."""
from __future__ import annotations

from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.pattern import (
    PatternFrequency,
    count_patterns,
    format_pattern_report,
    message_pattern,
)


def _entry(message: str, severity: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"2024-01-01T12:00:00 {severity} {message}",
    )


# ---------------------------------------------------------------------------
# message_pattern
# ---------------------------------------------------------------------------

def test_message_pattern_replaces_integers():
    assert message_pattern("retried 3 times") == "retried <NUM> times"


def test_message_pattern_replaces_ipv4():
    assert message_pattern("connected to 192.168.1.1") == "connected to <IP>"


def test_message_pattern_replaces_hex():
    assert message_pattern("id=deadbeef00") == "id=<HEX>"


def test_message_pattern_replaces_quoted_strings():
    assert message_pattern('user "alice" logged in') == 'user <STR> logged in'


def test_message_pattern_collapses_whitespace():
    assert message_pattern("too   many   spaces") == "too many spaces"


def test_message_pattern_same_for_similar_messages():
    p1 = message_pattern("request took 120ms")
    p2 = message_pattern("request took 340ms")
    assert p1 == p2


def test_message_pattern_empty_string():
    assert message_pattern("") == ""


# ---------------------------------------------------------------------------
# count_patterns
# ---------------------------------------------------------------------------

def test_count_patterns_empty_returns_empty_list():
    assert count_patterns([]) == []


def test_count_patterns_single_entry():
    results = count_patterns([_entry("disk usage at 80%")])
    assert len(results) == 1
    assert results[0].count == 1


def test_count_patterns_groups_similar_messages():
    entries = [
        _entry("retried 1 times"),
        _entry("retried 2 times"),
        _entry("retried 5 times"),
    ]
    results = count_patterns(entries)
    assert len(results) == 1
    assert results[0].count == 3


def test_count_patterns_sorted_by_count_desc():
    entries = [
        _entry("foo bar"),
        _entry("retried 1 times"),
        _entry("retried 2 times"),
    ]
    results = count_patterns(entries)
    assert results[0].count >= results[-1].count


def test_count_patterns_example_preserved():
    original = "retried 99 times"
    results = count_patterns([_entry(original)])
    assert results[0].example == original


def test_count_patterns_severity_counts():
    entries = [
        _entry("disk full", severity="ERROR"),
        _entry("disk full", severity="WARNING"),
        _entry("disk full", severity="ERROR"),
    ]
    results = count_patterns(entries)
    assert results[0].severities["ERROR"] == 2
    assert results[0].severities["WARNING"] == 1


# ---------------------------------------------------------------------------
# format_pattern_report
# ---------------------------------------------------------------------------

def test_format_pattern_report_contains_header():
    report = format_pattern_report([])
    assert "Pattern Frequency Report" in report


def test_format_pattern_report_empty_note():
    report = format_pattern_report([])
    assert "no entries" in report


def test_format_pattern_report_shows_count():
    entries = [_entry("disk usage at 80%"), _entry("disk usage at 90%")]
    freqs = count_patterns(entries)
    report = format_pattern_report(freqs)
    assert "2" in report


def test_format_pattern_report_respects_top_limit():
    entries = [_entry(f"message number {i}") for i in range(20)]
    freqs = count_patterns(entries)
    report = format_pattern_report(freqs, top=3)
    # Only 3 numbered items should appear
    assert report.count("1.") == 1
    assert "4." not in report
