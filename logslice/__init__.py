"""logslice — Fast log file slicer that filters by time range and severity."""

from logslice.parser import LogEntry, parse_line, SEVERITY_ORDER

__all__ = ["LogEntry", "parse_line", "SEVERITY_ORDER"]
__version__ = "0.1.0"
