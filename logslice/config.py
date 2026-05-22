"""Configuration loading and validation for logslice."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_CONFIG_PATHS = [
    ".logslice.json",
    os.path.expanduser("~/.logslice.json"),
]

VALID_FORMATS = {"plain", "colored", "json"}
VALID_SEVERITIES = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclass
class LogSliceConfig:
    """Holds default settings loaded from a config file."""

    format: str = "plain"
    min_severity: Optional[str] = None
    output_file: Optional[str] = None
    append: bool = False
    show_stats: bool = False
    extra: dict = field(default_factory=dict)


class ConfigError(ValueError):
    """Raised when the configuration file contains invalid values."""


def _validate(data: dict) -> None:
    """Raise ConfigError if any known field has an invalid value."""
    fmt = data.get("format")
    if fmt is not None and fmt not in VALID_FORMATS:
        raise ConfigError(
            f"Invalid format {fmt!r}. Must be one of {sorted(VALID_FORMATS)}."
        )

    sev = data.get("min_severity")
    if sev is not None and sev.upper() not in VALID_SEVERITIES:
        raise ConfigError(
            f"Invalid min_severity {sev!r}. Must be one of {sorted(VALID_SEVERITIES)}."
        )


def load_config(path: Optional[str] = None) -> LogSliceConfig:
    """Load configuration from *path* or the first default path that exists.

    Returns a default :class:`LogSliceConfig` when no file is found.
    """
    candidates = [path] if path else DEFAULT_CONFIG_PATHS

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            with open(candidate, "r", encoding="utf-8") as fh:
                try:
                    data = json.load(fh)
                except json.JSONDecodeError as exc:
                    raise ConfigError(f"Cannot parse config file {candidate!r}: {exc}") from exc

            _validate(data)

            known = {"format", "min_severity", "output_file", "append", "show_stats"}
            extra = {k: v for k, v in data.items() if k not in known}

            return LogSliceConfig(
                format=data.get("format", "plain"),
                min_severity=data.get("min_severity"),
                output_file=data.get("output_file"),
                append=bool(data.get("append", False)),
                show_stats=bool(data.get("show_stats", False)),
                extra=extra,
            )

    return LogSliceConfig()
