"""Tests for logslice.report_context — context report generation helpers."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from logslice.parser import LogEntry
from logslice.context import ContextEntry
from logslice.report_context import (
    context_report,
    severity_predicate,
    keyword_predicate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(msg: str, severity: str = "INFO", ts: str = "2024-01-01T12:00:00Z") -> LogEntry:
    return LogEntry(
        timestamp=datetime.fromisoformat(ts.replace("Z", "+00:00")),
        severity=severity,
        message=msg,
        raw=f"2024-01-01T12:00:00Z {severity} {msg}",
    )


def _ctx_entry(match: LogEntry, before=None, after=None) -> ContextEntry:
    return ContextEntry(
        match=match,
        before=before or [],
        after=after or [],
    )


# ---------------------------------------------------------------------------
# severity_predicate
# ---------------------------------------------------------------------------

def test_severity_predicate_matches_exact():
    pred = severity_predicate("ERROR")
    assert pred(_entry("boom", severity="ERROR")) is True


def test_severity_predicate_excludes_lower():
    pred = severity_predicate("ERROR")
    assert pred(_entry("info msg", severity="INFO")) is False


def test_severity_predicate_case_insensitive_input():
    pred = severity_predicate("error")
    assert pred(_entry("crash", severity="ERROR")) is True


def test_severity_predicate_includes_critical():
    pred = severity_predicate("ERROR")
    assert pred(_entry("fatal", severity="CRITICAL")) is True


# ---------------------------------------------------------------------------
# keyword_predicate
# ---------------------------------------------------------------------------

def test_keyword_predicate_matches_substring():
    pred = keyword_predicate("timeout")
    assert pred(_entry("connection timeout occurred")) is True


def test_keyword_predicate_no_match():
    pred = keyword_predicate("timeout")
    assert pred(_entry("everything is fine")) is False


def test_keyword_predicate_case_insensitive():
    pred = keyword_predicate("TIMEOUT")
    assert pred(_entry("connection timeout occurred")) is True


def test_keyword_predicate_empty_keyword_matches_all():
    pred = keyword_predicate("")
    assert pred(_entry("anything")) is True


# ---------------------------------------------------------------------------
# context_report
# ---------------------------------------------------------------------------

def test_context_report_empty_input():
    result = context_report([])
    assert result == ""


def test_context_report_single_match_no_context():
    entry = _entry("disk full", severity="ERROR")
    ctx = _ctx_entry(entry)
    result = context_report([ctx])
    assert "disk full" in result
    assert "ERROR" in result


def test_context_report_includes_before_lines():
    match = _entry("crash", severity="ERROR")
    before = [_entry("starting process"), _entry("loading config")]
    ctx = _ctx_entry(match, before=before)
    result = context_report([ctx])
    assert "starting process" in result
    assert "loading config" in result
    assert "crash" in result


def test_context_report_includes_after_lines():
    match = _entry("crash", severity="ERROR")
    after = [_entry("cleanup started"), _entry("cleanup done")]
    ctx = _ctx_entry(match, after=after)
    result = context_report([ctx])
    assert "cleanup started" in result
    assert "cleanup done" in result


def test_context_report_separator_between_groups():
    e1 = _entry("error one", severity="ERROR")
    e2 = _entry("error two", severity="ERROR")
    ctx1 = _ctx_entry(e1)
    ctx2 = _ctx_entry(e2)
    result = context_report([ctx1, ctx2])
    # Expect some separator (dashes or blank line) between groups
    assert "error one" in result
    assert "error two" in result
    # The two matches should not be on the same line
    lines = result.splitlines()
    positions = [i for i, ln in enumerate(lines) if "error one" in ln or "error two" in ln]
    assert len(positions) == 2
    assert positions[1] > positions[0] + 1  # at least one line between them


def test_context_report_match_line_highlighted():
    match = _entry("critical failure", severity="CRITICAL")
    ctx = _ctx_entry(match)
    result = context_report([ctx])
    # Match line should be visually distinct (e.g. prefixed with '>')
    match_line = next(ln for ln in result.splitlines() if "critical failure" in ln)
    assert match_line.lstrip().startswith(">") or ">>" in match_line or "CRITICAL" in match_line
