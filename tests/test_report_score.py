"""Tests for logslice.report_score."""

from __future__ import annotations

from datetime import datetime, timezone

from logslice.parser import LogEntry
from logslice.score import score_entries, score_entry
from logslice.report_score import (
    average_score,
    format_score_report,
    score_distribution,
    top_n,
)

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(severity: str = "INFO", message: str = "msg") -> LogEntry:
    return LogEntry(
        timestamp=_NOW,
        severity=severity,
        message=message,
        raw=f"{_NOW} [{severity}] {message}",
    )


def _scored(severities):
    entries = [_entry(s) for s in severities]
    return score_entries(entries, now=_NOW)


# --- top_n ---

def test_top_n_returns_first_n():
    scored = _scored(["CRITICAL", "ERROR", "INFO", "DEBUG"])
    result = top_n(scored, 2)
    assert len(result) == 2


def test_top_n_larger_than_list_returns_all():
    scored = _scored(["INFO"])
    assert len(top_n(scored, 100)) == 1


def test_top_n_empty_returns_empty():
    assert top_n([], 5) == []


# --- score_distribution ---

def test_score_distribution_empty_returns_empty():
    assert score_distribution([]) == {}


def test_score_distribution_returns_buckets():
    scored = _scored(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    dist = score_distribution(scored, buckets=3)
    assert isinstance(dist, dict)
    assert len(dist) == 3


def test_score_distribution_all_same_score():
    scored = _scored(["INFO", "INFO", "INFO"])
    dist = score_distribution(scored, buckets=5)
    assert sum(dist.values()) == 3


def test_score_distribution_counts_sum_to_total():
    scored = _scored(["DEBUG", "INFO", "ERROR"])
    dist = score_distribution(scored, buckets=5)
    assert sum(dist.values()) == len(scored)


# --- average_score ---

def test_average_score_empty_is_zero():
    assert average_score([]) == 0.0


def test_average_score_single_entry():
    s = score_entry(_entry("INFO"), now=_NOW)
    assert average_score([s]) == s.score


def test_average_score_multiple():
    scored = _scored(["DEBUG", "CRITICAL"])
    avg = average_score(scored)
    assert avg > 0.0
    assert avg == round(sum(s.score for s in scored) / len(scored), 4)


# --- format_score_report ---

def test_format_score_report_contains_header():
    scored = _scored(["ERROR", "INFO"])
    report = format_score_report(scored, top=5)
    assert "Score Report" in report


def test_format_score_report_contains_distribution_section():
    scored = _scored(["ERROR", "INFO"])
    report = format_score_report(scored)
    assert "distribution" in report.lower()


def test_format_score_report_empty_input():
    report = format_score_report([], top=5)
    assert "0 entries" in report or "top 5" in report.lower()
