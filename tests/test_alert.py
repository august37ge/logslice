"""Tests for logslice.alert."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.alert import (
    AlertRule,
    AlertEvent,
    _entry_matches_rule,
    evaluate_rule,
    evaluate_rules,
)


def _entry(ts_offset: float, severity: str = "ERROR", message: str = "boom") -> LogEntry:
    """Create a LogEntry with timestamp = epoch + ts_offset seconds."""
    ts = datetime.fromtimestamp(ts_offset, tz=timezone.utc)
    return LogEntry(timestamp=ts, severity=severity, message=message, raw=f"{ts} {severity} {message}")


# ---------------------------------------------------------------------------
# _entry_matches_rule
# ---------------------------------------------------------------------------

def test_entry_matches_rule_exact_severity():
    rule = AlertRule(name="r", severity="ERROR", threshold=1)
    assert _entry_matches_rule(_entry(0, "ERROR"), rule) is True


def test_entry_matches_rule_higher_severity():
    rule = AlertRule(name="r", severity="WARNING", threshold=1)
    assert _entry_matches_rule(_entry(0, "ERROR"), rule) is True


def test_entry_matches_rule_lower_severity_excluded():
    rule = AlertRule(name="r", severity="ERROR", threshold=1)
    assert _entry_matches_rule(_entry(0, "INFO"), rule) is False


def test_entry_matches_rule_message_filter_pass():
    rule = AlertRule(name="r", severity="ERROR", threshold=1, message_contains="boom")
    assert _entry_matches_rule(_entry(0, "ERROR", "big boom here"), rule) is True


def test_entry_matches_rule_message_filter_fail():
    rule = AlertRule(name="r", severity="ERROR", threshold=1, message_contains="crash")
    assert _entry_matches_rule(_entry(0, "ERROR", "big boom here"), rule) is False


# ---------------------------------------------------------------------------
# evaluate_rule
# ---------------------------------------------------------------------------

def test_evaluate_rule_no_trigger_below_threshold():
    rule = AlertRule(name="r", severity="ERROR", threshold=3, window_seconds=60)
    entries = [_entry(i, "ERROR") for i in range(2)]
    assert evaluate_rule(iter(entries), rule) is None


def test_evaluate_rule_triggers_at_threshold():
    rule = AlertRule(name="r", severity="ERROR", threshold=3, window_seconds=60)
    entries = [_entry(i, "ERROR") for i in range(3)]
    event = evaluate_rule(iter(entries), rule)
    assert event is not None
    assert event.rule_name == "r"
    assert event.count >= 3


def test_evaluate_rule_returns_alert_event_type():
    rule = AlertRule(name="burst", severity="ERROR", threshold=2, window_seconds=60)
    entries = [_entry(i, "ERROR") for i in range(5)]
    event = evaluate_rule(iter(entries), rule)
    assert isinstance(event, AlertEvent)


def test_evaluate_rule_window_evicts_old_entries():
    rule = AlertRule(name="r", severity="ERROR", threshold=3, window_seconds=10)
    # First two entries are far apart; third is within window of second only
    entries = [_entry(0, "ERROR"), _entry(50, "ERROR"), _entry(55, "ERROR")]
    # Only 2 entries fall within any 10-second window => should NOT trigger
    assert evaluate_rule(iter(entries), rule) is None


def test_evaluate_rule_skips_non_matching_severity():
    rule = AlertRule(name="r", severity="ERROR", threshold=2, window_seconds=60)
    entries = [_entry(i, "INFO") for i in range(10)]
    assert evaluate_rule(iter(entries), rule) is None


def test_evaluate_rule_empty_entries_returns_none():
    rule = AlertRule(name="r", severity="ERROR", threshold=1, window_seconds=60)
    assert evaluate_rule(iter([]), rule) is None


# ---------------------------------------------------------------------------
# evaluate_rules
# ---------------------------------------------------------------------------

def test_evaluate_rules_returns_list():
    rules = [AlertRule(name="r", severity="ERROR", threshold=1, window_seconds=60)]
    entries = [_entry(0, "ERROR")]
    result = evaluate_rules(entries, rules)
    assert isinstance(result, list)


def test_evaluate_rules_multiple_rules_independent():
    rules = [
        AlertRule(name="errors", severity="ERROR", threshold=2, window_seconds=60),
        AlertRule(name="warnings", severity="WARNING", threshold=5, window_seconds=60),
    ]
    entries = [_entry(i, "ERROR") for i in range(3)]
    events = evaluate_rules(entries, rules)
    names = [e.rule_name for e in events]
    assert "errors" in names
    assert "warnings" not in names


def test_alert_event_str_contains_rule_name():
    event = AlertEvent(rule_name="my_rule", count=5, threshold=3, window_seconds=60.0)
    assert "my_rule" in str(event)
