"""Human-readable alert report: summarise AlertEvents for display."""
from __future__ import annotations

from typing import List

from logslice.alert import AlertEvent


def format_alert_event(event: AlertEvent, *, show_entries: bool = False) -> str:
    """Format a single *event* as a multi-line string."""
    lines = [
        f"[ALERT] {event.rule_name}",
        f"  Triggered : {event.count} entries >= threshold {event.threshold}"
        f" within {event.window_seconds}s",
    ]
    if show_entries:
        lines.append("  Matching entries:")
        for entry in event.matching_entries:
            lines.append(f"    {entry.raw}")
    return "\n".join(lines)


def format_alert_report(
    events: List[AlertEvent],
    *,
    show_entries: bool = False,
) -> str:
    """Format all *events* as a single report string.

    Returns a placeholder message when *events* is empty.
    """
    if not events:
        return "No alerts triggered."
    sections = [format_alert_event(e, show_entries=show_entries) for e in events]
    header = f"=== Alert Report: {len(events)} alert(s) triggered ==="
    return "\n\n".join([header] + sections)


def alert_summary(events: List[AlertEvent]) -> dict:
    """Return a compact summary dict suitable for JSON serialisation."""
    return {
        "total_alerts": len(events),
        "alerts": [
            {
                "rule": e.rule_name,
                "count": e.count,
                "threshold": e.threshold,
                "window_seconds": e.window_seconds,
            }
            for e in events
        ],
    }
