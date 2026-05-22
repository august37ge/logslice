"""Tests for logslice.cache."""

import os
import time
from pathlib import Path

import pytest

from logslice.cache import (
    CacheEntry,
    _cache_path,
    _is_valid,
    load_cache,
    save_cache,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_log(tmp_path: Path, content: str = "line1\nline2\n") -> Path:
    p = tmp_path / "app.log"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# _cache_path
# ---------------------------------------------------------------------------

def test_cache_path_creates_directory(tmp_path):
    cache_dir = str(tmp_path / "cache")
    result = _cache_path("/var/log/app.log", cache_dir=cache_dir)
    assert result.parent.exists()
    assert result.suffix == ".json"


def test_cache_path_deterministic(tmp_path):
    cache_dir = str(tmp_path / "cache")
    p1 = _cache_path("/var/log/app.log", cache_dir=cache_dir)
    p2 = _cache_path("/var/log/app.log", cache_dir=cache_dir)
    assert p1 == p2


def test_cache_path_different_for_different_files(tmp_path):
    cache_dir = str(tmp_path / "cache")
    p1 = _cache_path("/var/log/a.log", cache_dir=cache_dir)
    p2 = _cache_path("/var/log/b.log", cache_dir=cache_dir)
    assert p1 != p2


# ---------------------------------------------------------------------------
# _is_valid
# ---------------------------------------------------------------------------

def test_is_valid_returns_true_for_fresh_entry(tmp_path):
    log = _write_log(tmp_path)
    stat = os.stat(str(log))
    entry = CacheEntry(
        file_path=str(log),
        file_size=stat.st_size,
        file_mtime=stat.st_mtime,
    )
    assert _is_valid(entry, str(log)) is True


def test_is_valid_returns_false_when_size_changes(tmp_path):
    log = _write_log(tmp_path)
    stat = os.stat(str(log))
    entry = CacheEntry(
        file_path=str(log),
        file_size=stat.st_size + 99,
        file_mtime=stat.st_mtime,
    )
    assert _is_valid(entry, str(log)) is False


def test_is_valid_returns_false_for_missing_file(tmp_path):
    entry = CacheEntry(file_path="/nonexistent.log", file_size=0, file_mtime=0.0)
    assert _is_valid(entry, "/nonexistent.log") is False


# ---------------------------------------------------------------------------
# save_cache / load_cache round-trip
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    log = _write_log(tmp_path)
    cache_dir = str(tmp_path / "cache")
    index = [("2024-01-01T00:00:00", 0), ("2024-01-01T01:00:00", 50)]
    save_cache(str(log), index, cache_dir=cache_dir)
    result = load_cache(str(log), cache_dir=cache_dir)
    assert result is not None
    assert result.index == index


def test_load_cache_returns_none_when_no_file(tmp_path):
    cache_dir = str(tmp_path / "cache")
    result = load_cache(str(tmp_path / "missing.log"), cache_dir=cache_dir)
    assert result is None


def test_load_cache_returns_none_after_file_modified(tmp_path):
    log = _write_log(tmp_path)
    cache_dir = str(tmp_path / "cache")
    save_cache(str(log), [], cache_dir=cache_dir)
    # Modify the file to invalidate the cache
    time.sleep(0.05)
    log.write_text("extra line\n", encoding="utf-8")
    result = load_cache(str(log), cache_dir=cache_dir)
    assert result is None


def test_save_cache_silently_ignores_missing_log(tmp_path):
    cache_dir = str(tmp_path / "cache")
    # Should not raise even if the source file does not exist
    save_cache("/does/not/exist.log", [], cache_dir=cache_dir)
