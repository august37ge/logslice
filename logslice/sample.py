"""Reservoir and fixed-interval sampling of log entries."""

from __future__ import annotations

import random
from typing import Iterable, Iterator, List

from logslice.parser import LogEntry


def sample_every_n(entries: Iterable[LogEntry], n: int) -> Iterator[LogEntry]:
    """Yield every *n*-th entry (1-based).  n=1 returns all entries."""
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    for i, entry in enumerate(entries):
        if i % n == 0:
            yield entry


def reservoir_sample(entries: Iterable[LogEntry], k: int, seed: int | None = None) -> List[LogEntry]:
    """Return up to *k* entries chosen uniformly at random (reservoir algorithm).

    The relative order of selected entries is preserved.
    """
    if k < 0:
        raise ValueError(f"k must be >= 0, got {k}")
    rng = random.Random(seed)
    reservoir: List[LogEntry] = []
    for i, entry in enumerate(entries):
        if len(reservoir) < k:
            reservoir.append(entry)
        else:
            j = rng.randint(0, i)
            if j < k:
                reservoir[j] = entry
    # Sort by timestamp to restore chronological order.
    reservoir.sort(key=lambda e: e.timestamp)
    return reservoir


def sample_by_rate(entries: Iterable[LogEntry], rate: float, seed: int | None = None) -> Iterator[LogEntry]:
    """Yield each entry independently with probability *rate* (0.0–1.0)."""
    if not 0.0 <= rate <= 1.0:
        raise ValueError(f"rate must be between 0.0 and 1.0, got {rate}")
    rng = random.Random(seed)
    for entry in entries:
        if rng.random() < rate:
            yield entry
