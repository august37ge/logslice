"""Tests for logslice.playback."""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from logslice.parser import LogEntry
from logslice.playback import PlaybackConfig, run_playback


def _entry(ts: str, sev: str = "INFO", msg: str = "msg") -> LogEntry:
    dt = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    return LogEntry(timestamp=dt, severity=sev, message=msg, raw=f"{ts} {sev} {msg}")


def _run(entries, **kwargs):
    buf = io.StringIO()
    cfg = PlaybackConfig(output=buf, **kwargs)
    with patch("logslice.replay.time.sleep"):
        summary = run_playback(entries, cfg)
    return buf.getvalue(), summary


def test_dry_run_returns_summary_no_output():
    entries = [_entry("2024-01-01T00:00:00"), _entry("2024-01-01T00:00:05")]
    buf = io.StringIO()
    cfg = PlaybackConfig(output=buf, dry_run=True, speed=1.0)
    summary = run_playback(entries, cfg)
    assert summary["count"] == 2
    assert buf.getvalue() == ""


def test_plain_output_has_lines():
    entries = [_entry("2024-01-01T00:00:00"), _entry("2024-01-01T00:00:01")]
    out, summary = _run(entries, fmt="plain", speed=9999.0)
    lines = [l for l in out.splitlines() if l]
    assert len(lines) == 2


def test_json_output_is_parseable():
    entries = [_entry("2024-01-01T00:00:00", "ERROR", "boom")]
    out, _ = _run(entries, fmt="json", speed=9999.0)
    parsed = json.loads(out.strip())
    assert parsed["message"] == "boom"


def test_emitted_count_in_summary():
    entries = [_entry("2024-01-01T00:00:00"), _entry("2024-01-01T00:00:01")]
    _, summary = _run(entries, fmt="plain", speed=9999.0)
    assert summary["emitted"] == 2


def test_max_entries_limits_output():
    entries = [
        _entry("2024-01-01T00:00:00"),
        _entry("2024-01-01T00:00:01"),
        _entry("2024-01-01T00:00:02"),
    ]
    out, summary = _run(entries, fmt="plain", speed=9999.0, max_entries=2)
    lines = [l for l in out.splitlines() if l]
    assert len(lines) == 2
    assert summary["emitted"] == 2


def test_empty_entries_returns_zero_count():
    out, summary = _run([], fmt="plain", speed=1.0)
    assert summary["count"] == 0
    assert out == ""


def test_speed_reflected_in_summary():
    entries = [_entry("2024-01-01T00:00:00"), _entry("2024-01-01T00:00:10")]
    _, summary = _run(entries, fmt="plain", speed=2.0)
    assert summary["speed"] == 2.0
    assert summary["wall_duration_seconds"] == pytest.approx(5.0)
