"""Export log entries to various file formats (CSV, JSONL, plain text)."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Iterable, List, Literal

from logslice.parser import LogEntry

ExportFormat = Literal["csv", "jsonl", "txt"]


def _entry_to_dict(entry: LogEntry) -> dict:
    return {
        "timestamp": entry.timestamp.isoformat(),
        "severity": entry.severity,
        "message": entry.message,
        **entry.extra,
    }


def export_csv(entries: Iterable[LogEntry], stream: io.TextIOBase) -> int:
    """Write entries as CSV rows; return number of rows written."""
    fieldnames = ["timestamp", "severity", "message"]
    writer = csv.DictWriter(
        stream,
        fieldnames=fieldnames,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    count = 0
    for entry in entries:
        writer.writerow(_entry_to_dict(entry))
        count += 1
    return count


def export_jsonl(entries: Iterable[LogEntry], stream: io.TextIOBase) -> int:
    """Write entries as newline-delimited JSON; return number of lines written."""
    count = 0
    for entry in entries:
        stream.write(json.dumps(_entry_to_dict(entry)) + "\n")
        count += 1
    return count


def export_txt(entries: Iterable[LogEntry], stream: io.TextIOBase) -> int:
    """Write entries as plain text (original raw line); return count."""
    count = 0
    for entry in entries:
        stream.write(entry.raw + "\n")
        count += 1
    return count


def export_to_file(
    entries: Iterable[LogEntry],
    path: str | Path,
    fmt: ExportFormat = "txt",
) -> int:
    """Export *entries* to *path* in the requested format; return row count."""
    _exporters = {"csv": export_csv, "jsonl": export_jsonl, "txt": export_txt}
    if fmt not in _exporters:
        raise ValueError(f"Unsupported export format: {fmt!r}")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        return _exporters[fmt](entries, fh)  # type: ignore[arg-type]
