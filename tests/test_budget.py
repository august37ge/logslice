"""Tests for logslice.budget."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.budget import (
    BudgetConfig,
    BudgetResult,
    apply_budget,
    format_budget_report,
    iter_budget,
    _window_start,
)
from logslice.parser import LogEntry


def _entry(ts: datetime, severity: str = "INFO", message: str = "msg") -> LogEntry:
    return LogEntry(timestamp=ts, severity=severity, message=message, raw=f"{ts} {severity} {message}")


def _dt(hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, second, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# _window_start
# ---------------------------------------------------------------------------

def test_window_start_on_boundary():
    ts = _dt(hour=2, minute=0)
    ws = _window_start(ts, window_minutes=60)
    assert ws.hour == 2 and ws.minute == 0


def test_window_start_mid_bucket():
    ts = _dt(hour=2, minute=35)
    ws = _window_start(ts, window_minutes=60)
    assert ws.hour == 2 and ws.minute == 0


def test_window_start_5min():
    ts = _dt(hour=1, minute=7)
    ws = _window_start(ts, window_minutes=5)
    assert ws.minute == 5


# ---------------------------------------------------------------------------
# apply_budget
# ---------------------------------------------------------------------------

def test_apply_budget_no_drops_within_limit():
    entries = [_entry(_dt(minute=i), "INFO") for i in range(5)]
    cfg = BudgetConfig(max_per_severity=10, window_minutes=60)
    result = apply_budget(entries, cfg)
    assert len(result.allowed) == 5
    assert result.dropped == 0


def test_apply_budget_drops_excess():
    entries = [_entry(_dt(minute=i), "DEBUG") for i in range(10)]
    cfg = BudgetConfig(max_per_severity=3, window_minutes=60)
    result = apply_budget(entries, cfg)
    assert len(result.allowed) == 3
    assert result.dropped == 7
    assert result.dropped_by_severity["DEBUG"] == 7


def test_apply_budget_separate_windows():
    # 3 entries in hour 0, 3 in hour 1 — limit 2 per window
    entries = (
        [_entry(_dt(hour=0, minute=i), "INFO") for i in range(3)]
        + [_entry(_dt(hour=1, minute=i), "INFO") for i in range(3)]
    )
    cfg = BudgetConfig(max_per_severity=2, window_minutes=60)
    result = apply_budget(entries, cfg)
    assert len(result.allowed) == 4  # 2 per window
    assert result.dropped == 2


def test_apply_budget_severity_override():
    entries = [_entry(_dt(minute=i), "ERROR") for i in range(10)]
    cfg = BudgetConfig(max_per_severity=2, window_minutes=60, overrides={"ERROR": 8})
    result = apply_budget(entries, cfg)
    assert len(result.allowed) == 8
    assert result.dropped == 2


def test_apply_budget_multiple_severities_independent():
    entries = (
        [_entry(_dt(minute=i), "INFO") for i in range(5)]
        + [_entry(_dt(minute=i), "ERROR") for i in range(5)]
    )
    cfg = BudgetConfig(max_per_severity=3, window_minutes=60)
    result = apply_budget(entries, cfg)
    assert len(result.allowed) == 6  # 3 INFO + 3 ERROR
    assert result.dropped_by_severity["INFO"] == 2
    assert result.dropped_by_severity["ERROR"] == 2


def test_apply_budget_default_config():
    entries = [_entry(_dt(minute=0), "INFO")]
    result = apply_budget(entries)
    assert len(result.allowed) == 1


# ---------------------------------------------------------------------------
# iter_budget
# ---------------------------------------------------------------------------

def test_iter_budget_yields_allowed_only():
    entries = [_entry(_dt(minute=i), "WARN") for i in range(6)]
    cfg = BudgetConfig(max_per_severity=4, window_minutes=60)
    allowed = list(iter_budget(entries, cfg))
    assert len(allowed) == 4


# ---------------------------------------------------------------------------
# format_budget_report
# ---------------------------------------------------------------------------

def test_format_budget_report_no_drops():
    result = BudgetResult(allowed=[_entry(_dt())], dropped=0)
    report = format_budget_report(result)
    assert "Allowed : 1" in report
    assert "Dropped : 0" in report


def test_format_budget_report_shows_severity_breakdown():
    from collections import defaultdict
    dropped = defaultdict(int, {"DEBUG": 5, "INFO": 2})
    result = BudgetResult(allowed=[], dropped=7, dropped_by_severity=dropped)
    report = format_budget_report(result)
    assert "DEBUG" in report
    assert "INFO" in report
    assert "5" in report
