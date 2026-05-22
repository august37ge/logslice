"""Tests for logslice.tail."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from logslice.tail import tail_bytes, tail_entries, tail_lines


_SAMPLE = textwrap.dedent("""\
    2024-01-01T00:00:01Z INFO  first line
    2024-01-01T00:00:02Z DEBUG second line
    2024-01-01T00:00:03Z WARN  third line
    2024-01-01T00:00:04Z ERROR fourth line
    2024-01-01T00:00:05Z INFO  fifth line
""")


@pytest.fixture()
def log_file(tmp_path: Path) -> str:
    p = tmp_path / "sample.log"
    p.write_text(_SAMPLE)
    return str(p)


# ---------------------------------------------------------------------------
# tail_bytes
# ---------------------------------------------------------------------------

def test_tail_bytes_returns_correct_length(log_file: str) -> None:
    data = tail_bytes(log_file, 10)
    assert len(data) == 10


def test_tail_bytes_larger_than_file_returns_whole_file(log_file: str) -> None:
    size = os.path.getsize(log_file)
    data = tail_bytes(log_file, size + 1000)
    assert len(data) == size


# ---------------------------------------------------------------------------
# tail_lines
# ---------------------------------------------------------------------------

def test_tail_lines_returns_last_n(log_file: str) -> None:
    lines = tail_lines(log_file, 2)
    assert len(lines) == 2
    assert "fifth line" in lines[-1]
    assert "fourth line" in lines[-2]


def test_tail_lines_n_zero_returns_empty(log_file: str) -> None:
    assert tail_lines(log_file, 0) == []


def test_tail_lines_n_larger_than_file_returns_all(log_file: str) -> None:
    lines = tail_lines(log_file, 1000)
    assert len(lines) == 5


def test_tail_lines_empty_file(tmp_path: Path) -> None:
    p = tmp_path / "empty.log"
    p.write_text("")
    assert tail_lines(str(p), 10) == []


def test_tail_lines_preserves_order(log_file: str) -> None:
    lines = tail_lines(log_file, 3)
    assert "third line" in lines[0]
    assert "fourth line" in lines[1]
    assert "fifth line" in lines[2]


# ---------------------------------------------------------------------------
# tail_entries
# ---------------------------------------------------------------------------

def test_tail_entries_yields_log_entries(log_file: str) -> None:
    entries = list(tail_entries(log_file, 3))
    assert len(entries) == 3
    assert all(hasattr(e, "severity") for e in entries)


def test_tail_entries_skips_invalid_lines(tmp_path: Path) -> None:
    p = tmp_path / "mixed.log"
    p.write_text(
        "not a valid log line\n"
        "2024-01-01T00:00:01Z INFO  valid entry\n"
    )
    entries = list(tail_entries(str(p), 5))
    assert len(entries) == 1
    assert entries[0].message == "valid entry"
