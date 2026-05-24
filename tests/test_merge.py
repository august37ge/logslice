"""Tests for logslice.merge."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.merge import count_merged, merge_and_deduplicate, merge_sorted
from logslice.parser import LogEntry


def _entry(ts: str, severity: str = "INFO", message: str = "msg") -> LogEntry:
    dt = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    return LogEntry(timestamp=dt, severity=severity, message=message, raw=f"{ts} {severity} {message}")


# ---------------------------------------------------------------------------
# merge_sorted
# ---------------------------------------------------------------------------

def test_merge_sorted_single_stream():
    entries = [_entry("2024-01-01T00:00:01"), _entry("2024-01-01T00:00:02")]
    result = list(merge_sorted(entries))
    assert result == entries


def test_merge_sorted_two_streams_interleaved():
    a = [_entry("2024-01-01T00:00:01"), _entry("2024-01-01T00:00:03")]
    b = [_entry("2024-01-01T00:00:02"), _entry("2024-01-01T00:00:04")]
    result = list(merge_sorted(a, b))
    timestamps = [e.timestamp.second for e in result]
    assert timestamps == [1, 2, 3, 4]


def test_merge_sorted_empty_streams():
    result = list(merge_sorted([], []))
    assert result == []


def test_merge_sorted_one_empty_one_nonempty():
    entries = [_entry("2024-01-01T00:00:01")]
    result = list(merge_sorted([], entries))
    assert len(result) == 1


def test_merge_sorted_preserves_order_across_three_streams():
    a = [_entry("2024-01-01T00:00:01"), _entry("2024-01-01T00:00:06")]
    b = [_entry("2024-01-01T00:00:02"), _entry("2024-01-01T00:00:05")]
    c = [_entry("2024-01-01T00:00:03"), _entry("2024-01-01T00:00:04")]
    result = list(merge_sorted(a, b, c))
    assert result == sorted(result, key=lambda e: e.timestamp)


# ---------------------------------------------------------------------------
# merge_and_deduplicate
# ---------------------------------------------------------------------------

def test_dedup_no_duplicates_returns_all():
    a = [_entry("2024-01-01T00:00:01", message="a")]
    b = [_entry("2024-01-01T00:00:02", message="b")]
    result = list(merge_and_deduplicate(a, b))
    assert len(result) == 2


def test_dedup_removes_exact_consecutive_duplicate():
    a = [
        _entry("2024-01-01T00:00:01", message="same"),
        _entry("2024-01-01T00:00:01", message="same"),
    ]
    result = list(merge_and_deduplicate(a, window_seconds=1.0))
    assert len(result) == 1


def test_dedup_keeps_duplicate_outside_window():
    a = [
        _entry("2024-01-01T00:00:01", message="same"),
        _entry("2024-01-01T00:00:10", message="same"),
    ]
    result = list(merge_and_deduplicate(a, window_seconds=5.0))
    assert len(result) == 2


def test_dedup_different_severity_not_deduped():
    a = [
        _entry("2024-01-01T00:00:01", severity="INFO", message="x"),
        _entry("2024-01-01T00:00:01", severity="ERROR", message="x"),
    ]
    result = list(merge_and_deduplicate(a, window_seconds=5.0))
    assert len(result) == 2


# ---------------------------------------------------------------------------
# count_merged
# ---------------------------------------------------------------------------

def test_count_merged_empty():
    total, sources = count_merged([])
    assert total == 0
    assert sources == 0


def test_count_merged_counts_entries():
    entries = [_entry("2024-01-01T00:00:01"), _entry("2024-01-01T00:00:02")]
    total, _ = count_merged(entries)
    assert total == 2
