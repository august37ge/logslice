"""Tests for logslice.filter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.filter import FilterConfig, filter_entries, filter_by_severity
from logslice.parser import LogEntry


def _entry(
    severity: str = "INFO",
    message: str = "hello world",
    source: str = "",
) -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        severity=severity,
        message=message,
        raw=f"2024-01-01T00:00:00Z [{severity}] {message}",
        extra={"source": source} if source else {},
    )


def _collect(it) -> List[LogEntry]:
    return list(it)


# --- FilterConfig construction ---

def test_filter_config_uppercases_severities():
    cfg = FilterConfig(severities=["info", "warn"])
    assert cfg.severities == ["INFO", "WARN"]


def test_filter_config_empty_severities_means_all():
    cfg = FilterConfig()
    assert cfg.severities == []


# --- filter_entries: severity ---

def test_filter_by_severity_keeps_matching():
    entries = [_entry("INFO"), _entry("ERROR"), _entry("DEBUG")]
    cfg = FilterConfig(severities=["INFO", "ERROR"])
    result = _collect(filter_entries(entries, cfg))
    assert len(result) == 2
    assert all(e.severity in ("INFO", "ERROR") for e in result)


def test_filter_empty_severity_list_returns_all():
    entries = [_entry("INFO"), _entry("ERROR")]
    cfg = FilterConfig()
    assert len(_collect(filter_entries(entries, cfg))) == 2


# --- filter_entries: message pattern ---

def test_filter_by_message_pattern_matches():
    entries = [_entry(message="connection refused"), _entry(message="all ok")]
    cfg = FilterConfig(message_pattern="refused")
    result = _collect(filter_entries(entries, cfg))
    assert len(result) == 1
    assert "refused" in result[0].message


def test_filter_message_pattern_case_insensitive_by_default():
    entries = [_entry(message="Connection Refused"), _entry(message="all ok")]
    cfg = FilterConfig(message_pattern="connection refused")
    assert len(_collect(filter_entries(entries, cfg))) == 1


def test_filter_message_pattern_case_sensitive():
    entries = [_entry(message="Connection Refused"), _entry(message="connection refused")]
    cfg = FilterConfig(message_pattern="connection refused", ignore_case=False)
    result = _collect(filter_entries(entries, cfg))
    assert len(result) == 1
    assert result[0].message == "connection refused"


# --- filter_entries: source pattern ---

def test_filter_by_source_pattern():
    entries = [
        _entry(source="app.server"),
        _entry(source="app.worker"),
        _entry(source="scheduler"),
    ]
    cfg = FilterConfig(source_pattern=r"app\.")
    result = _collect(filter_entries(entries, cfg))
    assert len(result) == 2


def test_filter_source_no_match_excludes_all():
    entries = [_entry(source="database"), _entry(source="cache")]
    cfg = FilterConfig(source_pattern="^app")
    assert _collect(filter_entries(entries, cfg)) == []


# --- combined filters ---

def test_filter_severity_and_message_combined():
    entries = [
        _entry(severity="ERROR", message="disk full"),
        _entry(severity="ERROR", message="all good"),
        _entry(severity="INFO", message="disk full"),
    ]
    cfg = FilterConfig(severities=["ERROR"], message_pattern="disk")
    result = _collect(filter_entries(entries, cfg))
    assert len(result) == 1
    assert result[0].severity == "ERROR"
    assert "disk" in result[0].message


# --- filter_by_severity convenience wrapper ---

def test_filter_by_severity_convenience():
    entries = [_entry("DEBUG"), _entry("INFO"), _entry("WARNING")]
    result = _collect(filter_by_severity(entries, ["DEBUG", "WARNING"]))
    assert len(result) == 2
    assert all(e.severity in ("DEBUG", "WARNING") for e in result)
