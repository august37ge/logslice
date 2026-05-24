"""CLI helper that runs rate-limiting and prints a report."""
from __future__ import annotations

import argparse
import sys
from typing import Sequence

from logslice.parser import parse_line
from logslice.rate import rate_limit_entries, throttle_entries
from logslice.report_rate import compute_rate_report, format_rate_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-rate",
        description="Apply rate-limiting to a log file and report dropped entries.",
    )
    p.add_argument("file", help="Path to log file")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--window",
        nargs=2,
        metavar=("SECONDS", "MAX"),
        type=int,
        help="Sliding-window rate limit: SECONDS window, MAX entries allowed",
    )
    mode.add_argument(
        "--throttle",
        metavar="SECONDS",
        type=float,
        help="Minimum gap in seconds between consecutive entries",
    )
    p.add_argument(
        "--report",
        action="store_true",
        help="Print a drop report instead of the filtered entries",
    )
    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        with open(args.file) as fh:
            raw_lines = fh.readlines()
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    original = [e for line in raw_lines if (e := parse_line(line)) is not None]

    if args.window:
        win_sec, max_e = args.window
        filtered = list(rate_limit_entries(iter(original), win_sec, max_e))
    else:
        filtered = list(throttle_entries(iter(original), args.throttle))

    if args.report:
        report = compute_rate_report(original, filtered)
        print(format_rate_report(report))
    else:
        for entry in filtered:
            print(entry.raw)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
