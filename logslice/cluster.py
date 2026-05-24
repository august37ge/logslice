"""Cluster similar log entries by message pattern."""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

from logslice.parser import LogEntry

# Tokens that are replaced when building a cluster key
_VARIABLE_RE = re.compile(
    r"\b(?:"
    r"\d+\.\d+\.\d+\.\d+"  # IPv4
    r"|[0-9a-fA-F]{8}-[0-9a-fA-F-]{27}"  # UUID
    r"|\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"  # datetime
    r"|0x[0-9a-fA-F]+"  # hex
    r"|\d+"  # plain integers
    r")\b"
)


def _message_key(message: str) -> str:
    """Return a normalised key for clustering similar messages."""
    key = _VARIABLE_RE.sub("<VAR>", message)
    key = re.sub(r"\s+", " ", key).strip()
    return key


@dataclass
class Cluster:
    key: str
    entries: List[LogEntry] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.entries)

    @property
    def severities(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for e in self.entries:
            counts[e.severity] += 1
        return dict(counts)

    @property
    def representative(self) -> str:
        return self.entries[0].message if self.entries else ""


def cluster_entries(
    entries: Iterable[LogEntry],
    min_count: int = 1,
) -> List[Cluster]:
    """Group entries into clusters by normalised message pattern.

    Args:
        entries: Iterable of LogEntry objects.
        min_count: Only return clusters with at least this many entries.

    Returns:
        List of Cluster objects sorted by count descending.
    """
    buckets: Dict[str, Cluster] = {}
    for entry in entries:
        key = _message_key(entry.message)
        if key not in buckets:
            buckets[key] = Cluster(key=key)
        buckets[key].entries.append(entry)

    result = [c for c in buckets.values() if c.count >= min_count]
    result.sort(key=lambda c: c.count, reverse=True)
    return result


def format_cluster_report(clusters: List[Cluster]) -> List[str]:
    """Return a human-readable report of clusters."""
    if not clusters:
        return ["No clusters found."]
    lines: List[str] = []
    for i, cluster in enumerate(clusters, 1):
        sev_str = ", ".join(f"{k}:{v}" for k, v in sorted(cluster.severities.items()))
        lines.append(f"{i:>4}. [{cluster.count:>5}x] [{sev_str}] {cluster.representative[:80]}")
    return lines
