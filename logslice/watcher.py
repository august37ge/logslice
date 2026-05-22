"""Simple file-tail watcher: yields new log entries appended to a file.

Designed for short-lived polling use-cases (e.g. ``logslice --follow``).
For production use consider pairing with inotify / kqueue.
"""

from __future__ import annotations

import time
from typing import Iterator

from logslice.parser import LogEntry, parse_line


def follow(
    path: str,
    poll_interval: float = 0.25,
    encoding: str = "utf-8",
    max_iterations: int | None = None,
) -> Iterator[LogEntry]:
    """Yield :class:`~logslice.parser.LogEntry` objects as they are appended.

    Parameters
    ----------
    path:
        Path to the log file to watch.
    poll_interval:
        Seconds to sleep between read attempts.
    encoding:
        File encoding.
    max_iterations:
        Stop after this many poll cycles (``None`` = run forever).
        Useful for testing.
    """
    with open(path, "r", encoding=encoding, errors="replace") as fh:
        # Seek to end so we only see *new* content.
        fh.seek(0, 2)

        iterations = 0
        while max_iterations is None or iterations < max_iterations:
            line = fh.readline()
            if line:
                entry = parse_line(line.rstrip("\n"))
                if entry is not None:
                    yield entry
            else:
                time.sleep(poll_interval)
                iterations += 1
