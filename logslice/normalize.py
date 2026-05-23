"""Normalize log entries: standardize severity labels and clean up messages."""

from __future__ import annotations

from typing import Iterable, Iterator

from logslice.parser import LogEntry

# Map common severity aliases to canonical names
_SEVERITY_ALIASES: dict[str, str] = {
    "warn": "WARNING",
    "warning": "WARNING",
    "err": "ERROR",
    "error": "ERROR",
    "crit": "CRITICAL",
    "critical": "CRITICAL",
    "info": "INFO",
    "information": "INFO",
    "dbg": "DEBUG",
    "debug": "DEBUG",
    "fatal": "CRITICAL",
    "trace": "DEBUG",
}


def normalize_severity(severity: str) -> str:
    """Return a canonical severity string for the given input.

    Unknown severities are returned uppercased but otherwise unchanged.
    """
    key = severity.strip().lower()
    return _SEVERITY_ALIASES.get(key, severity.strip().upper())


def normalize_message(message: str) -> str:
    """Strip leading/trailing whitespace and collapse internal runs of spaces."""
    stripped = message.strip()
    # Collapse multiple spaces into one
    import re
    return re.sub(r" {2,}", " ", stripped)


def normalize_entry(entry: LogEntry) -> LogEntry:
    """Return a new LogEntry with normalized severity and message."""
    return LogEntry(
        timestamp=entry.timestamp,
        severity=normalize_severity(entry.severity),
        message=normalize_message(entry.message),
        raw=entry.raw,
    )


def normalize_entries(entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
    """Yield normalized copies of each entry in *entries*."""
    for entry in entries:
        yield normalize_entry(entry)
