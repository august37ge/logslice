"""Tests for logslice.formatter."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from logslice.formatter import (
    format_colored,
    format_json,
    format_plain,
    get_formatter,
    render_entries,
)
from logslice.parser import LogEntry

_TS = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
_ENTRY = LogEntry(timestamp=_TS, severity="INFO", message="server started")


def test_format_plain_contains_all_fields():
    result = format_plain(_ENTRY)
    assert "2024-03-15T10:30:00+00:00" in result
    assert "INFO" in result
    assert "server started" in result


def test_format_plain_structure():
    result = format_plain(_ENTRY)
    assert result.startswith("[")
    assert "] [INFO] " in result


def test_format_colored_contains_ansi_codes():
    result = format_colored(_ENTRY)
    assert "\033[" in result
    assert "\033[0m" in result
    assert "INFO" in result


def test_format_colored_unknown_severity_no_color():
    entry = LogEntry(timestamp=_TS, severity="UNKNOWN", message="test")
    result = format_colored(entry)
    assert "\033[" not in result.split("UNKNOWN")[0].split("]")[-1]


def test_format_json_is_valid_json():
    result = format_json(_ENTRY)
    data = json.loads(result)
    assert data["severity"] == "INFO"
    assert data["message"] == "server started"
    assert "timestamp" in data


def test_get_formatter_plain():
    fn = get_formatter("plain")
    assert fn is format_plain


def test_get_formatter_json():
    fn = get_formatter("json")
    assert fn is format_json


def test_get_formatter_unknown_raises():
    with pytest.raises(ValueError, match="Unknown formatter"):
        get_formatter("xml")


def test_render_entries_yields_formatted_strings():
    entries = [
        LogEntry(timestamp=_TS, severity="DEBUG", message="msg1"),
        LogEntry(timestamp=_TS, severity="ERROR", message="msg2"),
    ]
    results = list(render_entries(entries, fmt="plain"))
    assert len(results) == 2
    assert "DEBUG" in results[0]
    assert "ERROR" in results[1]


def test_render_entries_default_fmt_is_plain():
    entries = [_ENTRY]
    result = list(render_entries(entries))[0]
    assert result == format_plain(_ENTRY)
