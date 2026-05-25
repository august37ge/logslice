"""Tests for logslice.topology."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.topology import (
    TopologyNode,
    build_topology,
    format_topology,
    max_severity_for_source,
    severity_distribution,
)


def _entry(source: str, severity: str, ts: datetime | None = None) -> LogEntry:
    if ts is None:
        ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return LogEntry(timestamp=ts, severity=severity, message="msg", source=source, raw="raw")


# ---------------------------------------------------------------------------
# build_topology
# ---------------------------------------------------------------------------

def test_build_topology_empty_returns_empty_dict():
    assert build_topology([]) == {}


def test_build_topology_single_source():
    entries = [_entry("app", "INFO")]
    nodes = build_topology(entries)
    assert "app" in nodes
    assert nodes["app"].entry_count == 1
    assert "INFO" in nodes["app"].severities


def test_build_topology_accumulates_entry_count():
    entries = [_entry("app", "INFO"), _entry("app", "ERROR")]
    nodes = build_topology(entries)
    assert nodes["app"].entry_count == 2
    assert nodes["app"].severities == {"INFO", "ERROR"}


def test_build_topology_neighbours_within_window():
    t0 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2024, 1, 1, 12, 0, 3, tzinfo=timezone.utc)  # 3 s apart
    entries = [_entry("svc-a", "INFO", t0), _entry("svc-b", "WARN", t1)]
    nodes = build_topology(entries, window_seconds=5)
    assert "svc-b" in nodes["svc-a"].neighbours
    assert "svc-a" in nodes["svc-b"].neighbours


def test_build_topology_no_neighbours_outside_window():
    t0 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc)  # 10 s apart
    entries = [_entry("svc-a", "INFO", t0), _entry("svc-b", "WARN", t1)]
    nodes = build_topology(entries, window_seconds=5)
    assert nodes["svc-a"].neighbours == set()
    assert nodes["svc-b"].neighbours == set()


def test_build_topology_source_none_mapped_to_unknown():
    entry = LogEntry(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        severity="DEBUG",
        message="no source",
        source=None,
        raw="raw",
    )
    nodes = build_topology([entry])
    assert "unknown" in nodes


# ---------------------------------------------------------------------------
# max_severity_for_source
# ---------------------------------------------------------------------------

def test_max_severity_for_source_returns_highest():
    node = TopologyNode(source="app", severities={"DEBUG", "ERROR", "INFO"})
    assert max_severity_for_source(node) == "ERROR"


def test_max_severity_for_source_empty_returns_unknown():
    node = TopologyNode(source="app")
    assert max_severity_for_source(node) == "UNKNOWN"


# ---------------------------------------------------------------------------
# format_topology
# ---------------------------------------------------------------------------

def test_format_topology_empty():
    assert format_topology({}) == "(no entries)"


def test_format_topology_contains_source():
    entries = [_entry("web", "INFO")]
    nodes = build_topology(entries)
    out = format_topology(nodes)
    assert "web" in out
    assert "INFO" in out


# ---------------------------------------------------------------------------
# severity_distribution
# ---------------------------------------------------------------------------

def test_severity_distribution_keys_match_sources():
    entries = [_entry("a", "INFO"), _entry("b", "ERROR")]
    nodes = build_topology(entries)
    dist = severity_distribution(nodes)
    assert set(dist.keys()) == {"a", "b"}


def test_severity_distribution_contains_seen_severities():
    entries = [_entry("svc", "WARN"), _entry("svc", "CRITICAL")]
    nodes = build_topology(entries)
    dist = severity_distribution(nodes)
    assert "WARN" in dist["svc"]
    assert "CRITICAL" in dist["svc"]
