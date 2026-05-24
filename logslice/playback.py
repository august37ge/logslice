"""High-level playback controller combining replay with formatting and output."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import IO, Iterable, Optional

from logslice.formatter import get_formatter
from logslice.parser import LogEntry
from logslice.replay import replay_entries, replay_summary


@dataclass
class PlaybackConfig:
    speed: float = 1.0
    fmt: str = "plain"  # plain | colored | json
    output: IO = field(default_factory=lambda: sys.stdout)
    dry_run: bool = False  # summarise without replaying
    max_entries: Optional[int] = None


def run_playback(entries: Iterable[LogEntry], config: PlaybackConfig) -> dict:
    """Replay *entries* according to *config*.

    Returns a summary dict with counts and timing information.
    """
    entry_list = list(entries)
    if config.max_entries is not None:
        entry_list = entry_list[: config.max_entries]

    if config.dry_run:
        return replay_summary(entry_list, speed=config.speed)

    formatter = get_formatter(config.fmt)
    emitted = 0

    def _emit(entry: LogEntry) -> None:
        nonlocal emitted
        line = formatter(entry)
        config.output.write(line + "\n")
        emitted += 1

    # Consume the generator to drive the replay
    for _ in replay_entries(entry_list, speed=config.speed, on_entry=_emit):
        pass

    summary = replay_summary(entry_list, speed=config.speed)
    summary["emitted"] = emitted
    return summary
