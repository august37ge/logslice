"""Integration tests for logslice.pipeline.run_pipeline."""
from __future__ import annotations

import io
import json
import tempfile
import os
from datetime import datetime, timezone

import pytest

from logslice.pipeline import run_pipeline


SAMPLE_LOG = """2024-06-01T08:00:00 INFO  server started
2024-06-01T09:00:00 DEBUG checking config
2024-06-01T10:00:00 WARNING high memory usage
2024-06-01T11:00:00 ERROR  out of memory
not a valid log line
2024-06-01T12:00:00 INFO  server stopped
"""


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "test.log"
    p.write_text(SAMPLE_LOG)
    return str(p)


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def test_pipeline_returns_stats(log_file):
    out = io.StringIO()
    stats = run_pipeline(log_file, output=out)
    assert stats.total_entries == 5


def test_pipeline_plain_output(log_file):
    out = io.StringIO()
    run_pipeline(log_file, fmt="plain", output=out)
    text = out.getvalue()
    assert "INFO" in text
    assert "ERROR" in text


def test_pipeline_json_output(log_file):
    out = io.StringIO()
    run_pipeline(log_file, fmt="json", output=out)
    for line in out.getvalue().strip().splitlines():
        obj = json.loads(line)
        assert "severity" in obj


def test_pipeline_start_filter(log_file):
    out = io.StringIO()
    stats = run_pipeline(log_file, start=_dt("2024-06-01T10:00:00"), output=out)
    assert stats.total_entries == 3


def test_pipeline_end_filter(log_file):
    out = io.StringIO()
    stats = run_pipeline(log_file, end=_dt("2024-06-01T09:00:00"), output=out)
    assert stats.total_entries == 2


def test_pipeline_severity_filter(log_file):
    out = io.StringIO()
    stats = run_pipeline(log_file, min_severity="WARNING", output=out)
    for sev in stats.severity_counts:
        assert sev in ("WARNING", "ERROR", "CRITICAL")


def test_pipeline_show_stats(log_file):
    out = io.StringIO()
    run_pipeline(log_file, output=out, show_stats=True)
    text = out.getvalue()
    assert "Total entries" in text
    assert "Skipped" in text
