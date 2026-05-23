"""Utilities for truncating long log messages in output."""

from typing import Optional
from logslice.parser import LogEntry

DEFAULT_MAX_LENGTH = 200
ELLIPSIS = "..."


def truncate_message(message: str, max_length: int = DEFAULT_MAX_LENGTH) -> str:
    """Truncate a message to max_length characters, appending ellipsis if needed."""
    if max_length < len(ELLIPSIS):
        raise ValueError(f"max_length must be at least {len(ELLIPSIS)}")
    if len(message) <= max_length:
        return message
    return message[: max_length - len(ELLIPSIS)] + ELLIPSIS


def truncate_entry(
    entry: LogEntry, max_length: int = DEFAULT_MAX_LENGTH
) -> LogEntry:
    """Return a new LogEntry with its message truncated to max_length."""
    truncated = truncate_message(entry.message, max_length)
    return LogEntry(
        timestamp=entry.timestamp,
        severity=entry.severity,
        message=truncated,
        raw=entry.raw,
    )


def truncate_entries(
    entries: list[LogEntry],
    max_length: int = DEFAULT_MAX_LENGTH,
    only_if_longer: Optional[int] = None,
) -> list[LogEntry]:
    """Truncate messages in a list of entries.

    Args:
        entries: Source log entries.
        max_length: Maximum message length after truncation.
        only_if_longer: If set, only truncate entries whose message exceeds
            this threshold (useful to leave short messages untouched).

    Returns:
        List of (possibly new) LogEntry objects.
    """
    result = []
    for entry in entries:
        threshold = only_if_longer if only_if_longer is not None else max_length
        if len(entry.message) > threshold:
            result.append(truncate_entry(entry, max_length))
        else:
            result.append(entry)
    return result
