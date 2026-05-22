"""Output formatters for log entries."""

from __future__ import annotations

import json
from typing import Iterable

from logslice.parser import LogEntry

_SEVERITY_COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[35m",
}
_RESET = "\033[0m"


def format_plain(entry: LogEntry) -> str:
    """Return a plain-text representation of a log entry."""
    return f"[{entry.timestamp.isoformat()}] [{entry.severity}] {entry.message}"


def format_colored(entry: LogEntry) -> str:
    """Return an ANSI-colored representation of a log entry."""
    color = _SEVERITY_COLORS.get(entry.severity, "")
    severity_str = f"{color}[{entry.severity}]{_RESET}" if color else f"[{entry.severity}]"
    return f"[{entry.timestamp.isoformat()}] {severity_str} {entry.message}"


def format_json(entry: LogEntry) -> str:
    """Return a JSON representation of a log entry."""
    return json.dumps(
        {
            "timestamp": entry.timestamp.isoformat(),
            "severity": entry.severity,
            "message": entry.message,
        }
    )


_FORMATTERS = {
    "plain": format_plain,
    "colored": format_colored,
    "json": format_json,
}


def get_formatter(name: str):
    """Return a formatter callable by name, raising ValueError for unknown names."""
    try:
        return _FORMATTERS[name]
    except KeyError:
        valid = ", ".join(sorted(_FORMATTERS))
        raise ValueError(f"Unknown formatter {name!r}. Valid options: {valid}")


def render_entries(entries: Iterable[LogEntry], fmt: str = "plain") -> Iterable[str]:
    """Yield formatted strings for each log entry."""
    formatter = get_formatter(fmt)
    for entry in entries:
        yield formatter(entry)
