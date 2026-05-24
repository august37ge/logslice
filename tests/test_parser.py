"""Tests for logslice.parser module."""

import pytest
from datetime import datetime
from logslice.parser import parse_line, parse_timestamp, LogEntry, SEVERITY_ORDER


SAMPLE_LINES = [
    (
        "2024-01-15 12:34:56,789 [ERROR] Connection refused",
        datetime(2024, 1, 15, 12, 34, 56, 789000),
        "ERROR",
        "Connection refused",
    ),
    (
        "2024-06-01T08:00:00 INFO Server started",
        datetime(2024, 6, 1, 8, 0, 0),
        "INFO",
        "Server started",
    ),
    (
        "2024-03-20 09:15:30.001 (WARNING) Disk usage above 80%",
        datetime(2024, 3, 20, 9, 15, 30, 1000),
        "WARNING",
        "Disk usage above 80%",
    ),
    (
        "2024-03-20 09:15:30 WARN low memory",
        datetime(2024, 3, 20, 9, 15, 30),
        "WARNING",
        "low memory",
    ),
    (
        "2024-03-20 09:15:30 FATAL system crash",
        datetime(2024, 3, 20, 9, 15, 30),
        "CRITICAL",
        "system crash",
    ),
]


@pytest.mark.parametrize("line,expected_ts,expected_sev,expected_msg", SAMPLE_LINES)
def test_parse_line_valid(line, expected_ts, expected_sev, expected_msg):
    entry = parse_line(line)
    assert entry is not None
    assert entry.timestamp == expected_ts
    assert entry.severity == expected_sev
    assert entry.message == expected_msg
    assert entry.raw == line


def test_parse_line_invalid_returns_none():
    assert parse_line("this is not a log line") is None
    assert parse_line("") is None
    assert parse_line("  ") is None


def test_severity_level_ordering():
    levels = [parse_line(line).severity_level for line, *_ in SAMPLE_LINES]
    # ERROR > INFO, WARNING > INFO
    assert levels[0] > levels[1]   # ERROR > INFO
    assert levels[2] > levels[1]   # WARNING > INFO


def test_parse_timestamp_raises_on_bad_input():
    from logslice.parser import parse_timestamp
    with pytest.raises(ValueError):
        parse_timestamp("not-a-date")


def test_log_entry_severity_level_unknown():
    entry = LogEntry(
        timestamp=datetime.now(),
        severity="UNKNOWN",
        message="test",
        raw="test",
    )
    assert entry.severity_level == -1


def test_log_entry_severity_level_matches_severity_order():
    """Verify that severity_level values align with the SEVERITY_ORDER mapping."""
    for severity, expected_level in SEVERITY_ORDER.items():
        entry = LogEntry(
            timestamp=datetime.now(),
            severity=severity,
            message="test",
            raw="test",
        )
        assert entry.severity_level == expected_level, (
            f"Expected severity_level {expected_level} for '{severity}', "
            f"got {entry.severity_level}"
        )


@pytest.mark.parametrize("line,expected_ts,_sev,_msg", SAMPLE_LINES)
def test_parse_line_raw_preserved(line, expected_ts, _sev, _msg):
    """Ensure the raw field always stores the original unparsed line."""
    entry = parse_line(line)
    assert entry is not None
    assert entry.raw == line
