"""Tests for logslice.checkpoint."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from logslice.checkpoint import (
    Checkpoint,
    _checkpoint_path,
    save_checkpoint,
    load_checkpoint,
    clear_checkpoint,
    checkpoint_exists,
)


@pytest.fixture(autouse=True)
def _patch_checkpoint_dir(tmp_path, monkeypatch):
    import logslice.checkpoint as cp_mod
    monkeypatch.setattr(cp_mod, "_CHECKPOINT_DIR", tmp_path / "checkpoints")


LOG_PATH = "/var/log/app/app.log"


def test_checkpoint_path_creates_directory(tmp_path, monkeypatch):
    import logslice.checkpoint as cp_mod
    cp_dir = tmp_path / "cp"
    monkeypatch.setattr(cp_mod, "_CHECKPOINT_DIR", cp_dir)
    path = _checkpoint_path(LOG_PATH)
    assert cp_dir.exists()
    assert path.suffix == ".json"


def test_checkpoint_path_deterministic():
    p1 = _checkpoint_path(LOG_PATH)
    p2 = _checkpoint_path(LOG_PATH)
    assert p1 == p2


def test_checkpoint_path_different_for_different_files():
    p1 = _checkpoint_path("/logs/a.log")
    p2 = _checkpoint_path("/logs/b.log")
    assert p1 != p2


def test_save_checkpoint_writes_file():
    cp = Checkpoint(file_path=LOG_PATH, byte_offset=1024, line_number=50)
    path = save_checkpoint(cp)
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["byte_offset"] == 1024
    assert data["line_number"] == 50


def test_save_checkpoint_includes_timestamp():
    cp = Checkpoint(file_path=LOG_PATH, byte_offset=0, line_number=0, last_timestamp="2024-01-01T00:00:00")
    path = save_checkpoint(cp)
    data = json.loads(path.read_text())
    assert data["last_timestamp"] == "2024-01-01T00:00:00"


def test_load_checkpoint_returns_none_when_missing():
    result = load_checkpoint("/nonexistent/file.log")
    assert result is None


def test_load_checkpoint_round_trips():
    cp = Checkpoint(file_path=LOG_PATH, byte_offset=2048, line_number=100, last_timestamp="2024-06-01T12:00:00")
    save_checkpoint(cp)
    loaded = load_checkpoint(LOG_PATH)
    assert loaded is not None
    assert loaded.byte_offset == 2048
    assert loaded.line_number == 100
    assert loaded.last_timestamp == "2024-06-01T12:00:00"


def test_clear_checkpoint_removes_file():
    cp = Checkpoint(file_path=LOG_PATH, byte_offset=0, line_number=0)
    save_checkpoint(cp)
    assert checkpoint_exists(LOG_PATH)
    removed = clear_checkpoint(LOG_PATH)
    assert removed is True
    assert not checkpoint_exists(LOG_PATH)


def test_clear_checkpoint_returns_false_when_not_found():
    result = clear_checkpoint("/no/such/log.log")
    assert result is False


def test_checkpoint_exists_false_before_save():
    assert not checkpoint_exists("/logs/fresh.log")


def test_checkpoint_exists_true_after_save():
    cp = Checkpoint(file_path=LOG_PATH, byte_offset=512, line_number=10)
    save_checkpoint(cp)
    assert checkpoint_exists(LOG_PATH)
