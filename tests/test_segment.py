"""Tests for logslice.segment."""
from datetime import datetime, timedelta, timezone

import pytest

from logslice.parser import LogEntry
from logslice.segment import (
    Segment,
    format_segment_report,
    segment_entries,
)


def _dt(minute: int, second: int = 0) -> datetime:
    return datetime(2024, 1, 1, 12, minute, second, tzinfo=timezone.utc)


def _entry(minute: int, second: int = 0, msg: str = "msg") -> LogEntry:
    return LogEntry(timestamp=_dt(minute, second), severity="INFO", message=msg, source="app")


# ---------------------------------------------------------------------------
# Segment dataclass
# ---------------------------------------------------------------------------

def test_segment_empty_properties():
    seg = Segment()
    assert seg.start is None
    assert seg.end is None
    assert seg.duration_seconds == 0.0
    assert seg.count == 0


def test_segment_single_entry():
    seg = Segment(entries=[_entry(0)])
    assert seg.start == _dt(0)
    assert seg.end == _dt(0)
    assert seg.duration_seconds == 0.0
    assert seg.count == 1


def test_segment_multiple_entries_duration():
    seg = Segment(entries=[_entry(0), _entry(2), _entry(4)])
    assert seg.duration_seconds == pytest.approx(240.0)
    assert seg.count == 3


# ---------------------------------------------------------------------------
# segment_entries
# ---------------------------------------------------------------------------

def test_segment_entries_empty_yields_nothing():
    result = list(segment_entries([]))
    assert result == []


def test_segment_entries_all_within_gap():
    entries = [_entry(0), _entry(1), _entry(2)]
    result = list(segment_entries(entries, max_gap=timedelta(minutes=5)))
    assert len(result) == 1
    assert result[0].count == 3


def test_segment_entries_splits_on_large_gap():
    entries = [_entry(0), _entry(1), _entry(10), _entry(11)]
    result = list(segment_entries(entries, max_gap=timedelta(minutes=5)))
    assert len(result) == 2
    assert result[0].count == 2
    assert result[1].count == 2


def test_segment_entries_multiple_gaps():
    entries = [_entry(0), _entry(10), _entry(20)]
    result = list(segment_entries(entries, max_gap=timedelta(minutes=5)))
    assert len(result) == 3


def test_segment_entries_boundary_exactly_at_gap():
    # gap is exactly max_gap — should NOT split (not strictly greater)
    entries = [_entry(0), _entry(5)]
    result = list(segment_entries(entries, max_gap=timedelta(minutes=5)))
    assert len(result) == 1


def test_segment_entries_just_over_gap_splits():
    entries = [_entry(0, 0), _entry(0, 1)]
    result = list(segment_entries(entries, max_gap=timedelta(seconds=0, microseconds=1)))
    # 1-second gap > 1-microsecond max_gap
    assert len(result) == 2


def test_segment_entries_invalid_gap_raises():
    with pytest.raises(ValueError, match="positive"):
        list(segment_entries([_entry(0)], max_gap=timedelta(seconds=0)))


def test_segment_entries_preserves_order():
    entries = [_entry(0), _entry(1), _entry(2)]
    result = list(segment_entries(entries, max_gap=timedelta(minutes=5)))
    assert result[0].entries == entries


# ---------------------------------------------------------------------------
# format_segment_report
# ---------------------------------------------------------------------------

def test_format_segment_report_empty():
    assert format_segment_report([]) == "No segments found."


def test_format_segment_report_contains_segment_count():
    segs = list(segment_entries([_entry(0), _entry(10)], max_gap=timedelta(minutes=5)))
    report = format_segment_report(segs)
    assert "Segments: 2" in report


def test_format_segment_report_contains_entry_counts():
    segs = list(segment_entries([_entry(0), _entry(1), _entry(10)], max_gap=timedelta(minutes=5)))
    report = format_segment_report(segs)
    assert "entries=2" in report
    assert "entries=1" in report
