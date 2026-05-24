"""Tests for logslice.classify."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.classify import (
    ClassifiedEntry,
    ClassifyRule,
    category_counts,
    classify_entries,
    format_category_report,
    top_categories,
)
from logslice.parser import LogEntry


def _entry(message: str, severity: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"2024-01-01T12:00:00 {severity} {message}",
    )


# --- ClassifyRule ---

def test_classify_rule_matches_pattern():
    rule = ClassifyRule(category="db", pattern=r"database")
    assert rule.matches(_entry("database connection failed"))


def test_classify_rule_no_match_returns_false():
    rule = ClassifyRule(category="db", pattern=r"database")
    assert not rule.matches(_entry("network timeout"))


def test_classify_rule_ignore_case_default():
    rule = ClassifyRule(category="db", pattern=r"DATABASE")
    assert rule.matches(_entry("database error"))


def test_classify_rule_case_sensitive():
    rule = ClassifyRule(category="db", pattern=r"DATABASE", ignore_case=False)
    assert not rule.matches(_entry("database error"))
    assert rule.matches(_entry("DATABASE error"))


# --- classify_entries ---

def test_classify_entries_assigns_first_matching_rule():
    rules = [
        ClassifyRule(category="auth", pattern=r"login|logout"),
        ClassifyRule(category="db", pattern=r"database"),
    ]
    entries = [_entry("user login succeeded"), _entry("database timeout")]
    result = list(classify_entries(entries, rules))
    assert result[0].category == "auth"
    assert result[1].category == "db"


def test_classify_entries_uses_default_when_no_match():
    rules = [ClassifyRule(category="auth", pattern=r"login")]
    entries = [_entry("disk full")]
    result = list(classify_entries(entries, rules, default="other"))
    assert result[0].category == "other"


def test_classify_entries_empty_input_yields_nothing():
    rules = [ClassifyRule(category="auth", pattern=r"login")]
    result = list(classify_entries([], rules))
    assert result == []


def test_classify_entries_no_rules_all_default():
    entries = [_entry("hello"), _entry("world")]
    result = list(classify_entries(entries, [], default="uncategorized"))
    assert all(ce.category == "uncategorized" for ce in result)


# --- category_counts ---

def test_category_counts_correct():
    rules = [ClassifyRule(category="auth", pattern=r"login")]
    entries = [_entry("login ok"), _entry("login fail"), _entry("disk full")]
    classified = classify_entries(entries, rules, default="other")
    counts = category_counts(classified)
    assert counts["auth"] == 2
    assert counts["other"] == 1


def test_category_counts_empty_returns_empty_dict():
    assert category_counts([]) == {}


# --- top_categories ---

def test_top_categories_sorted_descending():
    counts = {"auth": 10, "db": 5, "network": 15}
    top = top_categories(counts, n=2)
    assert top[0] == ("network", 15)
    assert top[1] == ("auth", 10)


def test_top_categories_n_larger_than_available():
    counts = {"a": 1, "b": 2}
    top = top_categories(counts, n=10)
    assert len(top) == 2


# --- format_category_report ---

def test_format_category_report_contains_categories():
    counts = {"auth": 3, "db": 7}
    report = format_category_report(counts)
    assert "auth" in report
    assert "db" in report
    assert "7" in report


def test_format_category_report_empty():
    report = format_category_report({})
    assert "No entries" in report
