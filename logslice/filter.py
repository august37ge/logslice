"""Field-based filtering for log entries."""

from __future__ import annotations

import re
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogEntry


class FilterConfig:
    """Holds criteria for filtering log entries."""

    def __init__(
        self,
        severities: Optional[List[str]] = None,
        message_pattern: Optional[str] = None,
        source_pattern: Optional[str] = None,
        ignore_case: bool = True,
    ) -> None:
        self.severities = [s.upper() for s in severities] if severities else []
        self.message_pattern = message_pattern
        self.source_pattern = source_pattern
        self.ignore_case = ignore_case

        flags = re.IGNORECASE if ignore_case else 0
        self._msg_re = re.compile(message_pattern, flags) if message_pattern else None
        self._src_re = re.compile(source_pattern, flags) if source_pattern else None


def _matches(entry: LogEntry, cfg: FilterConfig) -> bool:
    """Return True if *entry* satisfies every criterion in *cfg*."""
    if cfg.severities and entry.severity.upper() not in cfg.severities:
        return False
    if cfg._msg_re and not cfg._msg_re.search(entry.message):
        return False
    if cfg._src_re:
        source = entry.extra.get("source", "")
        if not cfg._src_re.search(source):
            return False
    return True


def filter_entries(
    entries: Iterable[LogEntry],
    cfg: FilterConfig,
) -> Iterator[LogEntry]:
    """Yield entries that match *cfg*."""
    for entry in entries:
        if _matches(entry, cfg):
            yield entry


def filter_by_severity(
    entries: Iterable[LogEntry],
    severities: List[str],
) -> Iterator[LogEntry]:
    """Convenience wrapper — filter by severity list only."""
    cfg = FilterConfig(severities=severities)
    return filter_entries(entries, cfg)
