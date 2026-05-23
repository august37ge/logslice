"""Tests for logslice.sample."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.sample import reservoir_sample, sample_by_rate, sample_every_n


def _entry(msg: str, ts: datetime | None = None) -> LogEntry:
    if ts is None:
        ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return LogEntry(timestamp=ts, severity="INFO", message=msg, raw=f"2024-01-01T12:00:00Z INFO {msg}")


def _entries(n: int) -> List[LogEntry]:
    return [_entry(f"msg-{i}") for i in range(n)]


# --- sample_every_n ---

def test_sample_every_n_n1_returns_all():
    entries = _entries(6)
    result = list(sample_every_n(entries, 1))
    assert result == entries


def test_sample_every_n_n2_returns_half():
    entries = _entries(6)
    result = list(sample_every_n(entries, 2))
    assert len(result) == 3
    assert result == entries[::2]


def test_sample_every_n_n3():
    entries = _entries(9)
    result = list(sample_every_n(entries, 3))
    assert len(result) == 3


def test_sample_every_n_raises_on_zero():
    with pytest.raises(ValueError):
        list(sample_every_n(_entries(5), 0))


def test_sample_every_n_empty_input():
    assert list(sample_every_n([], 2)) == []


# --- reservoir_sample ---

def test_reservoir_sample_k_larger_than_population_returns_all():
    entries = _entries(4)
    result = reservoir_sample(entries, k=10, seed=0)
    assert len(result) == 4


def test_reservoir_sample_k_zero_returns_empty():
    result = reservoir_sample(_entries(10), k=0, seed=0)
    assert result == []


def test_reservoir_sample_returns_k_items():
    entries = _entries(100)
    result = reservoir_sample(entries, k=10, seed=42)
    assert len(result) == 10


def test_reservoir_sample_raises_on_negative_k():
    with pytest.raises(ValueError):
        reservoir_sample(_entries(5), k=-1)


def test_reservoir_sample_is_deterministic_with_seed():
    entries = _entries(50)
    r1 = reservoir_sample(entries, k=5, seed=7)
    r2 = reservoir_sample(entries, k=5, seed=7)
    assert [e.message for e in r1] == [e.message for e in r2]


# --- sample_by_rate ---

def test_sample_by_rate_1_returns_all():
    entries = _entries(20)
    result = list(sample_by_rate(entries, rate=1.0, seed=0))
    assert result == entries


def test_sample_by_rate_0_returns_none():
    entries = _entries(20)
    result = list(sample_by_rate(entries, rate=0.0, seed=0))
    assert result == []


def test_sample_by_rate_raises_on_invalid_rate():
    with pytest.raises(ValueError):
        list(sample_by_rate(_entries(5), rate=1.5))


def test_sample_by_rate_roughly_half():
    entries = _entries(1000)
    result = list(sample_by_rate(entries, rate=0.5, seed=99))
    assert 400 <= len(result) <= 600
