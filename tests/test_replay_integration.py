"""Integration-style tests for replay timing behaviour."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import call, patch

from logslice.parser import LogEntry
from logslice.replay import replay_entries


def _entry(ts: str) -> LogEntry:
    dt = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    return LogEntry(timestamp=dt, severity="DEBUG", message="x", raw="x")


def test_sleep_called_between_entries():
    entries = [
        _entry("2024-06-01T00:00:00"),
        _entry("2024-06-01T00:00:02"),
    ]
    sleep_calls = []

    def fake_sleep(n):
        sleep_calls.append(n)

    with patch("logslice.replay.time.sleep", side_effect=fake_sleep):
        with patch("logslice.replay.time.monotonic", side_effect=[0.0, 0.0, 0.001]):
            list(replay_entries(entries, speed=1.0))

    assert len(sleep_calls) == 1
    assert sleep_calls[0] == pytest.approx(2.0 - 0.001, abs=1e-3)


def test_sleep_not_called_when_elapsed_exceeds_delay():
    """If processing already took longer than the delay, no sleep is issued."""
    entries = [
        _entry("2024-06-01T00:00:00"),
        _entry("2024-06-01T00:00:01"),
    ]
    # monotonic returns 0.0 at start, then 5.0 after first entry (already late)
    with patch("logslice.replay.time.sleep") as mock_sleep:
        with patch("logslice.replay.time.monotonic", side_effect=[0.0, 5.0, 5.0]):
            list(replay_entries(entries, speed=1.0))

    mock_sleep.assert_not_called()


def test_speed_halves_sleep_duration():
    entries = [
        _entry("2024-06-01T00:00:00"),
        _entry("2024-06-01T00:00:04"),
    ]
    sleep_calls = []

    with patch("logslice.replay.time.sleep", side_effect=lambda n: sleep_calls.append(n)):
        with patch("logslice.replay.time.monotonic", side_effect=[0.0, 0.0, 0.0]):
            list(replay_entries(entries, speed=2.0))

    assert len(sleep_calls) == 1
    assert sleep_calls[0] == pytest.approx(2.0, abs=1e-3)


import pytest
