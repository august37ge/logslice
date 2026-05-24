"""Tests for logslice.report_rate."""
from __future__ import annotations

from datetime import datetime, timezone

from logslice.parser import LogEntry
from logslice.report_rate import RateReport, compute_rate_report, format_rate_report


def _entry(severity: str = "INFO", message: str = "msg") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        severity=severity,
        message=message,
        raw=f"2024-01-01 {severity} {message}",
    )


def test_compute_rate_report_no_drops():
    entries = [_entry() for _ in range(3)]
    report = compute_rate_report(entries, entries)
    assert report.total_in == 3
    assert report.total_out == 3
    assert report.dropped == 0
    assert report.drop_rate == 0.0


def test_compute_rate_report_some_drops():
    orig = [_entry("ERROR"), _entry("INFO"), _entry("WARN")]
    kept = orig[:2]
    report = compute_rate_report(orig, kept)
    assert report.total_in == 3
    assert report.total_out == 2
    assert report.dropped == 1


def test_compute_rate_report_drop_rate_fraction():
    orig = [_entry() for _ in range(4)]
    kept = orig[:1]
    report = compute_rate_report(orig, kept)
    assert abs(report.drop_rate - 0.75) < 1e-9


def test_compute_rate_report_severity_dropped_counts():
    e_err = _entry("ERROR")
    e_info = _entry("INFO")
    orig = [e_err, e_info]
    report = compute_rate_report(orig, [e_info])
    assert report.severity_dropped == {"ERROR": 1}


def test_compute_rate_report_empty_input():
    report = compute_rate_report([], [])
    assert report.total_in == 0
    assert report.total_out == 0
    assert report.drop_rate == 0.0


def test_format_rate_report_contains_counts():
    report = RateReport(
        total_in=10,
        total_out=7,
        dropped=3,
        drop_rate=0.3,
        severity_dropped={"ERROR": 2, "WARN": 1},
    )
    text = format_rate_report(report)
    assert "10" in text
    assert "7" in text
    assert "3" in text
    assert "30.0%" in text


def test_format_rate_report_shows_severity_breakdown():
    report = RateReport(
        total_in=5,
        total_out=3,
        dropped=2,
        drop_rate=0.4,
        severity_dropped={"CRITICAL": 2},
    )
    text = format_rate_report(report)
    assert "CRITICAL" in text
    assert "2" in text


def test_format_rate_report_no_severity_section_when_none_dropped():
    report = RateReport(
        total_in=3,
        total_out=3,
        dropped=0,
        drop_rate=0.0,
        severity_dropped={},
    )
    text = format_rate_report(report)
    assert "severity" not in text.lower()
