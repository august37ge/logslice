"""Normalize log entries for consistent downstream processing.

Provides field normalization such as uppercasing severity, stripping
whitespace from messages, and optionally truncating long messages.
"""

from logslice.parser import LogEntry
from logslice.truncate import truncate_message, DEFAULT_MAX_LENGTH

KNOWN_SEVERITIES = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def normalize_severity(severity: str) -> str:
    """Uppercase and strip severity; keep as-is if unrecognized."""
    normalized = severity.strip().upper()
    return normalized if normalized in KNOWN_SEVERITIES else severity.strip()


def normalize_message(message: str, max_length: int | None = None) -> str:
    """Strip surrounding whitespace and optionally truncate the message."""
    cleaned = message.strip()
    if max_length is not None:
        cleaned = truncate_message(cleaned, max_length)
    return cleaned


def normalize_entry(
    entry: LogEntry,
    max_message_length: int | None = None,
) -> LogEntry:
    """Return a normalized copy of a LogEntry.

    - Severity is uppercased and stripped.
    - Message is stripped; optionally truncated to *max_message_length*.
    - Timestamp and raw line are preserved unchanged.
    """
    return LogEntry(
        timestamp=entry.timestamp,
        severity=normalize_severity(entry.severity),
        message=normalize_message(entry.message, max_message_length),
        raw=entry.raw,
    )


def normalize_entries(
    entries: list[LogEntry],
    max_message_length: int | None = None,
) -> list[LogEntry]:
    """Normalize a list of log entries.

    Args:
        entries: Iterable of LogEntry objects.
        max_message_length: If provided, messages longer than this are
            truncated to *max_message_length* characters (including ellipsis).

    Returns:
        New list of normalized LogEntry objects.
    """
    return [normalize_entry(e, max_message_length) for e in entries]
