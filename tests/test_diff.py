"""Tests for logslice.diff."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.diff import (
    DiffEntry,
    _entry_key,
    diff_entries,
    iter_diff,
    format_diff,
)


def _entry(msg: str, severity: str = "INFO", ts: str = "2024-01-01T00:00:00Z") -> LogEntry:
    return LogEntry(
        timestamp=datetime.fromisoformat(ts.replace("Z", "+00:00")),
        severity=severity,
        message=msg,
        raw=f"{ts} [{severity}] {msg}",
    )


def test_entry_key_uses_severity_and_message():
    e = _entry("hello", "ERROR")
    assert _entry_key(e) == ("ERROR", "hello")


def test_entry_key_strips_message_whitespace():
    e = _entry("  hello  ", "INFO")
    assert _entry_key(e) == ("INFO", "hello")


def test_diff_entries_all_same_marked_equal():
    entries = [_entry("msg1"), _entry("msg2")]
    result = diff_entries(entries, entries)
    assert all(d.tag == '=' for d in result)


def test_diff_entries_removed_when_only_in_left():
    left = [_entry("only-left")]
    right: List[LogEntry] = []
    result = diff_entries(left, right)
    assert len(result) == 1
    assert result[0].tag == '-'
    assert result[0].entry.message == "only-left"


def test_diff_entries_added_when_only_in_right():
    left: List[LogEntry] = []
    right = [_entry("only-right")]
    result = diff_entries(left, right)
    assert len(result) == 1
    assert result[0].tag == '+'
    assert result[0].entry.message == "only-right"


def test_diff_entries_mixed():
    left = [_entry("common"), _entry("removed")]
    right = [_entry("common"), _entry("added")]
    result = diff_entries(left, right)
    tags = {d.entry.message: d.tag for d in result}
    assert tags["common"] == '='
    assert tags["removed"] == '-'
    assert tags["added"] == '+'


def test_diff_entries_severity_distinguishes_entries():
    left = [_entry("msg", "INFO")]
    right = [_entry("msg", "ERROR")]
    result = diff_entries(left, right)
    tags = {(d.entry.severity, d.entry.message): d.tag for d in result}
    assert tags[("INFO", "msg")] == '-'
    assert tags[("ERROR", "msg")] == '+'


def test_iter_diff_yields_same_as_diff_entries():
    left = [_entry("a"), _entry("b")]
    right = [_entry("b"), _entry("c")]
    assert list(iter_diff(left, right)) == diff_entries(left, right)


def test_format_diff_prefix_plus():
    d = DiffEntry(tag='+', entry=_entry("new line"))
    lines = format_diff([d])
    assert lines[0].startswith('+ ')
    assert 'new line' in lines[0]


def test_format_diff_prefix_minus():
    d = DiffEntry(tag='-', entry=_entry("old line"))
    lines = format_diff([d])
    assert lines[0].startswith('- ')


def test_format_diff_prefix_equal():
    d = DiffEntry(tag='=', entry=_entry("same"))
    lines = format_diff([d])
    assert lines[0].startswith('  ')


def test_format_diff_contains_severity_and_message():
    d = DiffEntry(tag='+', entry=_entry("check", "WARNING"))
    lines = format_diff([d])
    assert '[WARNING]' in lines[0]
    assert 'check' in lines[0]
