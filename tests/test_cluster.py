"""Tests for logslice.cluster."""
from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.cluster import (
    Cluster,
    _message_key,
    cluster_entries,
    format_cluster_report,
)


def _entry(message: str, severity: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"2024-01-01 12:00:00 {severity} {message}",
    )


# --- _message_key ---

def test_message_key_replaces_integers():
    assert _message_key("retried 3 times") == "retried <VAR> times"


def test_message_key_replaces_ipv4():
    assert _message_key("connected to 192.168.1.1") == "connected to <VAR>"


def test_message_key_replaces_hex():
    assert _message_key("addr 0xFF at offset 12") == "addr <VAR> at offset <VAR>"


def test_message_key_normalises_whitespace():
    assert _message_key("  hello   world  ") == "hello world"


def test_message_key_same_pattern_for_different_numbers():
    assert _message_key("took 100ms") == _message_key("took 250ms")


# --- cluster_entries ---

def test_cluster_entries_empty_returns_empty():
    assert cluster_entries([]) == []


def test_cluster_entries_groups_similar_messages():
    entries = [
        _entry("retried 1 times"),
        _entry("retried 2 times"),
        _entry("retried 3 times"),
    ]
    clusters = cluster_entries(entries)
    assert len(clusters) == 1
    assert clusters[0].count == 3


def test_cluster_entries_distinct_messages_separate_clusters():
    entries = [
        _entry("disk full"),
        _entry("network timeout"),
    ]
    clusters = cluster_entries(entries)
    assert len(clusters) == 2


def test_cluster_entries_sorted_by_count_desc():
    entries = [
        _entry("event A once"),
        _entry("retried 1 times"),
        _entry("retried 2 times"),
    ]
    clusters = cluster_entries(entries)
    assert clusters[0].count >= clusters[-1].count


def test_cluster_entries_min_count_filters():
    entries = [
        _entry("retried 1 times"),
        _entry("retried 2 times"),
        _entry("disk full"),
    ]
    clusters = cluster_entries(entries, min_count=2)
    assert all(c.count >= 2 for c in clusters)


def test_cluster_severities_counted_correctly():
    entries = [
        _entry("error on port 80", severity="ERROR"),
        _entry("error on port 443", severity="WARNING"),
    ]
    clusters = cluster_entries(entries)
    assert clusters[0].severities.get("ERROR") == 1
    assert clusters[0].severities.get("WARNING") == 1


def test_cluster_representative_is_first_message():
    entries = [_entry("disk full"), _entry("disk full")]
    clusters = cluster_entries(entries)
    assert clusters[0].representative == "disk full"


# --- format_cluster_report ---

def test_format_cluster_report_empty():
    lines = format_cluster_report([])
    assert lines == ["No clusters found."]


def test_format_cluster_report_contains_count():
    entries = [_entry("retried 1 times"), _entry("retried 2 times")]
    clusters = cluster_entries(entries)
    report = format_cluster_report(clusters)
    assert any("2" in line for line in report)


def test_format_cluster_report_line_count_matches_clusters():
    entries = [_entry("disk full"), _entry("network error 5"), _entry("network error 6")]
    clusters = cluster_entries(entries)
    report = format_cluster_report(clusters)
    assert len(report) == len(clusters)
