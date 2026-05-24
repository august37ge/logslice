"""Tests for logslice.profile."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from logslice.profile import (
    ProfileResult,
    format_profile,
    profile_file,
    profile_lines,
)


VALID_LINE = "2024-01-15T10:00:00 ERROR Something went wrong"
INFO_LINE = "2024-01-15T10:01:00 INFO  Service started"
INVALID_LINE = "not a log line at all"


def test_profile_lines_empty_input():
    result = profile_lines([])
    assert result.total_lines == 0
    assert result.parsed_lines == 0
    assert result.skipped_lines == 0
    assert result.elapsed_seconds >= 0.0


def test_profile_lines_counts_total():
    lines = [VALID_LINE, INFO_LINE, INVALID_LINE]
    result = profile_lines(lines)
    assert result.total_lines == 3


def test_profile_lines_parsed_vs_skipped():
    lines = [VALID_LINE, INFO_LINE, INVALID_LINE]
    result = profile_lines(lines)
    assert result.parsed_lines == 2
    assert result.skipped_lines == 1


def test_profile_lines_severity_counts():
    lines = [VALID_LINE, VALID_LINE, INFO_LINE]
    result = profile_lines(lines)
    assert result.severity_counts.get("ERROR", 0) == 2
    assert result.severity_counts.get("INFO", 0) == 1


def test_profile_lines_throughput_positive():
    lines = [VALID_LINE] * 100
    result = profile_lines(lines)
    assert result.lines_per_second > 0


def test_profile_result_summary_contains_key_fields():
    result = ProfileResult(
        total_lines=10,
        parsed_lines=8,
        skipped_lines=2,
        elapsed_seconds=0.5,
        lines_per_second=20.0,
    )
    summary = result.summary()
    assert "total=10" in summary
    assert "parsed=8" in summary
    assert "skipped=2" in summary


def test_format_profile_header():
    result = profile_lines([VALID_LINE, INFO_LINE])
    report = format_profile(result)
    assert "=== logslice profile ===" in report


def test_format_profile_shows_severity_breakdown():
    result = profile_lines([VALID_LINE, INFO_LINE])
    report = format_profile(result)
    assert "ERROR" in report
    assert "INFO" in report


def test_format_profile_shows_skipped():
    result = profile_lines([INVALID_LINE])
    report = format_profile(result)
    assert "Skipped" in report
    assert "1" in report


def test_profile_file_reads_file(tmp_path: Path):
    log = tmp_path / "app.log"
    log.write_text(
        textwrap.dedent("""\
            2024-01-15T10:00:00 ERROR bad thing
            2024-01-15T10:00:01 INFO  ok thing
            garbage line
        """)
    )
    result = profile_file(str(log))
    assert result.total_lines == 3
    assert result.parsed_lines == 2
    assert result.skipped_lines == 1


def test_profile_file_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        profile_file(str(tmp_path / "nonexistent.log"))
