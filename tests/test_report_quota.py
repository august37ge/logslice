"""Tests for logslice.report_quota."""
from __future__ import annotations

from logslice.quota import QuotaResult
from logslice.report_quota import (
    format_quota_report,
    drop_rate,
    quota_summary,
)


def _result(
    emitted: int = 10,
    dropped: int = 5,
    by_sev: dict | None = None,
    by_src: dict | None = None,
) -> QuotaResult:
    r = QuotaResult(emitted=emitted, dropped=dropped)
    r.dropped_by_severity = by_sev or {}
    r.dropped_by_source = by_src or {}
    return r


# --- drop_rate ---

def test_drop_rate_zero_when_nothing_dropped():
    assert drop_rate(_result(emitted=10, dropped=0)) == 0.0


def test_drop_rate_one_when_all_dropped():
    assert drop_rate(_result(emitted=0, dropped=5)) == 1.0


def test_drop_rate_fraction():
    rate = drop_rate(_result(emitted=3, dropped=1))
    assert abs(rate - 0.25) < 1e-9


def test_drop_rate_empty_is_zero():
    assert drop_rate(_result(emitted=0, dropped=0)) == 0.0


# --- format_quota_report ---

def test_format_quota_report_contains_emitted_dropped():
    report = format_quota_report(_result(emitted=7, dropped=3))
    assert "7" in report
    assert "3" in report


def test_format_quota_report_custom_title():
    report = format_quota_report(_result(), title="My Quota")
    assert "My Quota" in report


def test_format_quota_report_severity_section_present():
    r = _result(by_sev={"ERROR": 2, "WARN": 1})
    report = format_quota_report(r)
    assert "ERROR" in report
    assert "WARN" in report


def test_format_quota_report_source_section_present():
    r = _result(by_src={"db": 4})
    report = format_quota_report(r)
    assert "db" in report


def test_format_quota_report_no_sections_when_empty_dicts():
    report = format_quota_report(_result(by_sev={}, by_src={}))
    assert "Dropped by severity" not in report
    assert "Dropped by source" not in report


def test_format_quota_report_unknown_source_label():
    r = _result(by_src={"": 2})
    report = format_quota_report(r)
    assert "<unknown>" in report


# --- quota_summary ---

def test_quota_summary_keys_present():
    summary = quota_summary(_result(emitted=8, dropped=2))
    assert set(summary.keys()) == {
        "emitted", "dropped", "drop_rate",
        "dropped_by_severity", "dropped_by_source",
    }


def test_quota_summary_drop_rate_rounded():
    r = _result(emitted=3, dropped=1)
    summary = quota_summary(r)
    assert summary["drop_rate"] == 0.25


def test_quota_summary_dicts_are_plain_dicts():
    r = _result(by_sev={"INFO": 1}, by_src={"api": 2})
    summary = quota_summary(r)
    assert isinstance(summary["dropped_by_severity"], dict)
    assert isinstance(summary["dropped_by_source"], dict)
