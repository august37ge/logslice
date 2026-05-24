"""Benchmark helpers: compare profile results across runs or files."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from logslice.profile import ProfileResult, profile_file


@dataclass
class BenchmarkResult:
    label: str
    profile: ProfileResult


def run_benchmark(files: Dict[str, str]) -> List[BenchmarkResult]:
    """Profile each labelled file path and return ordered results.

    Args:
        files: mapping of label -> file path.

    Returns:
        List of BenchmarkResult sorted by throughput descending.
    """
    results: List[BenchmarkResult] = []
    for label, path in files.items():
        prof = profile_file(path)
        results.append(BenchmarkResult(label=label, profile=prof))
    results.sort(key=lambda r: r.profile.lines_per_second, reverse=True)
    return results


def compare_profiles(
    baseline: ProfileResult, candidate: ProfileResult
) -> Dict[str, float]:
    """Return delta metrics between a baseline and candidate profile.

    Positive values mean the candidate is faster / larger.
    """
    return {
        "delta_lines_per_second": candidate.lines_per_second - baseline.lines_per_second,
        "delta_elapsed_seconds": candidate.elapsed_seconds - baseline.elapsed_seconds,
        "delta_parsed_lines": candidate.parsed_lines - baseline.parsed_lines,
        "delta_skipped_lines": candidate.skipped_lines - baseline.skipped_lines,
        "speedup_ratio": (
            candidate.lines_per_second / baseline.lines_per_second
            if baseline.lines_per_second > 0
            else 0.0
        ),
    }


def format_benchmark(results: List[BenchmarkResult]) -> str:
    """Render benchmark results as a simple table."""
    if not results:
        return "No benchmark results."
    header = f"{'Label':<20} {'Lines':>8} {'Parsed':>8} {'Skipped':>8} {'Rate (l/s)':>12}"
    sep = "-" * len(header)
    rows = [header, sep]
    for r in results:
        p = r.profile
        rows.append(
            f"{r.label:<20} {p.total_lines:>8} {p.parsed_lines:>8}"
            f" {p.skipped_lines:>8} {p.lines_per_second:>12.1f}"
        )
    return "\n".join(rows)
