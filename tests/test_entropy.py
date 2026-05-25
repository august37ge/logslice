"""Tests for logslice.entropy."""
from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.entropy import (
    _shannon_entropy,
    anomalous_entries,
    format_entropy_report,
    mark_anomalies,
    score_entries,
    EntropyResult,
)


def _entry(msg: str, severity: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        severity=severity,
        message=msg,
        raw=f"2024-01-01T12:00:00Z {severity} {msg}",
    )


# --- _shannon_entropy ---

def test_shannon_entropy_empty_string_is_zero():
    assert _shannon_entropy("") == 0.0


def test_shannon_entropy_single_char_is_zero():
    assert _shannon_entropy("aaaa") == 0.0


def test_shannon_entropy_two_equal_symbols():
    # "ab" repeated — 1 bit
    result = _shannon_entropy("abababab")
    assert abs(result - 1.0) < 1e-9


def test_shannon_entropy_increases_with_variety():
    low = _shannon_entropy("aaabbbccc")
    high = _shannon_entropy("abcdefghijklmnopqrstuvwxyz")
    assert high > low


# --- score_entries ---

def test_score_entries_returns_one_result_per_entry():
    entries = [_entry("hello world"), _entry("foo bar baz")]
    results = score_entries(entries)
    assert len(results) == 2


def test_score_entries_anomaly_flag_false_by_default():
    results = score_entries([_entry("test message")])
    assert all(not r.is_anomaly for r in results)


def test_score_entries_entropy_non_negative():
    results = score_entries([_entry("some log line with content")])
    assert all(r.entropy >= 0.0 for r in results)


# --- mark_anomalies ---

def test_mark_anomalies_explicit_threshold():
    entries = [_entry("aaa"), _entry("abcdefghijklmnopqrstuvwxyz0123456789!@#")]
    results = score_entries(entries)
    mark_anomalies(results, threshold=2.5)
    anomalies = [r for r in results if r.is_anomaly]
    assert len(anomalies) == 1
    assert anomalies[0].entry.message.startswith("abcdefg")


def test_mark_anomalies_auto_threshold_marks_outlier():
    normal = [_entry("aaa"), _entry("bbb"), _entry("ccc")]
    outlier = _entry("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()")
    results = score_entries(normal + [outlier])
    mark_anomalies(results, z_score_cutoff=1.0)
    assert results[-1].is_anomaly


def test_mark_anomalies_empty_returns_empty():
    assert mark_anomalies([]) == []


# --- anomalous_entries ---

def test_anomalous_entries_yields_only_anomalies():
    entries = [
        _entry("aaa"),
        _entry("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()"),
    ]
    found = list(anomalous_entries(entries, z_score_cutoff=0.5))
    assert all(r.is_anomaly for r in found)


def test_anomalous_entries_empty_input_yields_nothing():
    assert list(anomalous_entries([])) == []


# --- format_entropy_report ---

def test_format_entropy_report_contains_counts():
    entries = [_entry("aaa"), _entry("abcdefghijklmnopqrstuvwxyz")]
    results = score_entries(entries)
    mark_anomalies(results, threshold=2.0)
    report = format_entropy_report(results)
    assert "Entries analysed" in report
    assert "Anomalies found" in report


def test_format_entropy_report_lists_anomalous_messages():
    msg = "abcdefghijklmnopqrstuvwxyz0123456789"
    entries = [_entry("aaa"), _entry(msg)]
    results = score_entries(entries)
    mark_anomalies(results, threshold=1.0)
    report = format_entropy_report(results)
    assert msg[:40] in report
