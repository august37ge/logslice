"""Baseline comparison: capture a snapshot of log statistics and compare
against a later run to detect regressions or anomalies."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Iterable, Optional

from logslice.parser import LogEntry


@dataclass
class BaselineSnapshot:
    total: int = 0
    severity_counts: Dict[str, int] = field(default_factory=dict)
    earliest: Optional[str] = None
    latest: Optional[str] = None


@dataclass
class BaselineDiff:
    total_delta: int
    added_severities: Dict[str, int]
    removed_severities: Dict[str, int]
    changed_severities: Dict[str, int]  # severity -> delta


def capture(entries: Iterable[LogEntry]) -> BaselineSnapshot:
    """Build a snapshot from an iterable of log entries."""
    snap = BaselineSnapshot()
    for entry in entries:
        snap.total += 1
        sev = entry.severity.upper()
        snap.severity_counts[sev] = snap.severity_counts.get(sev, 0) + 1
        ts = entry.timestamp.isoformat()
        if snap.earliest is None or ts < snap.earliest:
            snap.earliest = ts
        if snap.latest is None or ts > snap.latest:
            snap.latest = ts
    return snap


def compare(old: BaselineSnapshot, new: BaselineSnapshot) -> BaselineDiff:
    """Compare two snapshots and return the diff."""
    old_sevs = old.severity_counts
    new_sevs = new.severity_counts
    all_keys = set(old_sevs) | set(new_sevs)

    added: Dict[str, int] = {}
    removed: Dict[str, int] = {}
    changed: Dict[str, int] = {}

    for key in all_keys:
        o = old_sevs.get(key, 0)
        n = new_sevs.get(key, 0)
        if o == 0 and n > 0:
            added[key] = n
        elif n == 0 and o > 0:
            removed[key] = o
        elif o != n:
            changed[key] = n - o

    return BaselineDiff(
        total_delta=new.total - old.total,
        added_severities=added,
        removed_severities=removed,
        changed_severities=changed,
    )


def save_baseline(snapshot: BaselineSnapshot, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(snapshot), indent=2))


def load_baseline(path: Path) -> BaselineSnapshot:
    data = json.loads(path.read_text())
    return BaselineSnapshot(**data)


def format_diff(diff: BaselineDiff) -> str:
    lines = [f"Total delta: {diff.total_delta:+d}"]
    for sev, count in sorted(diff.added_severities.items()):
        lines.append(f"  + {sev}: {count} (new)")
    for sev, count in sorted(diff.removed_severities.items()):
        lines.append(f"  - {sev}: {count} (gone)")
    for sev, delta in sorted(diff.changed_severities.items()):
        lines.append(f"  ~ {sev}: {delta:+d}")
    if not (diff.added_severities or diff.removed_severities or diff.changed_severities):
        lines.append("  No severity changes.")
    return "\n".join(lines)
