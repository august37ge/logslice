"""topology.py – build a source-to-severity dependency map from log entries."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Set, Tuple

from logslice.parser import LogEntry, severity_level


@dataclass
class TopologyNode:
    source: str
    severities: Set[str] = field(default_factory=set)
    entry_count: int = 0
    neighbours: Set[str] = field(default_factory=set)  # sources that appeared within window


def build_topology(
    entries: Iterable[LogEntry],
    window_seconds: int = 5,
) -> Dict[str, TopologyNode]:
    """Return a map of source -> TopologyNode.

    Two sources are considered neighbours when entries from them appear
    within *window_seconds* of each other (ordered by timestamp).
    """
    nodes: Dict[str, TopologyNode] = {}
    recent: List[Tuple[float, str]] = []  # (epoch, source)

    for entry in entries:
        src = entry.source or "unknown"
        if src not in nodes:
            nodes[src] = TopologyNode(source=src)
        node = nodes[src]
        node.severities.add(entry.severity)
        node.entry_count += 1

        ts = entry.timestamp.timestamp()
        cutoff = ts - window_seconds
        recent = [(t, s) for t, s in recent if t >= cutoff]

        for _, neighbour in recent:
            if neighbour != src:
                node.neighbours.add(neighbour)
                nodes[neighbour].neighbours.add(src)

        recent.append((ts, src))

    return nodes


def max_severity_for_source(node: TopologyNode) -> str:
    """Return the highest severity seen for a node."""
    if not node.severities:
        return "UNKNOWN"
    return max(node.severities, key=lambda s: severity_level(s))


def format_topology(nodes: Dict[str, TopologyNode]) -> str:
    """Render a human-readable topology summary."""
    if not nodes:
        return "(no entries)"
    lines: List[str] = []
    for src in sorted(nodes):
        node = nodes[src]
        top_sev = max_severity_for_source(node)
        neighbours = ", ".join(sorted(node.neighbours)) or "none"
        lines.append(
            f"{src}: entries={node.entry_count} max_severity={top_sev} neighbours=[{neighbours}]"
        )
    return "\n".join(lines)


def severity_distribution(nodes: Dict[str, TopologyNode]) -> Dict[str, Dict[str, int]]:
    """Return {source: {severity: count}} — counts are approximated from sets (presence only)."""
    # Full per-severity counts require a second pass; here we expose presence.
    return {src: {sev: 1 for sev in node.severities} for src, node in nodes.items()}
