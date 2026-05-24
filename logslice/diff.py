"""Log diff: compare two sequences of log entries and report additions/removals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, List, Tuple

from logslice.parser import LogEntry


@dataclass
class DiffEntry:
    """A single diff result line."""
    tag: str          # '+' added, '-' removed, '=' unchanged
    entry: LogEntry


def _entry_key(entry: LogEntry) -> Tuple[str, str]:
    """Identity key used for matching entries across two logs."""
    return (entry.severity.upper(), entry.message.strip())


def diff_entries(
    left: Iterable[LogEntry],
    right: Iterable[LogEntry],
) -> List[DiffEntry]:
    """Compare *left* (old) vs *right* (new) log entries.

    Uses a key-based diff: entries present only in *left* are marked '-',
    entries present only in *right* are marked '+', and entries present in
    both (by key) are marked '='.

    Order within each group follows the original sequence.
    """
    left_list = list(left)
    right_list = list(right)

    left_keys = [_entry_key(e) for e in left_list]
    right_keys = [_entry_key(e) for e in right_list]

    right_key_set = set(right_keys)
    left_key_set = set(left_keys)

    result: List[DiffEntry] = []

    for entry, key in zip(left_list, left_keys):
        tag = '=' if key in right_key_set else '-'
        result.append(DiffEntry(tag=tag, entry=entry))

    for entry, key in zip(right_list, right_keys):
        if key not in left_key_set:
            result.append(DiffEntry(tag='+', entry=entry))

    return result


def iter_diff(
    left: Iterable[LogEntry],
    right: Iterable[LogEntry],
) -> Iterator[DiffEntry]:
    """Streaming variant — yields DiffEntry objects one at a time."""
    yield from diff_entries(left, right)


def format_diff(diff: Iterable[DiffEntry]) -> List[str]:
    """Render diff entries as human-readable lines with a leading tag."""
    lines: List[str] = []
    for d in diff:
        prefix = {'+': '+ ', '-': '- ', '=': '  '}.get(d.tag, '  ')
        lines.append(
            f"{prefix}{d.entry.timestamp} [{d.entry.severity}] {d.entry.message}"
        )
    return lines
