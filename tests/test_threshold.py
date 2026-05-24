"""Tests for logslice.threshold."""
from __future__ import annotations

import pytest

from logslice.alert import AlertRule
from logslice.threshold import (
    ThresholdConfigError,
    _validate_rule,
    load_rules,
    rules_to_dict,
)


# ---------------------------------------------------------------------------
# _validate_rule
# ---------------------------------------------------------------------------

def test_validate_rule_minimal_valid():
    raw = {"name": "r", "severity": "ERROR", "threshold": 5}
    rule = _validate_rule(raw, 0)
    assert rule.name == "r"
    assert rule.severity == "ERROR"
    assert rule.threshold == 5


def test_validate_rule_defaults_window():
    raw = {"name": "r", "severity": "INFO", "threshold": 1}
    rule = _validate_rule(raw, 0)
    assert rule.window_seconds == 60.0


def test_validate_rule_custom_window():
    raw = {"name": "r", "severity": "WARNING", "threshold": 2, "window_seconds": 120}
    rule = _validate_rule(raw, 0)
    assert rule.window_seconds == 120.0


def test_validate_rule_severity_case_insensitive():
    raw = {"name": "r", "severity": "warning", "threshold": 1}
    rule = _validate_rule(raw, 0)
    assert rule.severity == "WARNING"


def test_validate_rule_message_contains_set():
    raw = {"name": "r", "severity": "ERROR", "threshold": 1, "message_contains": "fail"}
    rule = _validate_rule(raw, 0)
    assert rule.message_contains == "fail"


def test_validate_rule_missing_name_raises():
    with pytest.raises(ThresholdConfigError, match="name"):
        _validate_rule({"severity": "ERROR", "threshold": 1}, 0)


def test_validate_rule_missing_severity_raises():
    with pytest.raises(ThresholdConfigError, match="severity"):
        _validate_rule({"name": "r", "threshold": 1}, 0)


def test_validate_rule_missing_threshold_raises():
    with pytest.raises(ThresholdConfigError, match="threshold"):
        _validate_rule({"name": "r", "severity": "ERROR"}, 0)


def test_validate_rule_unknown_severity_raises():
    with pytest.raises(ThresholdConfigError, match="unknown severity"):
        _validate_rule({"name": "r", "severity": "VERBOSE", "threshold": 1}, 0)


def test_validate_rule_zero_threshold_raises():
    with pytest.raises(ThresholdConfigError, match="threshold"):
        _validate_rule({"name": "r", "severity": "ERROR", "threshold": 0}, 0)


def test_validate_rule_negative_window_raises():
    raw = {"name": "r", "severity": "ERROR", "threshold": 1, "window_seconds": -5}
    with pytest.raises(ThresholdConfigError, match="window_seconds"):
        _validate_rule(raw, 0)


# ---------------------------------------------------------------------------
# load_rules
# ---------------------------------------------------------------------------

def test_load_rules_empty_list():
    assert load_rules({"rules": []}) == []


def test_load_rules_no_rules_key_returns_empty():
    assert load_rules({}) == []


def test_load_rules_parses_multiple_rules():
    data = {
        "rules": [
            {"name": "a", "severity": "ERROR", "threshold": 3},
            {"name": "b", "severity": "WARNING", "threshold": 10, "window_seconds": 30},
        ]
    }
    rules = load_rules(data)
    assert len(rules) == 2
    assert rules[0].name == "a"
    assert rules[1].window_seconds == 30.0


def test_load_rules_invalid_rules_not_list_raises():
    with pytest.raises(ThresholdConfigError, match="list"):
        load_rules({"rules": "not a list"})


# ---------------------------------------------------------------------------
# rules_to_dict
# ---------------------------------------------------------------------------

def test_rules_to_dict_round_trip():
    rules = [
        AlertRule(name="x", severity="CRITICAL", threshold=1, window_seconds=30.0)
    ]
    d = rules_to_dict(rules)
    reloaded = load_rules(d)
    assert reloaded[0].name == "x"
    assert reloaded[0].severity == "CRITICAL"


def test_rules_to_dict_omits_none_message_contains():
    rules = [AlertRule(name="r", severity="ERROR", threshold=2)]
    d = rules_to_dict(rules)
    assert "message_contains" not in d["rules"][0]


def test_rules_to_dict_includes_message_contains_when_set():
    rules = [AlertRule(name="r", severity="ERROR", threshold=2, message_contains="oops")]
    d = rules_to_dict(rules)
    assert d["rules"][0]["message_contains"] == "oops"
