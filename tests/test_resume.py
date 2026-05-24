"""Tests for logslice.resume."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from logslice.checkpoint import Checkpoint, save_checkpoint, clear_checkpoint
from logslice.resume import iter_from_checkpoint, process_with_checkpoint


LINE_A = "2024-01-01T00:00:01Z INFO  service started\n"
LINE_B = "2024-01-01T00:00:02Z ERROR something broke\n"
LINE_C = "2024-01-01T00:00:03Z DEBUG details here\n"


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "app.log"
    p.write_text(LINE_A + LINE_B + LINE_C, encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def _patch_checkpoint_dir(tmp_path, monkeypatch):
    import logslice.checkpoint as cp_mod
    monkeypatch.setattr(cp_mod, "_CHECKPOINT_DIR", tmp_path / "checkpoints")


def test_iter_from_checkpoint_no_checkpoint_reads_all(log_file):
    entries = list(iter_from_checkpoint(str(log_file), checkpoint=None))
    assert len(entries) == 3


def test_iter_from_checkpoint_with_offset_skips_first_line(log_file):
    offset = len(LINE_A.encode("utf-8"))
    cp = Checkpoint(file_path=str(log_file), byte_offset=offset, line_number=1)
    entries = list(iter_from_checkpoint(str(log_file), checkpoint=cp))
    assert len(entries) == 2
    assert entries[0].severity == "ERROR"


def test_iter_from_checkpoint_at_end_yields_nothing(log_file):
    offset = log_file.stat().st_size
    cp = Checkpoint(file_path=str(log_file), byte_offset=offset, line_number=3)
    entries = list(iter_from_checkpoint(str(log_file), checkpoint=cp))
    assert entries == []


def test_process_with_checkpoint_no_resume_reads_all(log_file):
    entries, cp = process_with_checkpoint(str(log_file), resume=False)
    assert len(entries) == 3
    assert cp.line_number == 3
    assert cp.byte_offset == log_file.stat().st_size


def test_process_with_checkpoint_resume_skips_seen_lines(log_file):
    first_offset = len(LINE_A.encode("utf-8"))
    existing = Checkpoint(
        file_path=str(log_file), byte_offset=first_offset, line_number=1
    )
    save_checkpoint(existing)
    entries, cp = process_with_checkpoint(str(log_file), resume=True)
    assert len(entries) == 2
    assert cp.line_number == 3


def test_process_with_checkpoint_records_last_timestamp(log_file):
    entries, cp = process_with_checkpoint(str(log_file), resume=False)
    assert cp.last_timestamp is not None
    assert "2024-01-01" in cp.last_timestamp


def test_process_with_checkpoint_no_resume_ignores_saved(log_file):
    # Even if a checkpoint exists, resume=False should start from the top.
    full_offset = log_file.stat().st_size
    existing = Checkpoint(
        file_path=str(log_file), byte_offset=full_offset, line_number=3
    )
    save_checkpoint(existing)
    entries, cp = process_with_checkpoint(str(log_file), resume=False)
    assert len(entries) == 3
