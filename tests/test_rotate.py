"""Tests for logslice.rotate."""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from logslice.rotate import find_rotated, iter_rotated_lines, open_rotated


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _write_gz(path: Path, content: str) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        fh.write(content)


# ---------------------------------------------------------------------------
# find_rotated
# ---------------------------------------------------------------------------

def test_find_rotated_returns_empty_when_no_rotations(tmp_path):
    log = tmp_path / "app.log"
    _write(log, "line\n")
    assert find_rotated(log) == []


def test_find_rotated_finds_numbered_files(tmp_path):
    log = tmp_path / "app.log"
    _write(log, "")
    _write(tmp_path / "app.log.1", "")
    _write(tmp_path / "app.log.2", "")
    found = find_rotated(log)
    names = [p.name for p in found]
    assert "app.log.2" in names
    assert "app.log.1" in names


def test_find_rotated_finds_gz_file(tmp_path):
    log = tmp_path / "app.log"
    _write(log, "")
    _write_gz(tmp_path / "app.log.gz", "old line\n")
    found = find_rotated(log)
    assert any(p.suffix == ".gz" for p in found)


def test_find_rotated_excludes_base_file(tmp_path):
    log = tmp_path / "app.log"
    _write(log, "")
    _write(tmp_path / "app.log.1", "")
    found = find_rotated(log)
    assert log not in found


# ---------------------------------------------------------------------------
# open_rotated
# ---------------------------------------------------------------------------

def test_open_rotated_reads_plain_file(tmp_path):
    p = tmp_path / "app.log.1"
    _write(p, "hello\n")
    with open_rotated(p) as fh:
        assert fh.read() == "hello\n"


def test_open_rotated_reads_gz_file(tmp_path):
    p = tmp_path / "app.log.gz"
    _write_gz(p, "compressed\n")
    with open_rotated(p) as fh:
        assert fh.read() == "compressed\n"


# ---------------------------------------------------------------------------
# iter_rotated_lines
# ---------------------------------------------------------------------------

def test_iter_rotated_lines_order(tmp_path):
    log = tmp_path / "app.log"
    _write(tmp_path / "app.log.2", "oldest\n")
    _write(tmp_path / "app.log.1", "middle\n")
    _write(log, "newest\n")
    lines = list(iter_rotated_lines(log))
    assert lines[0].strip() == "oldest"
    assert lines[-1].strip() == "newest"


def test_iter_rotated_lines_no_rotations(tmp_path):
    log = tmp_path / "app.log"
    _write(log, "only\n")
    lines = list(iter_rotated_lines(log))
    assert lines == ["only\n"]


def test_iter_rotated_lines_missing_base(tmp_path):
    log = tmp_path / "app.log"
    _write(tmp_path / "app.log.1", "rotated\n")
    lines = list(iter_rotated_lines(log))
    assert lines == ["rotated\n"]
