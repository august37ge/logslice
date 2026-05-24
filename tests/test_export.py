"""Tests for logslice.export."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from logslice.export import export_csv, export_jsonl, export_txt, export_to_file
from logslice.parser import LogEntry


def _entry(
    severity: str = "INFO",
    message: str = "hello",
) -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 3, 10, 12, 0, 0, tzinfo=timezone.utc),
        severity=severity,
        message=message,
        raw=f"2024-03-10T12:00:00Z [{severity}] {message}",
        extra={},
    )


# --- export_csv ---

def test_export_csv_header_present():
    buf = io.StringIO()
    export_csv([_entry()], buf)
    buf.seek(0)
    reader = csv.DictReader(buf)
    assert set(reader.fieldnames or []) >= {"timestamp", "severity", "message"}


def test_export_csv_row_count():
    buf = io.StringIO()
    n = export_csv([_entry(), _entry("ERROR", "boom")], buf)
    assert n == 2


def test_export_csv_row_values():
    buf = io.StringIO()
    export_csv([_entry("WARNING", "disk low")], buf)
    buf.seek(0)
    rows = list(csv.DictReader(buf))
    assert rows[0]["severity"] == "WARNING"
    assert rows[0]["message"] == "disk low"


def test_export_csv_empty_input():
    buf = io.StringIO()
    n = export_csv([], buf)
    assert n == 0


# --- export_jsonl ---

def test_export_jsonl_each_line_is_valid_json():
    buf = io.StringIO()
    export_jsonl([_entry(), _entry("DEBUG", "trace")], buf)
    buf.seek(0)
    lines = [l for l in buf.read().splitlines() if l]
    for line in lines:
        obj = json.loads(line)
        assert "timestamp" in obj
        assert "severity" in obj


def test_export_jsonl_returns_count():
    buf = io.StringIO()
    n = export_jsonl([_entry(), _entry()], buf)
    assert n == 2


def test_export_jsonl_timestamp_is_iso():
    buf = io.StringIO()
    export_jsonl([_entry()], buf)
    buf.seek(0)
    obj = json.loads(buf.readline())
    assert obj["timestamp"].startswith("2024-03-10")


# --- export_txt ---

def test_export_txt_writes_raw_lines():
    entry = _entry("ERROR", "something failed")
    buf = io.StringIO()
    export_txt([entry], buf)
    buf.seek(0)
    assert entry.raw in buf.read()


def test_export_txt_returns_count():
    buf = io.StringIO()
    n = export_txt([_entry(), _entry(), _entry()], buf)
    assert n == 3


# --- export_to_file ---

def test_export_to_file_csv(tmp_path: Path):
    out = tmp_path / "out.csv"
    n = export_to_file([_entry(), _entry("ERROR")], out, fmt="csv")
    assert n == 2
    assert out.exists()
    content = out.read_text()
    assert "severity" in content


def test_export_to_file_jsonl(tmp_path: Path):
    out = tmp_path / "out.jsonl"
    export_to_file([_entry()], out, fmt="jsonl")
    obj = json.loads(out.read_text().strip())
    assert obj["severity"] == "INFO"


def test_export_to_file_txt(tmp_path: Path):
    entry = _entry(message="written to disk")
    out = tmp_path / "out.txt"
    export_to_file([entry], out, fmt="txt")
    assert "written to disk" in out.read_text()


def test_export_to_file_invalid_format_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_to_file([_entry()], tmp_path / "x", fmt="xml")  # type: ignore[arg-type]
