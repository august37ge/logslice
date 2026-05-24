"""Integration tests: checkpoint + resume working end-to-end."""

from __future__ import annotations

from pathlib import Path

import pytest

from logslice.checkpoint import (
    Checkpoint,
    save_checkpoint,
    load_checkpoint,
    clear_checkpoint,
    checkpoint_exists,
)
from logslice.resume import process_with_checkpoint


LINES = [
    "2024-03-01T08:00:00Z INFO  app booted\n",
    "2024-03-01T08:00:01Z WARNING disk low\n",
    "2024-03-01T08:00:02Z ERROR  connection refused\n",
    "2024-03-01T08:00:03Z DEBUG  retry attempt 1\n",
    "2024-03-01T08:00:04Z INFO  recovered\n",
]


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "service.log"
    p.write_text("".join(LINES), encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def _patch_checkpoint_dir(tmp_path, monkeypatch):
    import logslice.checkpoint as cp_mod
    monkeypatch.setattr(cp_mod, "_CHECKPOINT_DIR", tmp_path / "checkpoints")


def test_full_incremental_processing(log_file):
    """Simulate two processing runs: first reads all, second reads nothing new."""
    entries1, cp1 = process_with_checkpoint(str(log_file), resume=False)
    assert len(entries1) == 5
    save_checkpoint(cp1)

    entries2, cp2 = process_with_checkpoint(str(log_file), resume=True)
    assert len(entries2) == 0
    assert cp2.byte_offset == cp1.byte_offset


def test_incremental_processing_with_appended_lines(log_file):
    """Simulate a new line appended between two runs."""
    entries1, cp1 = process_with_checkpoint(str(log_file), resume=False)
    save_checkpoint(cp1)

    new_line = "2024-03-01T08:00:05Z CRITICAL  meltdown\n"
    with open(log_file, "a", encoding="utf-8") as fh:
        fh.write(new_line)

    entries2, cp2 = process_with_checkpoint(str(log_file), resume=True)
    assert len(entries2) == 1
    assert entries2[0].severity == "CRITICAL"


def test_clear_and_reprocess(log_file):
    """Clearing checkpoint causes full re-read."""
    _, cp1 = process_with_checkpoint(str(log_file), resume=False)
    save_checkpoint(cp1)
    assert checkpoint_exists(str(log_file))

    clear_checkpoint(str(log_file))
    assert not checkpoint_exists(str(log_file))

    entries, _ = process_with_checkpoint(str(log_file), resume=True)
    assert len(entries) == 5
