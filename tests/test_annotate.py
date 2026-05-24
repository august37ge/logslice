"""Tests for logslice.annotate."""

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.annotate import (
    AnnotatedEntry,
    annotate_entries,
    filter_by_tag,
    keyword_annotator,
    severity_annotator,
    source_annotator,
)
from logslice.parser import LogEntry


def _entry(
    message: str = "test message",
    severity: str = "INFO",
    source: str = "app",
) -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        severity=severity,
        source=source,
        message=message,
        raw=f"2024-01-01T12:00:00Z [{severity}] {source}: {message}",
    )


def test_annotated_entry_starts_with_no_tags():
    ae = AnnotatedEntry(entry=_entry())
    assert ae.tags == []


def test_add_tag_appends_tag():
    ae = AnnotatedEntry(entry=_entry())
    ae.add_tag("foo")
    assert "foo" in ae.tags


def test_add_tag_no_duplicates():
    ae = AnnotatedEntry(entry=_entry())
    ae.add_tag("foo")
    ae.add_tag("foo")
    assert ae.tags.count("foo") == 1


def test_severity_annotator_tags_error():
    entry = _entry(severity="ERROR")
    tag = severity_annotator(entry)
    assert tag == "high-severity"


def test_severity_annotator_tags_critical():
    entry = _entry(severity="CRITICAL")
    tag = severity_annotator(entry)
    assert tag == "high-severity"


def test_severity_annotator_skips_info():
    entry = _entry(severity="INFO")
    tag = severity_annotator(entry)
    assert tag is None


def test_keyword_annotator_matches():
    annotator = keyword_annotator("timeout", "refused")
    entry = _entry(message="connection timeout occurred")
    tag = annotator(entry)
    assert tag == "keyword:timeout"


def test_keyword_annotator_no_match_returns_none():
    annotator = keyword_annotator("timeout")
    entry = _entry(message="everything is fine")
    assert annotator(entry) is None


def test_keyword_annotator_case_insensitive():
    annotator = keyword_annotator("error")
    entry = _entry(message="An ERROR occurred")
    assert annotator(entry) == "keyword:error"


def test_source_annotator_maps_source():
    annotator = source_annotator({"db": "database", "web": "frontend"})
    entry = _entry(source="db")
    assert annotator(entry) == "database"


def test_source_annotator_unknown_source_returns_none():
    annotator = source_annotator({"db": "database"})
    entry = _entry(source="unknown")
    assert annotator(entry) is None


def test_annotate_entries_applies_all_annotators():
    entries = [
        _entry(severity="ERROR", message="timeout"),
        _entry(severity="INFO", message="all good"),
    ]
    annotators = [severity_annotator, keyword_annotator("timeout")]
    results = list(annotate_entries(entries, annotators))

    assert len(results) == 2
    assert "high-severity" in results[0].tags
    assert "keyword:timeout" in results[0].tags
    assert results[1].tags == []


def test_annotate_entries_preserves_original_entry():
    entry = _entry(severity="WARNING")
    results = list(annotate_entries([entry], [severity_annotator]))
    assert results[0].entry is entry


def test_filter_by_tag_returns_only_matching():
    entries = [
        _entry(severity="ERROR"),
        _entry(severity="INFO"),
        _entry(severity="CRITICAL"),
    ]
    annotated = list(annotate_entries(entries, [severity_annotator]))
    filtered = list(filter_by_tag(annotated, "high-severity"))
    assert len(filtered) == 2
    for ae in filtered:
        assert "high-severity" in ae.tags
