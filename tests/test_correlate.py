"""Tests for logslice.correlate."""
from datetime import datetime, timezone
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.correlate import (
    CorrelatedGroup,
    correlate_entries,
    format_correlated_group,
)


def _entry(ts: datetime, severity: str, message: str) -> LogEntry:
    return LogEntry(timestamp=ts, severity=severity, message=message, raw=f"{ts} {severity} {message}")


def _dt(second: int) -> datetime:
    return datetime(2024, 1, 1, 12, 0, second, tzinfo=timezone.utc)


# --- CorrelatedGroup ---

def test_correlated_group_all_entries_includes_anchor_and_related():
    anchor = _entry(_dt(0), "ERROR", "main")
    rel = _entry(_dt(1), "WARN", "side")
    group = CorrelatedGroup(anchor=anchor, related=[rel])
    assert group.all_entries == [anchor, rel]


def test_correlated_group_max_severity_returns_highest():
    anchor = _entry(_dt(0), "INFO", "a")
    rel = _entry(_dt(1), "ERROR", "b")
    group = CorrelatedGroup(anchor=anchor, related=[rel])
    assert group.max_severity == "ERROR"


def test_correlated_group_max_severity_anchor_wins():
    anchor = _entry(_dt(0), "CRITICAL", "a")
    rel = _entry(_dt(1), "DEBUG", "b")
    group = CorrelatedGroup(anchor=anchor, related=[rel])
    assert group.max_severity == "CRITICAL"


# --- correlate_entries ---

def test_correlate_no_candidates_yields_empty_related():
    anchor = _entry(_dt(0), "ERROR", "oops")
    groups = list(correlate_entries([anchor], [], window_seconds=5))
    assert len(groups) == 1
    assert groups[0].related == []


def test_correlate_within_window_included():
    anchor = _entry(_dt(0), "ERROR", "main")
    near = _entry(_dt(3), "WARN", "near")
    far = _entry(_dt(10), "WARN", "far")
    groups = list(correlate_entries([anchor], [near, far], window_seconds=5))
    assert near in groups[0].related
    assert far not in groups[0].related


def test_correlate_exact_boundary_included():
    anchor = _entry(_dt(0), "ERROR", "main")
    boundary = _entry(_dt(5), "INFO", "boundary")
    groups = list(correlate_entries([anchor], [boundary], window_seconds=5))
    assert boundary in groups[0].related


def test_correlate_anchor_excluded_from_own_related():
    anchor = _entry(_dt(0), "ERROR", "self")
    groups = list(correlate_entries([anchor], [anchor], window_seconds=10))
    assert anchor not in groups[0].related


def test_correlate_min_severity_filters_low_entries():
    anchor = _entry(_dt(0), "ERROR", "main")
    low = _entry(_dt(1), "DEBUG", "noise")
    high = _entry(_dt(2), "ERROR", "important")
    groups = list(correlate_entries([anchor], [low, high], window_seconds=5, min_severity="ERROR"))
    assert low not in groups[0].related
    assert high in groups[0].related


def test_correlate_related_sorted_by_timestamp():
    anchor = _entry(_dt(0), "ERROR", "main")
    e1 = _entry(_dt(4), "WARN", "later")
    e2 = _entry(_dt(1), "INFO", "earlier")
    groups = list(correlate_entries([anchor], [e1, e2], window_seconds=5))
    assert groups[0].related == [e2, e1]


# --- format_correlated_group ---

def test_format_correlated_group_contains_anchor_message():
    anchor = _entry(_dt(0), "ERROR", "something broke")
    group = CorrelatedGroup(anchor=anchor)
    output = format_correlated_group(group)
    assert "something broke" in output


def test_format_correlated_group_related_indented():
    anchor = _entry(_dt(0), "ERROR", "main")
    rel = _entry(_dt(1), "WARN", "related event")
    group = CorrelatedGroup(anchor=anchor, related=[rel])
    output = format_correlated_group(group)
    lines = output.splitlines()
    assert lines[1].startswith("  ->")
    assert "related event" in lines[1]
