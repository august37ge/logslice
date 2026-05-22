"""Tests for logslice.multifile."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from logslice.multifile import file_count_with_rotated, merge_files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TS1 = "2024-01-01T10:00:00"
TS2 = "2024-01-01T11:00:00"
TS3 = "2024-01-01T12:00:00"


def _log_line(ts: str, sev: str, msg: str) -> str:
    return f"{ts} [{sev}] {msg}"


def _write(path: Path, *lines: str) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# merge_files
# ---------------------------------------------------------------------------

def test_merge_files_single_file(tmp_path):
    log = tmp_path / "a.log"
    _write(log, _log_line(TS1, "INFO", "msg1"), _log_line(TS2, "ERROR", "msg2"))
    entries = list(merge_files([log]))
    assert len(entries) == 2


def test_merge_files_sorted_across_files(tmp_path):
    log_a = tmp_path / "a.log"
    log_b = tmp_path / "b.log"
    _write(log_a, _log_line(TS3, "INFO", "late"))
    _write(log_b, _log_line(TS1, "INFO", "early"))
    entries = list(merge_files([log_a, log_b]))
    assert entries[0].message == "early"
    assert entries[-1].message == "late"


def test_merge_files_skips_missing_file(tmp_path):
    log = tmp_path / "a.log"
    _write(log, _log_line(TS1, "INFO", "ok"))
    missing = tmp_path / "ghost.log"
    entries = list(merge_files([log, missing]))
    assert len(entries) == 1


def test_merge_files_severity_filter(tmp_path):
    log = tmp_path / "a.log"
    _write(
        log,
        _log_line(TS1, "DEBUG", "verbose"),
        _log_line(TS2, "ERROR", "important"),
    )
    entries = list(merge_files([log], severity="ERROR"))
    assert all(e.severity == "ERROR" for e in entries)


def test_merge_files_with_rotated(tmp_path):
    log = tmp_path / "app.log"
    rot = tmp_path / "app.log.1"
    _write(rot, _log_line(TS1, "INFO", "old"))
    _write(log, _log_line(TS3, "INFO", "new"))
    entries = list(merge_files([log], include_rotated=True))
    assert len(entries) == 2
    assert entries[0].message == "old"


def test_merge_files_empty_file(tmp_path):
    log = tmp_path / "empty.log"
    log.write_text("", encoding="utf-8")
    entries = list(merge_files([log]))
    assert entries == []


# ---------------------------------------------------------------------------
# file_count_with_rotated
# ---------------------------------------------------------------------------

def test_file_count_no_rotations(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("", encoding="utf-8")
    assert file_count_with_rotated(log) == 1


def test_file_count_with_rotations(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("", encoding="utf-8")
    (tmp_path / "app.log.1").write_text("", encoding="utf-8")
    (tmp_path / "app.log.2").write_text("", encoding="utf-8")
    assert file_count_with_rotated(log) == 3


def test_file_count_missing_base(tmp_path):
    log = tmp_path / "app.log"
    (tmp_path / "app.log.1").write_text("", encoding="utf-8")
    assert file_count_with_rotated(log) == 1
