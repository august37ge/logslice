"""Output sink utilities — write rendered log lines to files or stdout."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Optional, TextIO


def write_lines(
    lines: Iterable[str],
    destination: Optional[Path] = None,
    *,
    append: bool = False,
) -> int:
    """Write *lines* to *destination* (or stdout when None).

    Returns the number of lines written.
    """
    count = 0
    if destination is None:
        stream: TextIO = sys.stdout
        for line in lines:
            stream.write(line + "\n")
            count += 1
    else:
        mode = "a" if append else "w"
        with destination.open(mode, encoding="utf-8") as fh:
            for line in lines:
                fh.write(line + "\n")
                count += 1
    return count


def write_to_stream(lines: Iterable[str], stream: TextIO) -> int:
    """Write *lines* to an arbitrary text stream.  Returns lines written."""
    count = 0
    for line in lines:
        stream.write(line + "\n")
        count += 1
    return count
