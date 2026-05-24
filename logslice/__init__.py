"""logslice — Fast log file slicer that filters by time range and severity."""

from logslice.parser import LogEntry, parse_line, SEVERITY_ORDER

__all__ = ["LogEntry", "parse_line", "SEVERITY_ORDER", "slice_logs"]
__version__ = "0.1.0"


def slice_logs(lines, min_severity=None, start_time=None, end_time=None):
    """Filter log lines by time range and/or minimum severity level.

    Args:
        lines: Iterable of raw log line strings.
        min_severity: Minimum severity string (e.g. ``"WARNING"``). Lines
            below this level are excluded. ``None`` disables filtering.
        start_time: Inclusive lower bound as a :class:`datetime.datetime`.
            ``None`` means no lower bound.
        end_time: Inclusive upper bound as a :class:`datetime.datetime`.
            ``None`` means no upper bound.

    Yields:
        :class:`~logslice.parser.LogEntry` objects that match all criteria.
    """
    min_level = SEVERITY_ORDER.get(min_severity, 0) if min_severity else 0

    for line in lines:
        entry = parse_line(line)
        if entry is None:
            continue
        if start_time and entry.timestamp < start_time:
            continue
        if end_time and entry.timestamp > end_time:
            continue
        if min_severity and SEVERITY_ORDER.get(entry.severity, 0) < min_level:
            continue
        yield entry
