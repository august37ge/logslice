"""Tests for logslice.pivot."""

from __future__ import annotations

from datetime import datetime, timedelta

from logslice.aggregate import AggregateWindow
from logslice.pivot import format_pivot, pivot_by_severity


def _window(
    start: str,
    by_severity: dict | None = None,
    minutes: int = 5,
) -> AggregateWindow:
    dt = datetime.fromisoformat(start)
    w = AggregateWindow(
        window_start=dt,
        window_end=dt + timedelta(minutes=minutes),
        total=sum((by_severity or {}).values()),
        by_severity=by_severity or {},
    )
    return w


# ---------------------------------------------------------------------------
# pivot_by_severity
# ---------------------------------------------------------------------------

def test_pivot_empty_returns_empty_structures():
    rows, cols, cells = pivot_by_severity([])
    assert rows == []
    assert cells == {}


def test_pivot_row_labels_match_window_starts():
    windows = [
        _window("2024-01-01T10:00:00", {"INFO": 2}),
        _window("2024-01-01T10:05:00", {"ERROR": 1}),
    ]
    rows, _, _ = pivot_by_severity(windows)
    assert rows[0] == datetime(2024, 1, 1, 10, 0, 0)
    assert rows[1] == datetime(2024, 1, 1, 10, 5, 0)


def test_pivot_col_labels_auto_detected():
    windows = [
        _window("2024-01-01T10:00:00", {"INFO": 1, "ERROR": 2}),
    ]
    _, cols, _ = pivot_by_severity(windows)
    assert "INFO" in cols
    assert "ERROR" in cols


def test_pivot_col_labels_respect_severity_order():
    windows = [
        _window("2024-01-01T10:00:00", {"ERROR": 1, "DEBUG": 2, "INFO": 3}),
    ]
    _, cols, _ = pivot_by_severity(windows)
    assert cols.index("DEBUG") < cols.index("INFO") < cols.index("ERROR")


def test_pivot_explicit_severities_used():
    windows = [_window("2024-01-01T10:00:00", {"INFO": 1})]
    _, cols, _ = pivot_by_severity(windows, severities=["DEBUG", "INFO"])
    assert cols == ["DEBUG", "INFO"]


def test_pivot_cells_contain_correct_counts():
    windows = [
        _window("2024-01-01T10:00:00", {"INFO": 3, "ERROR": 1}),
    ]
    rows, cols, cells = pivot_by_severity(windows)
    ts = datetime(2024, 1, 1, 10, 0, 0)
    assert cells[(ts, "INFO")] == 3
    assert cells[(ts, "ERROR")] == 1


def test_pivot_missing_severity_defaults_to_zero():
    windows = [
        _window("2024-01-01T10:00:00", {"INFO": 2}),
    ]
    rows, cols, cells = pivot_by_severity(windows, severities=["INFO", "ERROR"])
    ts = datetime(2024, 1, 1, 10, 0, 0)
    assert cells[(ts, "ERROR")] == 0


# ---------------------------------------------------------------------------
# format_pivot
# ---------------------------------------------------------------------------

def test_format_pivot_empty_returns_no_data():
    assert format_pivot([], [], {}) == "No data."


def test_format_pivot_contains_severity_header():
    windows = [_window("2024-01-01T10:00:00", {"INFO": 1})]
    rows, cols, cells = pivot_by_severity(windows)
    output = format_pivot(rows, cols, cells)
    assert "INFO" in output


def test_format_pivot_contains_timestamp():
    windows = [_window("2024-01-01T10:00:00", {"INFO": 1})]
    rows, cols, cells = pivot_by_severity(windows)
    output = format_pivot(rows, cols, cells)
    assert "2024-01-01 10:00:00" in output


def test_format_pivot_row_count_matches_windows():
    windows = [
        _window("2024-01-01T10:00:00", {"INFO": 1}),
        _window("2024-01-01T10:05:00", {"ERROR": 2}),
    ]
    rows, cols, cells = pivot_by_severity(windows)
    output = format_pivot(rows, cols, cells)
    # header + separator + 2 data rows
    assert len(output.splitlines()) == 4
