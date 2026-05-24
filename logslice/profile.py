"""Profiling utilities: measure parse and filter timing across a log file."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from logslice.parser import LogEntry, parse_line


@dataclass
class ProfileResult:
    total_lines: int = 0
    parsed_lines: int = 0
    skipped_lines: int = 0
    elapsed_seconds: float = 0.0
    lines_per_second: float = 0.0
    severity_counts: dict = field(default_factory=dict)

    def summary(self) -> str:
        return (
            f"Lines total={self.total_lines} parsed={self.parsed_lines} "
            f"skipped={self.skipped_lines} "
            f"elapsed={self.elapsed_seconds:.4f}s "
            f"rate={self.lines_per_second:.1f} lines/s"
        )


def profile_lines(lines: Iterable[str]) -> ProfileResult:
    """Parse an iterable of raw log lines and collect timing + severity stats."""
    result = ProfileResult()
    start = time.perf_counter()

    for raw in lines:
        result.total_lines += 1
        entry = parse_line(raw)
        if entry is None:
            result.skipped_lines += 1
        else:
            result.parsed_lines += 1
            sev = entry.severity
            result.severity_counts[sev] = result.severity_counts.get(sev, 0) + 1

    elapsed = time.perf_counter() - start
    result.elapsed_seconds = elapsed
    result.lines_per_second = (
        result.total_lines / elapsed if elapsed > 0 else 0.0
    )
    return result


def profile_file(path: str) -> ProfileResult:
    """Open a log file and profile its lines."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return profile_lines(fh)


def format_profile(result: ProfileResult) -> str:
    """Return a human-readable multi-line profile report."""
    lines: List[str] = [
        "=== logslice profile ===",
        f"  Total lines   : {result.total_lines}",
        f"  Parsed        : {result.parsed_lines}",
        f"  Skipped       : {result.skipped_lines}",
        f"  Elapsed       : {result.elapsed_seconds:.4f} s",
        f"  Throughput    : {result.lines_per_second:.1f} lines/s",
        "  Severity breakdown:",
    ]
    for sev, count in sorted(result.severity_counts.items()):
        lines.append(f"    {sev:<10}: {count}")
    return "\n".join(lines)
