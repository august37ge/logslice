"""Pivot aggregated windows into a 2-D grid (time × severity)."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Tuple

from logslice.aggregate import AggregateWindow

# Default severity ordering used when none is provided.
_DEFAULT_SEVERITIES = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def pivot_by_severity(
    windows: Iterable[AggregateWindow],
    severities: List[str] | None = None,
) -> Tuple[List[datetime], List[str], Dict[Tuple[datetime, str], int]]:
    """Pivot windows into a (row=time, col=severity) matrix.

    Returns:
        A tuple of (row_labels, col_labels, cell_values) where *cell_values*
        maps ``(window_start, severity)`` to a count.
    """
    window_list = list(windows)
    if not window_list:
        return [], severities or [], {}

    row_labels: List[datetime] = [w.window_start for w in window_list]

    if severities is None:
        found: List[str] = []
        seen = set()
        for w in window_list:
            for sev in w.by_severity:
                if sev not in seen:
                    seen.add(sev)
                    found.append(sev)
        col_labels = sorted(found, key=lambda s: _DEFAULT_SEVERITIES.index(s)
                            if s in _DEFAULT_SEVERITIES else 999)
    else:
        col_labels = severities

    cells: Dict[Tuple[datetime, str], int] = {}
    for w in window_list:
        for sev in col_labels:
            cells[(w.window_start, sev)] = w.by_severity.get(sev, 0)

    return row_labels, col_labels, cells


def format_pivot(
    row_labels: List[datetime],
    col_labels: List[str],
    cells: Dict[Tuple[datetime, str], int],
    col_width: int = 10,
) -> str:
    """Render the pivot table as a fixed-width text grid."""
    if not row_labels:
        return "No data."

    time_col = 20
    header = f"{'Time':<{time_col}}" + "".join(f"{c:>{col_width}}" for c in col_labels)
    sep = "-" * len(header)
    lines = [header, sep]

    for ts in row_labels:
        row = f"{ts.strftime('%Y-%m-%d %H:%M:%S'):<{time_col}}"
        for sev in col_labels:
            row += f"{cells.get((ts, sev), 0):>{col_width}}"
        lines.append(row)

    return "\n".join(lines)
