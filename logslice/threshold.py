"""Threshold configuration: load and validate alert rules from a dict/TOML."""
from __future__ import annotations

from typing import Any, Dict, List

from logslice.alert import AlertRule


class ThresholdConfigError(ValueError):
    """Raised when a threshold configuration is invalid."""


_REQUIRED = ("name", "severity", "threshold")
_VALID_SEVERITIES = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def _validate_rule(raw: Dict[str, Any], index: int) -> AlertRule:
    """Parse and validate a single raw rule dict."""
    for key in _REQUIRED:
        if key not in raw:
            raise ThresholdConfigError(
                f"Rule at index {index} is missing required field '{key}'"
            )
    name = str(raw["name"])
    severity = str(raw["severity"]).upper()
    if severity not in _VALID_SEVERITIES:
        raise ThresholdConfigError(
            f"Rule '{name}': unknown severity '{severity}'. "
            f"Valid values: {sorted(_VALID_SEVERITIES)}"
        )
    threshold = int(raw["threshold"])
    if threshold < 1:
        raise ThresholdConfigError(
            f"Rule '{name}': threshold must be >= 1, got {threshold}"
        )
    window_seconds = float(raw.get("window_seconds", 60.0))
    if window_seconds <= 0:
        raise ThresholdConfigError(
            f"Rule '{name}': window_seconds must be > 0, got {window_seconds}"
        )
    message_contains = raw.get("message_contains") or None
    return AlertRule(
        name=name,
        severity=severity,
        threshold=threshold,
        window_seconds=window_seconds,
        message_contains=message_contains,
    )


def load_rules(data: Dict[str, Any]) -> List[AlertRule]:
    """Load alert rules from a configuration mapping.

    Expected shape::

        {"rules": [{"name": ..., "severity": ..., "threshold": ...}, ...]}

    Returns a list of :class:`~logslice.alert.AlertRule` objects.
    """
    raw_rules = data.get("rules", [])
    if not isinstance(raw_rules, list):
        raise ThresholdConfigError("'rules' must be a list")
    return [_validate_rule(r, i) for i, r in enumerate(raw_rules)]


def rules_to_dict(rules: List[AlertRule]) -> Dict[str, Any]:
    """Serialise *rules* back to a plain dict (round-trip helper)."""
    return {
        "rules": [
            {
                "name": r.name,
                "severity": r.severity,
                "threshold": r.threshold,
                "window_seconds": r.window_seconds,
                **(  # omit key when None for cleaner output
                    {"message_contains": r.message_contains}
                    if r.message_contains is not None
                    else {}
                ),
            }
            for r in rules
        ]
    }
