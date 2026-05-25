"""Tests for logslice.flatten."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.flatten import FlatEntry, flatten, flatten_to_list, resequence


def _dt(hour: int = 0, minute: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, tzinfo=timezone.utc)


def _entry(msg: str, severity: str = "INFO") -> LogEntry:
    return LogEntry(timestamp=_dt(), severity=severity, message=msg, raw=msg)


# ---------------------------------------------------------------------------
# flatten
# ---------------------------------------------------------------------------

def test_flatten_single_stream_sequence_starts_at_one():
    entries = [_entry("a"), _entry("b"), _entry("c")]
    result = list(flatten([entries]))
    assert [fe.sequence for fe in result] == [1, 2, 3]


def test_flatten_two_streams_contiguous_sequence():
    s1 = [_entry("x"), _entry("y")]
    s2 = [_entry("p"), _entry("q")]
    result = list(flatten([s1, s2]))
    assert [fe.sequence for fe in result] == [1, 2, 3, 4]


def test_flatten_labels_assigned_correctly():
    s1 = [_entry("a")]
    s2 = [_entry("b")]
    result = list(flatten([s1, s2], labels=["app.log", "error.log"]))
    assert result[0].source == "app.log"
    assert result[1].source == "error.log"


def test_flatten_missing_label_defaults_to_empty_string():
    s1 = [_entry("a")]
    s2 = [_entry("b")]
    result = list(flatten([s1, s2], labels=["only-one"]))
    assert result[0].source == "only-one"
    assert result[1].source == ""


def test_flatten_no_labels_all_sources_empty():
    entries = [_entry("a"), _entry("b")]
    result = list(flatten([entries]))
    assert all(fe.source == "" for fe in result)


def test_flatten_custom_start_sequence():
    entries = [_entry("a"), _entry("b")]
    result = list(flatten([entries], start=10))
    assert result[0].sequence == 10
    assert result[1].sequence == 11


def test_flatten_empty_streams_yields_nothing():
    result = list(flatten([[], []]))
    assert result == []


def test_flatten_preserves_entry_fields():
    e = _entry("hello world", severity="ERROR")
    result = list(flatten([[e]]))
    assert result[0].message == "hello world"
    assert result[0].severity == "ERROR"


# ---------------------------------------------------------------------------
# flatten_to_list
# ---------------------------------------------------------------------------

def test_flatten_to_list_returns_list():
    entries = [_entry("a")]
    result = flatten_to_list([entries])
    assert isinstance(result, list)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# resequence
# ---------------------------------------------------------------------------

def test_resequence_fills_gaps():
    fe1 = FlatEntry(entry=_entry("a"), sequence=1, source="s")
    fe2 = FlatEntry(entry=_entry("b"), sequence=5, source="s")
    fe3 = FlatEntry(entry=_entry("c"), sequence=99, source="s")
    result = list(resequence([fe1, fe2, fe3]))
    assert [fe.sequence for fe in result] == [1, 2, 3]


def test_resequence_preserves_source_and_entry():
    fe = FlatEntry(entry=_entry("msg"), sequence=42, source="origin")
    result = list(resequence([fe]))
    assert result[0].source == "origin"
    assert result[0].message == "msg"


def test_resequence_custom_start():
    fes = [FlatEntry(entry=_entry("x"), sequence=i, source="") for i in range(3)]
    result = list(resequence(fes, start=100))
    assert result[0].sequence == 100
    assert result[-1].sequence == 102
