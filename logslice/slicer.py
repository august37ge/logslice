"""Core log slicing logic: filter log entries by time range and severity."""

from datetime import datetime
from typing import Iterator, Optional

from logslice.parser import LogEntry, parse_line, severity_level


def slice_logs(
    lines: Iterator[str],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    min_severity: Optional[str] = None,
) -> Iterator[LogEntry]:
    """Yield log entries that fall within the given time range and severity.

    Args:
        lines: Iterable of raw log line strings.
        start: Inclusive lower bound for log timestamp. None means no lower bound.
        end: Inclusive upper bound for log timestamp. None means no upper bound.
        min_severity: Minimum severity level (e.g. 'WARNING'). None means all.

    Yields:
        LogEntry objects that match all provided filters.
    """
    min_level = severity_level(min_severity) if min_severity else 0

    for line in lines:
        entry = parse_line(line)
        if entry is None:
            continue

        if start is not None and entry.timestamp < start:
            continue

        if end is not None and entry.timestamp > end:
            continue

        if severity_level(entry.severity) < min_level:
            continue

        yield entry


def slice_file(
    filepath: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    min_severity: Optional[str] = None,
) -> Iterator[LogEntry]:
    """Open a log file and yield matching entries without loading it fully.

    Args:
        filepath: Path to the log file.
        start: Inclusive lower bound for log timestamp.
        end: Inclusive upper bound for log timestamp.
        min_severity: Minimum severity level string.

    Yields:
        LogEntry objects matching all filters.
    """
    with open(filepath, "r", encoding="utf-8") as fh:
        yield from slice_logs(fh, start=start, end=end, min_severity=min_severity)
