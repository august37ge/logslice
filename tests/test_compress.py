"""Tests for logslice.compress."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.compress import (
    CompressedRun,
    compress_entries,
    compression_ratio,
    decompress_runs,
    format_compressed_run,
)
from logslice.parser import LogEntry


def _dt(hour: int = 0, minute: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, tzinfo=timezone.utc)


def _entry(msg: str, severity: str = "INFO", hour: int = 0, minute: int = 0) -> LogEntry:
    return LogEntry(timestamp=_dt(hour, minute), severity=severity, message=msg, raw=f"{severity} {msg}")


# --- compress_entries ---

def test_compress_entries_empty_returns_empty():
    assert compress_entries([]) == []


def test_compress_entries_single_entry_count_one():
    runs = compress_entries([_entry("hello")])
    assert len(runs) == 1
    assert runs[0].count == 1


def test_compress_entries_two_identical_entries_merged():
    entries = [_entry("disk full", "ERROR"), _entry("disk full", "ERROR", minute=1)]
    runs = compress_entries(entries)
    assert len(runs) == 1
    assert runs[0].count == 2


def test_compress_entries_different_messages_not_merged():
    entries = [_entry("a"), _entry("b")]
    runs = compress_entries(entries)
    assert len(runs) == 2


def test_compress_entries_different_severity_not_merged():
    entries = [_entry("msg", "INFO"), _entry("msg", "ERROR")]
    runs = compress_entries(entries)
    assert len(runs) == 2


def test_compress_entries_run_tracks_first_and_last_timestamp():
    e1 = _entry("loop", minute=0)
    e2 = _entry("loop", minute=5)
    e3 = _entry("loop", minute=10)
    runs = compress_entries([e1, e2, e3])
    assert runs[0].first_timestamp == _dt(minute=0)
    assert runs[0].last_timestamp == _dt(minute=10)


def test_compress_entries_non_consecutive_not_merged():
    entries = [_entry("x"), _entry("y"), _entry("x")]
    runs = compress_entries(entries)
    assert len(runs) == 3


def test_compress_entries_strips_whitespace_for_key():
    entries = [_entry("  hello  "), _entry("hello")]
    runs = compress_entries(entries)
    assert len(runs) == 1
    assert runs[0].count == 2


# --- decompress_runs ---

def test_decompress_runs_restores_original_count():
    entries = [_entry("msg")] * 4
    runs = compress_entries(entries)
    restored = list(decompress_runs(runs))
    assert len(restored) == 4


def test_decompress_runs_empty_input():
    assert list(decompress_runs([])) == []


# --- compression_ratio ---

def test_compression_ratio_no_compression():
    assert compression_ratio(10, 10) == pytest.approx(1.0)


def test_compression_ratio_half():
    assert compression_ratio(10, 5) == pytest.approx(0.5)


def test_compression_ratio_zero_original_returns_zero():
    assert compression_ratio(0, 0) == pytest.approx(0.0)


# --- format_compressed_run ---

def test_format_compressed_run_single_no_repeat_marker():
    run = CompressedRun(entry=_entry("started", "INFO"), count=1)
    text = format_compressed_run(run)
    assert "(x" not in text
    assert "INFO" in text
    assert "started" in text


def test_format_compressed_run_multiple_shows_count():
    e = _entry("loop error", "ERROR", minute=0)
    run = CompressedRun(entry=e, count=5, first_timestamp=_dt(minute=0), last_timestamp=_dt(minute=4))
    text = format_compressed_run(run)
    assert "(x5)" in text
    assert ".." in text
