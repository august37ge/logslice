"""Tests for logslice.search."""

import re
from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.search import (
    _compile_pattern,
    matches_entry,
    search_entries,
)


def _entry(message: str, severity: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"2024-01-01 12:00:00 {severity} {message}",
    )


def test_compile_pattern_returns_compiled_regex():
    pat = _compile_pattern("error")
    assert pat.pattern == "error"


def test_compile_pattern_ignore_case():
    pat = _compile_pattern("error", ignore_case=True)
    assert pat.flags & re.IGNORECASE


def test_compile_pattern_raises_on_invalid_regex():
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        _compile_pattern("[unclosed")


def test_matches_entry_true():
    entry = _entry("Connection error occurred")
    pat = _compile_pattern("error")
    assert matches_entry(entry, pat) is True


def test_matches_entry_false():
    entry = _entry("All systems nominal")
    pat = _compile_pattern("error")
    assert matches_entry(entry, pat) is False


def test_search_entries_no_keyword_yields_all():
    entries = [_entry("foo"), _entry("bar"), _entry("baz")]
    result = list(search_entries(entries))
    assert result == entries


def test_search_entries_filters_by_keyword():
    entries = [_entry("disk error"), _entry("all ok"), _entry("another error")]
    result = list(search_entries(entries, keyword="error"))
    assert len(result) == 2
    assert all("error" in e.message for e in result)


def test_search_entries_ignore_case():
    entries = [_entry("ERROR: boom"), _entry("info message")]
    result = list(search_entries(entries, keyword="error", ignore_case=True))
    assert len(result) == 1
    assert result[0].message == "ERROR: boom"


def test_search_entries_invert():
    entries = [_entry("disk error"), _entry("all ok"), _entry("another error")]
    result = list(search_entries(entries, keyword="error", invert=True))
    assert len(result) == 1
    assert result[0].message == "all ok"


def test_search_entries_regex_pattern():
    entries = [_entry("timeout after 30s"), _entry("timeout after 5s"), _entry("ok")]
    result = list(search_entries(entries, keyword=r"timeout after \d+s"))
    assert len(result) == 2


def test_search_entries_empty_input():
    result = list(search_entries([], keyword="error"))
    assert result == []
