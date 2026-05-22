"""Tail support: read the last N lines or bytes from a log file."""

from __future__ import annotations

import os
from typing import Iterator

from logslice.parser import LogEntry, parse_line

_DEFAULT_BLOCK = 8192


def tail_bytes(path: str, n_bytes: int) -> bytes:
    """Return the last *n_bytes* bytes of *path* without loading the whole file."""
    size = os.path.getsize(path)
    read_size = min(n_bytes, size)
    with open(path, "rb") as fh:
        fh.seek(max(0, size - read_size))
        return fh.read()


def tail_lines(path: str, n: int, encoding: str = "utf-8") -> list[str]:
    """Return the last *n* text lines of *path*.

    Uses a block-read strategy so only a small portion of the file is loaded
    even for very large files.
    """
    if n <= 0:
        return []

    size = os.path.getsize(path)
    if size == 0:
        return []

    collected: list[bytes] = []
    remaining = n + 1  # +1 to handle trailing newline
    pos = size

    with open(path, "rb") as fh:
        while pos > 0 and len(collected) < remaining:
            block_size = min(_DEFAULT_BLOCK, pos)
            pos -= block_size
            fh.seek(pos)
            block = fh.read(block_size)
            lines = block.split(b"\n")
            collected = lines + collected

    text_lines = [l.decode(encoding, errors="replace") for l in collected]
    # Drop empty trailing entry caused by final newline
    if text_lines and text_lines[-1] == "":
        text_lines = text_lines[:-1]

    return text_lines[-n:]


def tail_entries(path: str, n: int, encoding: str = "utf-8") -> Iterator[LogEntry]:
    """Yield the last *n* parseable :class:`~logslice.parser.LogEntry` objects."""
    lines = tail_lines(path, n, encoding=encoding)
    for line in lines:
        entry = parse_line(line)
        if entry is not None:
            yield entry
