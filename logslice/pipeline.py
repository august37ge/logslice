"""High-level pipeline that wires parser, slicer, formatter, output, and stats."""
from __future__ import annotations

from datetime import datetime
from typing import IO, Optional

from logslice.slicer import slice_file
from logslice.formatter import get_formatter, render_entries
from logslice.output import write_to_stream
from logslice.stats import compute_stats, format_stats, SliceStats


def run_pipeline(
    path: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    min_severity: Optional[str] = None,
    fmt: str = "plain",
    output: IO[str] = None,
    show_stats: bool = False,
) -> SliceStats:
    """Execute the full log-slicing pipeline and return statistics.

    Parameters
    ----------
    path:         Path to the log file.
    start:        Optional lower bound for timestamp filtering.
    end:          Optional upper bound for timestamp filtering.
    min_severity: Optional minimum severity level (e.g. 'WARNING').
    fmt:          Output format – 'plain', 'colored', or 'json'.
    output:       Writable stream; defaults to sys.stdout.
    show_stats:   If True, print a stats summary after the entries.

    Returns
    -------
    SliceStats collected over the matched entries.
    """
    import sys

    if output is None:
        output = sys.stdout

    formatter = get_formatter(fmt)
    entries = list(slice_file(path, start=start, end=end, min_severity=min_severity))
    lines = render_entries(entries, formatter)
    write_to_stream(lines, output)

    stats = compute_stats(entries)

    if show_stats:
        output.write("\n--- stats ---\n")
        output.write(format_stats(stats))
        output.write("\n")

    return stats
