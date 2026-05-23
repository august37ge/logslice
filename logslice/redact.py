"""Redaction utilities for masking sensitive patterns in log entries."""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from logslice.parser import LogEntry

# Built-in patterns for common sensitive data
DEFAULT_PATTERNS: List[str] = [
    r"(?i)password=[^\s&]+",
    r"(?i)token=[^\s&]+",
    r"(?i)secret=[^\s&]+",
    r"\b(?:\d{4}[- ]?){3}\d{4}\b",  # credit card
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",  # email
]

REDACT_PLACEHOLDER = "[REDACTED]"


@dataclass
class RedactConfig:
    patterns: List[str] = field(default_factory=list)
    placeholder: str = REDACT_PLACEHOLDER
    use_defaults: bool = True


def _compile_patterns(config: RedactConfig) -> List[re.Pattern]:
    """Compile all active patterns into regex objects."""
    sources = list(DEFAULT_PATTERNS) if config.use_defaults else []
    sources.extend(config.patterns)
    compiled = []
    for pat in sources:
        try:
            compiled.append(re.compile(pat))
        except re.error as exc:
            raise ValueError(f"Invalid redaction pattern {pat!r}: {exc}") from exc
    return compiled


def redact_message(message: str, config: Optional[RedactConfig] = None) -> str:
    """Return *message* with all sensitive patterns replaced by the placeholder."""
    if config is None:
        config = RedactConfig()
    compiled = _compile_patterns(config)
    result = message
    for pattern in compiled:
        result = pattern.sub(config.placeholder, result)
    return result


def redact_entry(entry: LogEntry, config: Optional[RedactConfig] = None) -> LogEntry:
    """Return a new LogEntry with the message field redacted."""
    new_message = redact_message(entry.message, config)
    return LogEntry(
        timestamp=entry.timestamp,
        severity=entry.severity,
        message=new_message,
        raw=entry.raw,
    )


def redact_entries(
    entries: List[LogEntry], config: Optional[RedactConfig] = None
) -> List[LogEntry]:
    """Redact a list of log entries in place (returns new list)."""
    return [redact_entry(e, config) for e in entries]
