"""High-level pipeline: slice → format → output."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from logslice.formatter import render_entries
from logslice.output import write_lines
from logslice.slicer import slice_file


def run_pipeline(
    input_path: Path,
    *,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    min_severity: Optional[str] = None,
    fmt: str = "plain",
    output_path: Optional[Path] = None,
    append: bool = False,
) -> int:
    """Slice *input_path*, format the results, and write to *output_path* or stdout.

    Returns the number of log entries written.
    """
    entries = slice_file(
        input_path,
        start=start,
        end=end,
        min_severity=min_severity,
    )
    lines = render_entries(entries, fmt=fmt)
    return write_lines(lines, output_path, append=append)
