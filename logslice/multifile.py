"""Multi-file log slicing: merge entries from rotated and multiple log files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogEntry, parse_line
from logslice.rotate import find_rotated, iter_rotated_lines
from logslice.slicer import slice_logs


def _parse_stream(lines: Iterable[str]) -> Iterator[LogEntry]:
    """Yield valid :class:`LogEntry` objects from *lines*."""
    for line in lines:
        entry = parse_line(line.rstrip("\n"))
        if entry is not None:
            yield entry


def merge_files(
    paths: List[str | Path],
    *,
    include_rotated: bool = False,
    start=None,
    end=None,
    severity: Optional[str] = None,
) -> Iterator[LogEntry]:
    """Yield log entries from multiple files, sorted by timestamp.

    Parameters
    ----------
    paths:
        Ordered list of log file paths to read.
    include_rotated:
        When *True*, also read rotated variants of each path.
    start / end:
        Optional :class:`datetime` bounds passed to :func:`slice_logs`.
    severity:
        Minimum severity string passed to :func:`slice_logs`.
    """
    all_entries: List[LogEntry] = []

    for path in paths:
        path = Path(path)
        if include_rotated:
            lines: Iterable[str] = iter_rotated_lines(path)
        else:
            if not path.exists():
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

        entries = list(
            slice_logs(
                _parse_stream(lines),
                start=start,
                end=end,
                severity=severity,
            )
        )
        all_entries.extend(entries)

    all_entries.sort(key=lambda e: e.timestamp)
    yield from all_entries


def file_count_with_rotated(base_path: str | Path) -> int:
    """Return total number of log files (base + rotated) for *base_path*."""
    base = Path(base_path)
    rotated = find_rotated(base)
    return len(rotated) + (1 if base.exists() else 0)
