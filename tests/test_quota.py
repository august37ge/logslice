"""Tests for logslice.quota."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from logslice.parser import LogEntry
from logslice.quota import QuotaConfig, QuotaResult, apply_quota, quota_entries


def _entry(severity: str = "INFO", message: str = "msg", source: str = "app") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        severity=severity,
        message=message,
        source=source,
        raw=f"2024-01-01T00:00:00Z [{severity}] {message}",
    )


def _collect(entries, config):
    kept, result = quota_entries(entries, config)
    return kept, result


# --- QuotaConfig validation ---

def test_quota_config_defaults_are_none():
    cfg = QuotaConfig()
    assert cfg.per_severity is None
    assert cfg.per_source is None
    assert cfg.total is None


def test_quota_config_negative_per_severity_raises():
    with pytest.raises(ValueError, match="per_severity"):
        QuotaConfig(per_severity=-1)


def test_quota_config_negative_per_source_raises():
    with pytest.raises(ValueError, match="per_source"):
        QuotaConfig(per_source=-1)


def test_quota_config_negative_total_raises():
    with pytest.raises(ValueError, match="total"):
        QuotaConfig(total=-1)


# --- apply_quota ---

def test_apply_quota_no_limits_keeps_all():
    entries = [_entry() for _ in range(5)]
    results = list(apply_quota(entries, QuotaConfig()))
    assert all(ok for _, ok in results)
    assert len(results) == 5


def test_apply_quota_per_severity_limits_count():
    entries = [_entry("ERROR") for _ in range(6)]
    results = list(apply_quota(entries, QuotaConfig(per_severity=3)))
    kept = [e for e, ok in results if ok]
    dropped = [e for e, ok in results if not ok]
    assert len(kept) == 3
    assert len(dropped) == 3


def test_apply_quota_per_source_limits_count():
    entries = [_entry(source="svc") for _ in range(4)]
    results = list(apply_quota(entries, QuotaConfig(per_source=2)))
    kept = [e for e, ok in results if ok]
    assert len(kept) == 2


def test_apply_quota_total_cap():
    entries = [_entry() for _ in range(10)]
    results = list(apply_quota(entries, QuotaConfig(total=4)))
    kept = [e for e, ok in results if ok]
    assert len(kept) == 4


def test_apply_quota_mixed_severities_independent_buckets():
    entries = (
        [_entry("INFO") for _ in range(3)]
        + [_entry("ERROR") for _ in range(3)]
    )
    results = list(apply_quota(entries, QuotaConfig(per_severity=2)))
    kept = [e for e, ok in results if ok]
    assert len(kept) == 4  # 2 INFO + 2 ERROR


# --- quota_entries ---

def test_quota_entries_result_counts_match():
    entries = [_entry() for _ in range(8)]
    kept, result = _collect(entries, QuotaConfig(total=5))
    assert result.emitted == 5
    assert result.dropped == 3
    assert len(kept) == 5


def test_quota_entries_dropped_by_severity_populated():
    entries = [_entry("WARN") for _ in range(5)]
    _, result = _collect(entries, QuotaConfig(per_severity=2))
    assert result.dropped_by_severity.get("WARN", 0) == 3


def test_quota_entries_dropped_by_source_populated():
    entries = [_entry(source="db") for _ in range(4)]
    _, result = _collect(entries, QuotaConfig(per_source=1))
    assert result.dropped_by_source.get("db", 0) == 3


def test_quota_entries_empty_input():
    kept, result = _collect([], QuotaConfig(total=10))
    assert kept == []
    assert result.emitted == 0
    assert result.dropped == 0


def test_quota_entries_zero_total_drops_all():
    entries = [_entry() for _ in range(3)]
    kept, result = _collect(entries, QuotaConfig(total=0))
    assert kept == []
    assert result.dropped == 3
