"""High-level pipeline that wires together slicing, normalizing, and rendering."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from logslice.formatter import get_formatter, render_entries
from logslice.normalize import normalize_entries
from logslice.output import write_to_stream
from logslice.slicer import slice_file
from logslice.stats import SliceStats, compute_stats

import io


def run_pipeline(
    log_path: Path,
    *,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    severity: Optional[str] = None,
    fmt: str = "plain",
    normalize: bool = True,
    stream: Optional[io.TextIOBase] = None,
    output_path: Optional[Path] = None,
) -> SliceStats:
    """Run the full logslice pipeline and return statistics.

    Parameters
    ----------
    log_path:    Path to the log file to process.
    start:       Inclusive lower-bound timestamp filter.
    end:         Inclusive upper-bound timestamp filter.
    severity:    Minimum severity level to include (e.g. ``"WARNING"``).
    fmt:         Output format — ``"plain"``, ``"colored"``, or ``"json"``.
    normalize:   When *True* severity/message normalization is applied.
    stream:      If provided, rendered lines are written here.
    output_path: If provided, rendered lines are also written to this file.
    """
    entries, skipped = slice_file(
        log_path,
        start=start,
        end=end,
        min_severity=severity,
    )

    if normalize:
        entries = list(normalize_entries(entries))
    else:
        entries = list(entries)

    formatter = get_formatter(fmt)
    lines = list(render_entries(entries, formatter))

    if stream is not None:
        write_to_stream(lines, stream)

    if output_path is not None:
        from logslice.output import write_lines
        write_lines(lines, output_path)

    stats = compute_stats(entries, skipped_lines=skipped)
    return stats
