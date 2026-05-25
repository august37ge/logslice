"""Tests for logslice.fingerprint."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.fingerprint import (
    _normalise,
    fingerprint_message,
    fingerprint_entry,
    fingerprint_entries,
    group_by_fingerprint,
    format_fingerprint_report,
    FingerprintedEntry,
)

_TS = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(message: str, severity: str = "ERROR") -> LogEntry:
    return LogEntry(timestamp=_TS, severity=severity, message=message, raw="")


# --- _normalise ---

def test_normalise_strips_integers():
    assert "<X>" in _normalise("retried 3 times")


def test_normalise_strips_ipv4():
    assert "<X>" in _normalise("connected to 192.168.1.1")


def test_normalise_strips_hex():
    assert "<X>" in _normalise("id=deadbeef1234")


def test_normalise_lowercases():
    assert _normalise("HELLO") == "hello"


def test_normalise_collapses_whitespace():
    assert _normalise("a   b") == "a b"


# --- fingerprint_message ---

def test_fingerprint_message_returns_16_chars():
    fp = fingerprint_message("disk full")
    assert len(fp) == 16


def test_fingerprint_message_same_text_same_fp():
    assert fingerprint_message("disk full") == fingerprint_message("disk full")


def test_fingerprint_message_different_text_different_fp():
    assert fingerprint_message("disk full") != fingerprint_message("cpu high")


def test_fingerprint_message_dynamic_values_collapse():
    fp1 = fingerprint_message("retried 3 times")
    fp2 = fingerprint_message("retried 7 times")
    assert fp1 == fp2


# --- fingerprint_entry ---

def test_fingerprint_entry_includes_severity():
    e1 = _entry("disk full", severity="ERROR")
    e2 = _entry("disk full", severity="WARNING")
    assert fingerprint_entry(e1) != fingerprint_entry(e2)


def test_fingerprint_entry_stable():
    e = _entry("disk full")
    assert fingerprint_entry(e) == fingerprint_entry(e)


# --- fingerprint_entries ---

def test_fingerprint_entries_yields_fingerprintedentry():
    entries = [_entry("msg")]
    result = list(fingerprint_entries(entries))
    assert len(result) == 1
    assert isinstance(result[0], FingerprintedEntry)


def test_fingerprint_entries_fingerprint_matches_direct():
    e = _entry("disk full")
    result = list(fingerprint_entries([e]))
    assert result[0].fingerprint == fingerprint_entry(e)


# --- group_by_fingerprint ---

def test_group_by_fingerprint_same_message_same_group():
    entries = [_entry("disk full at /dev/sda1"), _entry("disk full at /dev/sdb2")]
    groups = group_by_fingerprint(entries)
    assert len(groups) == 1


def test_group_by_fingerprint_different_messages_different_groups():
    entries = [_entry("disk full"), _entry("cpu high")]
    groups = group_by_fingerprint(entries)
    assert len(groups) == 2


def test_group_by_fingerprint_empty_returns_empty():
    assert group_by_fingerprint([]) == {}


# --- format_fingerprint_report ---

def test_format_fingerprint_report_empty():
    assert format_fingerprint_report({}) == "No entries."


def test_format_fingerprint_report_contains_fingerprint():
    e = _entry("disk full")
    groups = group_by_fingerprint([e])
    report = format_fingerprint_report(groups)
    fp = fingerprint_entry(e)
    assert fp in report


def test_format_fingerprint_report_shows_count():
    entries = [_entry("disk full"), _entry("disk full")]
    groups = group_by_fingerprint(entries)
    report = format_fingerprint_report(groups)
    assert "2" in report
