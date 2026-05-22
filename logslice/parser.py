"""Log line parser: extracts timestamp and severity from a log line."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Matches lines like: 2024-01-15 12:34:56,789 [ERROR] Some message
# or:                 2024-01-15T12:34:56 ERROR Some message
LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[,.]\d+)?)"
    r"\s+[\[\(]?(?P<severity>DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)[\]\)]?"
    r"\s+(?P<message>.*)$",
    re.IGNORECASE,
)

SEVERITY_ORDER = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "WARN": 2,
    "ERROR": 3,
    "CRITICAL": 4,
    "FATAL": 4,
}


@dataclass
class LogEntry:
    timestamp: datetime
    severity: str
    message: str
    raw: str

    @property
    def severity_level(self) -> int:
        return SEVERITY_ORDER.get(self.severity.upper(), -1)


def parse_timestamp(ts_str: str) -> datetime:
    """Parse a timestamp string into a datetime object."""
    ts_str = ts_str.replace(",", ".").replace(" ", "T")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognised timestamp format: {ts_str!r}")


def parse_line(line: str) -> Optional[LogEntry]:
    """Parse a single log line. Returns None if the line doesn't match."""
    line = line.rstrip("\n")
    match = LOG_PATTERN.match(line)
    if not match:
        return None
    try:
        ts = parse_timestamp(match.group("timestamp"))
    except ValueError:
        return None
    severity = match.group("severity").upper()
    if severity == "WARN":
        severity = "WARNING"
    if severity == "FATAL":
        severity = "CRITICAL"
    return LogEntry(
        timestamp=ts,
        severity=severity,
        message=match.group("message"),
        raw=line,
    )
