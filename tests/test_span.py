"""Tests for logslice.span."""
from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.span import (
    SpanEntry,
    average_gap,
    format_span_report,
    iter_spans,
    largest_gaps,
)

_BASE = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(offset_seconds: int, msg: str = "msg") -> LogEntry:
    return LogEntry(
        timestamp=_BASE + timedelta(seconds=offset_seconds),
        severity="INFO",
        message=msg,
        raw=f"[INFO] {msg}",
    )


def _spans(offsets: List[int]) -> List[SpanEntry]:
    entries = [_entry(o) for o in offsets]
    return list(iter_spans(entries))


# --- iter_spans ---

def test_iter_spans_empty_yields_nothing():
    assert list(iter_spans([])) == []


def test_iter_spans_single_entry_yields_nothing():
    assert list(iter_spans([_entry(0)])) == []


def test_iter_spans_two_entries_yields_one_span():
    spans = _spans([0, 10])
    assert len(spans) == 1
    assert spans[0].gap_seconds == pytest.approx(10.0)


def test_iter_spans_three_entries_yields_two_spans():
    spans = _spans([0, 5, 20])
    assert len(spans) == 2
    assert spans[0].gap_seconds == pytest.approx(5.0)
    assert spans[1].gap_seconds == pytest.approx(15.0)


def test_iter_spans_before_and_after_are_consecutive_entries():
    e1, e2, e3 = _entry(0), _entry(3), _entry(9)
    spans = list(iter_spans([e1, e2, e3]))
    assert spans[0].before is e1
    assert spans[0].after is e2
    assert spans[1].before is e2
    assert spans[1].after is e3


# --- largest_gaps ---

def test_largest_gaps_returns_top_n_descending():
    spans = _spans([0, 1, 11, 12, 32])
    top = largest_gaps(iter(spans), n=2)
    assert len(top) == 2
    assert top[0].gap_seconds >= top[1].gap_seconds


def test_largest_gaps_n_zero_returns_empty():
    spans = _spans([0, 10, 20])
    assert largest_gaps(iter(spans), n=0) == []


def test_largest_gaps_n_larger_than_list_returns_all():
    spans = _spans([0, 5, 15])
    assert len(largest_gaps(iter(spans), n=100)) == 2


# --- average_gap ---

def test_average_gap_empty_returns_none():
    assert average_gap(iter([])) is None


def test_average_gap_single_span():
    spans = _spans([0, 20])
    avg = average_gap(iter(spans))
    assert avg is not None
    assert avg.total_seconds() == pytest.approx(20.0)


def test_average_gap_multiple_spans():
    spans = _spans([0, 10, 30])
    avg = average_gap(iter(spans))
    assert avg is not None
    # gaps: 10s, 20s -> mean 15s
    assert avg.total_seconds() == pytest.approx(15.0)


# --- format_span_report ---

def test_format_span_report_empty_returns_message():
    result = format_span_report([])
    assert "No spans" in result


def test_format_span_report_contains_total_and_average():
    spans = _spans([0, 10, 30])
    report = format_span_report(spans)
    assert "Total spans" in report
    assert "Average gap" in report


def test_format_span_report_top_gaps_listed():
    spans = _spans([0, 1, 101])
    report = format_span_report(spans, top_n=1)
    assert "100.00s" in report
