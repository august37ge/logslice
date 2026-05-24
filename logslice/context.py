"""Context lines: yield log entries with surrounding lines for each match."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogEntry


@dataclass
class ContextEntry:
    """A matched entry together with its surrounding context lines."""

    entry: LogEntry
    before: List[LogEntry] = field(default_factory=list)
    after: List[LogEntry] = field(default_factory=list)

    @property
    def match_timestamp(self) -> str:
        return self.entry.timestamp


def with_context(
    entries: Iterable[LogEntry],
    predicate,
    before: int = 0,
    after: int = 0,
) -> Iterator[ContextEntry]:
    """Yield ContextEntry objects for every entry where predicate(entry) is True.

    Args:
        entries:   Source log entries (consumed once).
        predicate: Callable(LogEntry) -> bool that marks entries of interest.
        before:    Number of preceding entries to include.
        after:     Number of following entries to include.
    """
    if before < 0 or after < 0:
        raise ValueError("before and after must be non-negative")

    buf: deque[LogEntry] = deque(maxlen=before) if before > 0 else deque(maxlen=0)
    # pending: (ContextEntry, remaining_after_lines)
    pending: deque[tuple[ContextEntry, int]] = deque()

    for entry in entries:
        # Feed pending matches their "after" lines.
        still_pending: deque[tuple[ContextEntry, int]] = deque()
        for ctx, remaining in pending:
            ctx.after.append(entry)
            remaining -= 1
            if remaining > 0:
                still_pending.append((ctx, remaining))
            else:
                yield ctx
        pending = still_pending

        if predicate(entry):
            ctx = ContextEntry(
                entry=entry,
                before=list(buf),
            )
            if after == 0:
                yield ctx
            else:
                pending.append((ctx, after))

        buf.append(entry)

    # Flush any matches still waiting for after-lines.
    for ctx, _ in pending:
        yield ctx


def format_context_entry(ctx: ContextEntry, separator: str = "--") -> List[str]:
    """Return a list of formatted lines for a ContextEntry."""
    lines: List[str] = []
    for e in ctx.before:
        lines.append(f"  {e.timestamp} [{e.severity}] {e.message}")
    lines.append(f"> {ctx.entry.timestamp} [{ctx.entry.severity}] {ctx.entry.message}")
    for e in ctx.after:
        lines.append(f"  {e.timestamp} [{e.severity}] {e.message}")
    if separator:
        lines.append(separator)
    return lines
