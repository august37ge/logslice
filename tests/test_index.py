"""Tests for logslice.index — byte-offset index building and seeking."""

from __future__ import annotations

import io
import textwrap
from pathlib import Path

import pytest

from logslice.index import (
    IndexEntry,
    build_index,
    save_index,
    load_index,
    seek_to_start,
)


_LINES = textwrap.dedent("""\
    2024-01-01T00:00:00 INFO  startup complete
    2024-01-01T00:01:00 DEBUG checking config
    2024-01-01T00:02:00 WARN  disk usage high
    2024-01-01T00:03:00 ERROR disk full
    2024-01-01T00:04:00 INFO  cleanup started
""")


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text(_LINES, encoding="utf-8")
    return p


def test_build_index_returns_first_entry(log_file):
    index = build_index(str(log_file), sample_every=500)
    assert len(index) >= 1
    assert index[0].offset == 0


def test_build_index_entry_has_valid_timestamp(log_file):
    index = build_index(str(log_file), sample_every=1)
    for entry in index:
        assert "T" in entry.timestamp_iso or len(entry.timestamp_iso) >= 10


def test_build_index_samples_every_n_lines(log_file):
    index = build_index(str(log_file), sample_every=2)
    # 5 valid lines, sample_every=2 → entries at line 1, 3, 5 → 3 entries
    assert len(index) == 3


def test_build_index_offsets_are_ascending(log_file):
    index = build_index(str(log_file), sample_every=1)
    offsets = [e.offset for e in index]
    assert offsets == sorted(offsets)


def test_save_and_load_index_roundtrip(log_file):
    index = build_index(str(log_file), sample_every=1)
    save_index(str(log_file), index)
    loaded = load_index(str(log_file))
    assert loaded is not None
    assert len(loaded) == len(index)
    assert loaded[0].offset == index[0].offset
    assert loaded[0].timestamp_iso == index[0].timestamp_iso


def test_load_index_returns_none_when_missing(tmp_path):
    missing = tmp_path / "ghost.log"
    missing.write_text("2024-01-01T00:00:00 INFO hi\n", encoding="utf-8")
    result = load_index(str(missing))
    assert result is None


def test_seek_to_start_seeks_to_best_offset():
    index = [
        IndexEntry(offset=0, timestamp_iso="2024-01-01T00:00:00"),
        IndexEntry(offset=100, timestamp_iso="2024-01-01T01:00:00"),
        IndexEntry(offset=200, timestamp_iso="2024-01-01T02:00:00"),
    ]
    fake = io.BytesIO(b"x" * 300)
    seek_to_start(fake, index, "2024-01-01T01:30:00")
    assert fake.tell() == 100


def test_seek_to_start_falls_back_to_zero_when_before_all():
    index = [
        IndexEntry(offset=50, timestamp_iso="2024-01-01T06:00:00"),
    ]
    fake = io.BytesIO(b"x" * 200)
    seek_to_start(fake, index, "2024-01-01T00:00:00")
    assert fake.tell() == 0


def test_seek_to_start_uses_last_entry_before_start():
    index = [
        IndexEntry(offset=0, timestamp_iso="2024-01-01T00:00:00"),
        IndexEntry(offset=80, timestamp_iso="2024-01-01T00:02:00"),
        IndexEntry(offset=160, timestamp_iso="2024-01-01T00:04:00"),
    ]
    fake = io.BytesIO(b"x" * 300)
    seek_to_start(fake, index, "2024-01-01T00:03:00")
    assert fake.tell() == 80
