"""High-level baseline report: capture, compare, and render a human-readable
or JSON summary of changes between two log snapshots."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Optional

from logslice.baseline import (
    BaselineDiff,
    BaselineSnapshot,
    capture,
    compare,
    format_diff,
    load_baseline,
    save_baseline,
)
from logslice.parser import LogEntry


def build_and_compare(
    entries: Iterable[LogEntry],
    baseline_path: Path,
    *,
    update: bool = False,
) -> Optional[BaselineDiff]:
    """Capture a snapshot from *entries*.

    If *baseline_path* exists, compare against it and return the diff.
    If *update* is True (or no baseline exists yet), save the new snapshot.
    Returns None when there is no previous baseline to compare against.
    """
    new_snap = capture(entries)

    if baseline_path.exists():
        old_snap = load_baseline(baseline_path)
        diff = compare(old_snap, new_snap)
        if update:
            save_baseline(new_snap, baseline_path)
        return diff

    save_baseline(new_snap, baseline_path)
    return None


def format_baseline_report(
    diff: Optional[BaselineDiff],
    *,
    fmt: str = "plain",
) -> str:
    """Render *diff* as plain text or JSON.

    If *diff* is None (first run), return an informational message.
    """
    if diff is None:
        if fmt == "json":
            return json.dumps({"status": "baseline_created"})
        return "Baseline created. Run again to compare."

    if fmt == "json":
        return json.dumps(asdict(diff), indent=2)

    return format_diff(diff)


def regression_detected(diff: Optional[BaselineDiff], *, severity: str = "ERROR") -> bool:
    """Return True if *diff* shows an increase in *severity* entries."""
    if diff is None:
        return False
    sev = severity.upper()
    delta = diff.changed_severities.get(sev, 0)
    added = diff.added_severities.get(sev, 0)
    return delta > 0 or added > 0
