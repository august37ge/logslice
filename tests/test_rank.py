"""Tests for logslice.rank."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.rank import (
    RankedEntry,
    _frequency_score,
    _recency_score,
    _severity_score,
    rank_entries,
)


def _entry(
    msg: str = "test message",
    severity: str = "INFO",
    ts: datetime | None = None,
    source: str = "app",
) -> LogEntry:
    if ts is None:
        ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return LogEntry(timestamp=ts, severity=severity, source=source, message=msg)


# ---------------------------------------------------------------------------
# Unit tests for sub-scorers
# ---------------------------------------------------------------------------

def test_severity_score_critical_is_one():
    assert _severity_score(_entry(severity="CRITICAL")) == 1.0


def test_severity_score_debug_is_low():
    score = _severity_score(_entry(severity="DEBUG"))
    assert score < 0.5


def test_severity_score_unknown_is_zero():
    score = _severity_score(_entry(severity="UNKNOWN_XYZ"))
    assert score == 0.0


def test_recency_score_latest_is_one():
    t0 = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
    entry = _entry(ts=t1)
    score = _recency_score(entry, t0.timestamp(), t1.timestamp())
    assert score == pytest.approx(1.0)


def test_recency_score_earliest_is_zero():
    t0 = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
    entry = _entry(ts=t0)
    score = _recency_score(entry, t0.timestamp(), t1.timestamp())
    assert score == pytest.approx(0.0)


def test_recency_score_single_timestamp_is_one():
    t = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
    entry = _entry()
    assert _recency_score(entry, t, t) == 1.0


def test_frequency_score_unique_message_is_one():
    freq_map = {"only once": 1}
    score = _frequency_score(_entry(msg="only once"), freq_map, 1)
    assert score == pytest.approx(0.0)  # 1 out of 1 → 1 - 1/1 = 0


def test_frequency_score_rare_message_higher_than_common():
    freq_map = {"common": 10, "rare": 1}
    rare = _frequency_score(_entry(msg="rare"), freq_map, 11)
    common = _frequency_score(_entry(msg="common"), freq_map, 11)
    assert rare > common


# ---------------------------------------------------------------------------
# Integration tests for rank_entries
# ---------------------------------------------------------------------------

def test_rank_entries_empty_returns_empty():
    assert rank_entries([]) == []


def test_rank_entries_returns_ranked_entry_instances():
    result = rank_entries([_entry()])
    assert isinstance(result[0], RankedEntry)


def test_rank_entries_rank_starts_at_one():
    entries = [_entry(msg="a"), _entry(msg="b")]
    result = rank_entries(entries)
    assert result[0].rank == 1


def test_rank_entries_sorted_descending():
    entries = [
        _entry(msg="low", severity="DEBUG"),
        _entry(msg="high", severity="CRITICAL"),
    ]
    result = rank_entries(entries)
    assert result[0].rank_score >= result[1].rank_score


def test_rank_entries_top_n_limits_results():
    entries = [_entry(msg=f"msg{i}") for i in range(10)]
    result = rank_entries(entries, top_n=3)
    assert len(result) == 3


def test_rank_entries_top_n_larger_than_list_returns_all():
    entries = [_entry(msg=f"msg{i}") for i in range(4)]
    result = rank_entries(entries, top_n=100)
    assert len(result) == 4


def test_rank_entries_critical_outranks_debug():
    t = datetime(2024, 1, 1, 12, tzinfo=timezone.utc)
    debug = _entry(msg="debug msg", severity="DEBUG", ts=t)
    critical = _entry(msg="critical msg", severity="CRITICAL", ts=t)
    result = rank_entries([debug, critical])
    assert result[0].entry.severity == "CRITICAL"


def test_rank_entries_rank_numbers_are_contiguous():
    entries = [_entry(msg=f"m{i}") for i in range(5)]
    result = rank_entries(entries)
    assert [r.rank for r in result] == list(range(1, 6))
