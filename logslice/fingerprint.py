"""Log entry fingerprinting — generate stable hashes for dedup and correlation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable, Iterator

from logslice.parser import LogEntry

# Tokens to strip before hashing so that dynamic values don't affect the key
_STRIP_PATTERNS = [
    re.compile(r'\b\d{1,3}(?:\.\d{1,3}){3}\b'),   # IPv4
    re.compile(r'\b[0-9a-fA-F]{8,}\b'),             # hex ids / hashes
    re.compile(r'\b\d+\b'),                          # plain integers
    re.compile(r'"[^"]*"'),                          # quoted strings
    re.compile(r"'[^']*'"),                           # single-quoted strings
]

_WHITESPACE = re.compile(r'\s+')


def _normalise(message: str) -> str:
    """Replace dynamic tokens with placeholders and collapse whitespace."""
    text = message
    for pat in _STRIP_PATTERNS:
        text = pat.sub('<X>', text)
    return _WHITESPACE.sub(' ', text).strip().lower()


def fingerprint_message(message: str) -> str:
    """Return a short hex fingerprint for a log message."""
    normalised = _normalise(message)
    return hashlib.sha1(normalised.encode()).hexdigest()[:16]


def fingerprint_entry(entry: LogEntry) -> str:
    """Return a fingerprint that captures severity + normalised message."""
    key = f"{entry.severity.upper()}:{_normalise(entry.message)}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]


@dataclass
class FingerprintedEntry:
    entry: LogEntry
    fingerprint: str


def fingerprint_entries(
    entries: Iterable[LogEntry],
) -> Iterator[FingerprintedEntry]:
    """Attach a fingerprint to every entry in *entries*."""
    for entry in entries:
        yield FingerprintedEntry(entry=entry, fingerprint=fingerprint_entry(entry))


def group_by_fingerprint(
    entries: Iterable[LogEntry],
) -> dict[str, list[LogEntry]]:
    """Group entries by their fingerprint."""
    groups: dict[str, list[LogEntry]] = {}
    for entry in entries:
        fp = fingerprint_entry(entry)
        groups.setdefault(fp, []).append(entry)
    return groups


def format_fingerprint_report(groups: dict[str, list[LogEntry]]) -> str:
    """Return a human-readable summary of fingerprint groups."""
    if not groups:
        return "No entries."
    lines = [f"{'Fingerprint':<18} {'Count':>6}  Representative message"]
    lines.append("-" * 72)
    for fp, entries in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        rep = entries[0].message[:48]
        lines.append(f"{fp:<18} {len(entries):>6}  {rep}")
    return "\n".join(lines)
