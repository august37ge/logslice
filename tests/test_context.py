"""Tests for logslice.context."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.context import ContextEntry, format_context_entry, with_context
from logslice.parser import LogEntry


def _entry(msg: str, severity: str = "INFO", minute: int = 0) -> LogEntry:
    ts = datetime(2024, 1, 1, 12, minute, 0, tzinfo=timezone.utc)
    return LogEntry(timestamp=ts.isoformat(), severity=severity, message=msg, raw=f"{ts.isoformat()} [{severity}] {msg}")


def _is_error(e: LogEntry) -> bool:
    return e.severity == "ERROR"


# ---------------------------------------------------------------------------
# Basic matching
# ---------------------------------------------------------------------------

def test_no_match_yields_nothing():
    entries = [_entry("ok", "INFO", i) for i in range(5)]
    result = list(with_context(entries, _is_error, before=1, after=1))
    assert result == []


def test_match_no_context():
    entries = [_entry("a"), _entry("boom", "ERROR"), _entry("b")]
    result = list(with_context(entries, _is_error, before=0, after=0))
    assert len(result) == 1
    assert result[0].entry.message == "boom"
    assert result[0].before == []
    assert result[0].after == []


def test_before_context():
    entries = [_entry("a", minute=0), _entry("b", minute=1), _entry("boom", "ERROR", minute=2)]
    result = list(with_context(entries, _is_error, before=2, after=0))
    assert len(result) == 1
    assert [e.message for e in result[0].before] == ["a", "b"]


def test_before_context_capped_by_available():
    entries = [_entry("a", minute=0), _entry("boom", "ERROR", minute=1)]
    result = list(with_context(entries, _is_error, before=5, after=0))
    assert len(result[0].before) == 1
    assert result[0].before[0].message == "a"


def test_after_context():
    entries = [_entry("boom", "ERROR", minute=0), _entry("x", minute=1), _entry("y", minute=2)]
    result = list(with_context(entries, _is_error, before=0, after=2))
    assert len(result) == 1
    assert [e.message for e in result[0].after] == ["x", "y"]


def test_after_context_capped_by_available():
    entries = [_entry("boom", "ERROR", minute=0), _entry("x", minute=1)]
    result = list(with_context(entries, _is_error, before=0, after=5))
    assert [e.message for e in result[0].after] == ["x"]


def test_multiple_matches():
    entries = [
        _entry("a", minute=0),
        _entry("e1", "ERROR", minute=1),
        _entry("b", minute=2),
        _entry("e2", "ERROR", minute=3),
        _entry("c", minute=4),
    ]
    result = list(with_context(entries, _is_error, before=1, after=1))
    assert len(result) == 2
    assert result[0].entry.message == "e1"
    assert result[1].entry.message == "e2"


def test_negative_before_raises():
    with pytest.raises(ValueError):
        list(with_context([], _is_error, before=-1, after=0))


def test_negative_after_raises():
    with pytest.raises(ValueError):
        list(with_context([], _is_error, before=0, after=-1))


# ---------------------------------------------------------------------------
# format_context_entry
# ---------------------------------------------------------------------------

def test_format_context_entry_marks_match():
    ctx = ContextEntry(entry=_entry("boom", "ERROR"))
    lines = format_context_entry(ctx)
    assert any(line.startswith(">") for line in lines)


def test_format_context_entry_separator_appended():
    ctx = ContextEntry(entry=_entry("boom", "ERROR"))
    lines = format_context_entry(ctx, separator="---")
    assert lines[-1] == "---"


def test_format_context_entry_no_separator():
    ctx = ContextEntry(entry=_entry("boom", "ERROR"))
    lines = format_context_entry(ctx, separator="")
    assert not any(line == "--" for line in lines)


def test_format_context_entry_before_and_after_indented():
    ctx = ContextEntry(
        entry=_entry("boom", "ERROR", minute=2),
        before=[_entry("pre", minute=1)],
        after=[_entry("post", minute=3)],
    )
    lines = format_context_entry(ctx, separator="")
    assert lines[0].startswith("  ")
    assert lines[1].startswith(">")
    assert lines[2].startswith("  ")
