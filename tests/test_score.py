"""Tests for logslice.score."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from logslice.parser import LogEntry
from logslice.score import (
    ScoredEntry,
    _keyword_score,
    _recency_score,
    _severity_score,
    format_scored,
    score_entries,
    score_entry,
)

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(
    severity: str = "INFO",
    message: str = "hello",
    ts: datetime | None = None,
) -> LogEntry:
    if ts is None:
        ts = _NOW
    return LogEntry(timestamp=ts, severity=severity, message=message, raw=f"{ts} [{severity}] {message}")


# --- _severity_score ---

def test_severity_score_critical_highest():
    score, reason = _severity_score(_entry("CRITICAL"))
    assert score == 8.0
    assert "CRITICAL" in reason


def test_severity_score_debug_lowest():
    score, _ = _severity_score(_entry("DEBUG"))
    assert score == 1.0


def test_severity_score_unknown_defaults_to_one():
    score, _ = _severity_score(_entry("TRACE"))
    assert score == 1.0


# --- _recency_score ---

def test_recency_score_fresh_entry_near_one():
    score, _ = _recency_score(_entry(ts=_NOW), now=_NOW)
    assert score == 1.0


def test_recency_score_old_entry_lower():
    old_ts = _NOW - timedelta(hours=48)
    score, _ = _recency_score(_entry(ts=old_ts), now=_NOW, half_life_hours=24.0)
    assert score < 0.5


def test_recency_score_naive_timestamp_treated_as_utc():
    naive_ts = _NOW.replace(tzinfo=None)
    score, _ = _recency_score(_entry(ts=naive_ts), now=_NOW)
    assert score == 1.0


# --- _keyword_score ---

def test_keyword_score_no_keywords_zero():
    score, reason = _keyword_score(_entry(message="disk full"), [])
    assert score == 0.0


def test_keyword_score_single_match():
    score, _ = _keyword_score(_entry(message="disk full"), ["disk"])
    assert score == 1.0


def test_keyword_score_multiple_matches():
    score, _ = _keyword_score(_entry(message="disk full error"), ["disk", "error"])
    assert score == 2.0


def test_keyword_score_case_insensitive():
    score, _ = _keyword_score(_entry(message="DISK FULL"), ["disk"])
    assert score == 1.0


# --- score_entry ---

def test_score_entry_returns_scored_entry():
    result = score_entry(_entry(), now=_NOW)
    assert isinstance(result, ScoredEntry)


def test_score_entry_higher_severity_higher_score():
    low = score_entry(_entry("DEBUG"), now=_NOW)
    high = score_entry(_entry("CRITICAL"), now=_NOW)
    assert high.score > low.score


def test_score_entry_reasons_has_three_items():
    result = score_entry(_entry(), now=_NOW)
    assert len(result.reasons) == 3


# --- score_entries ---

def test_score_entries_sorted_descending():
    entries = [_entry("DEBUG"), _entry("CRITICAL"), _entry("INFO")]
    scored = score_entries(entries, now=_NOW)
    scores = [s.score for s in scored]
    assert scores == sorted(scores, reverse=True)


def test_score_entries_empty_returns_empty():
    assert score_entries([], now=_NOW) == []


# --- format_scored ---

def test_format_scored_contains_score():
    s = score_entry(_entry("ERROR", message="boom"), now=_NOW)
    line = format_scored(s)
    assert str(s.score) in line or f"{s.score:.3f}" in line


def test_format_scored_contains_message():
    s = score_entry(_entry(message="unique-msg-xyz"), now=_NOW)
    assert "unique-msg-xyz" in format_scored(s)
