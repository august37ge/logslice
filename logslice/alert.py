"""Alert rules: evaluate log entries against threshold conditions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from logslice.parser import LogEntry, severity_level


@dataclass
class AlertRule:
    """A single alert rule definition."""
    name: str
    severity: str                  # minimum severity to match
    threshold: int                 # number of matching entries to trigger
    window_seconds: float = 60.0   # rolling window in seconds
    message_contains: Optional[str] = None


@dataclass
class AlertEvent:
    """Fired when a rule threshold is breached."""
    rule_name: str
    count: int
    threshold: int
    window_seconds: float
    matching_entries: List[LogEntry] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"ALERT '{self.rule_name}': {self.count} entries "
            f"(threshold={self.threshold}) in {self.window_seconds}s window"
        )


def _entry_matches_rule(entry: LogEntry, rule: AlertRule) -> bool:
    """Return True if *entry* satisfies the rule's severity and message filter."""
    if severity_level(entry.severity) < severity_level(rule.severity):
        return False
    if rule.message_contains and rule.message_contains not in entry.message:
        return False
    return True


def evaluate_rule(
    entries: Iterable[LogEntry],
    rule: AlertRule,
) -> Optional[AlertEvent]:
    """Evaluate *entries* against *rule* using a sliding window.

    Returns an :class:`AlertEvent` if the threshold is breached, else ``None``.
    Entries must be in chronological order.
    """
    from collections import deque

    window: deque[LogEntry] = deque()
    for entry in entries:
        if not _entry_matches_rule(entry, rule):
            continue
        window.append(entry)
        # Evict entries outside the rolling window
        cutoff = entry.timestamp.timestamp() - rule.window_seconds
        while window and window[0].timestamp.timestamp() < cutoff:
            window.popleft()
        if len(window) >= rule.threshold:
            return AlertEvent(
                rule_name=rule.name,
                count=len(window),
                threshold=rule.threshold,
                window_seconds=rule.window_seconds,
                matching_entries=list(window),
            )
    return None


def evaluate_rules(
    entries: Iterable[LogEntry],
    rules: List[AlertRule],
) -> List[AlertEvent]:
    """Evaluate a list of *rules* against *entries*.

    Each rule is evaluated independently over a fresh copy of the entry stream.
    """
    entries_list = list(entries)
    events: List[AlertEvent] = []
    for rule in rules:
        event = evaluate_rule(iter(entries_list), rule)
        if event is not None:
            events.append(event)
    return events
