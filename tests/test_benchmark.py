"""Tests for logslice.benchmark."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from logslice.benchmark import (
    BenchmarkResult,
    compare_profiles,
    format_benchmark,
    run_benchmark,
)
from logslice.profile import ProfileResult


LOG_CONTENT = textwrap.dedent("""\
    2024-01-15T10:00:00 ERROR something failed
    2024-01-15T10:00:01 INFO  all good
    2024-01-15T10:00:02 WARN  watch out
""")


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.log"
    p.write_text(LOG_CONTENT)
    return p


def test_run_benchmark_returns_one_result_per_file(log_file: Path):
    results = run_benchmark({"sample": str(log_file)})
    assert len(results) == 1
    assert results[0].label == "sample"


def test_run_benchmark_profile_populated(log_file: Path):
    results = run_benchmark({"sample": str(log_file)})
    prof = results[0].profile
    assert prof.total_lines == 3
    assert prof.parsed_lines == 3


def test_run_benchmark_sorted_by_throughput_desc(tmp_path: Path):
    f1 = tmp_path / "a.log"
    f2 = tmp_path / "b.log"
    f1.write_text(LOG_CONTENT)
    f2.write_text(LOG_CONTENT)
    results = run_benchmark({"a": str(f1), "b": str(f2)})
    rates = [r.profile.lines_per_second for r in results]
    assert rates == sorted(rates, reverse=True)


def test_run_benchmark_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        run_benchmark({"missing": str(tmp_path / "nope.log")})


def _make_profile(**kwargs) -> ProfileResult:
    defaults = dict(
        total_lines=100,
        parsed_lines=90,
        skipped_lines=10,
        elapsed_seconds=1.0,
        lines_per_second=100.0,
    )
    defaults.update(kwargs)
    return ProfileResult(**defaults)


def test_compare_profiles_delta_lines_per_second():
    base = _make_profile(lines_per_second=100.0)
    cand = _make_profile(lines_per_second=150.0)
    delta = compare_profiles(base, cand)
    assert delta["delta_lines_per_second"] == pytest.approx(50.0)


def test_compare_profiles_speedup_ratio():
    base = _make_profile(lines_per_second=100.0)
    cand = _make_profile(lines_per_second=200.0)
    delta = compare_profiles(base, cand)
    assert delta["speedup_ratio"] == pytest.approx(2.0)


def test_compare_profiles_zero_baseline_rate():
    base = _make_profile(lines_per_second=0.0)
    cand = _make_profile(lines_per_second=100.0)
    delta = compare_profiles(base, cand)
    assert delta["speedup_ratio"] == 0.0


def test_format_benchmark_empty():
    output = format_benchmark([])
    assert "No benchmark results" in output


def test_format_benchmark_contains_label(log_file: Path):
    results = run_benchmark({"myfile": str(log_file)})
    output = format_benchmark(results)
    assert "myfile" in output


def test_format_benchmark_contains_rate(log_file: Path):
    results = run_benchmark({"myfile": str(log_file)})
    output = format_benchmark(results)
    # Rate column header present
    assert "Rate" in output
