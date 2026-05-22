"""Tests for logslice.output."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from logslice.output import write_lines, write_to_stream


def test_write_to_stream_returns_line_count():
    buf = io.StringIO()
    count = write_to_stream(["line1", "line2", "line3"], buf)
    assert count == 3


def test_write_to_stream_content():
    buf = io.StringIO()
    write_to_stream(["hello", "world"], buf)
    buf.seek(0)
    assert buf.read() == "hello\nworld\n"


def test_write_lines_to_file(tmp_path: Path):
    out = tmp_path / "out.log"
    count = write_lines(["a", "b", "c"], out)
    assert count == 3
    assert out.read_text(encoding="utf-8") == "a\nb\nc\n"


def test_write_lines_append_mode(tmp_path: Path):
    out = tmp_path / "out.log"
    write_lines(["first"], out)
    write_lines(["second"], out, append=True)
    assert out.read_text(encoding="utf-8") == "first\nsecond\n"


def test_write_lines_overwrite_mode(tmp_path: Path):
    out = tmp_path / "out.log"
    write_lines(["old"], out)
    write_lines(["new"], out, append=False)
    assert out.read_text(encoding="utf-8") == "new\n"


def test_write_lines_stdout(capsys):
    count = write_lines(["stdout line"], destination=None)
    captured = capsys.readouterr()
    assert count == 1
    assert "stdout line" in captured.out


def test_write_lines_empty_iterable(tmp_path: Path):
    out = tmp_path / "empty.log"
    count = write_lines([], out)
    assert count == 0
    assert out.read_text(encoding="utf-8") == ""
