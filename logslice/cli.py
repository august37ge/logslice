"""Command-line interface for logslice."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from typing import Optional

from logslice.pipeline import run_pipeline


def _parse_dt(value: str) -> datetime:
    """Parse an ISO-8601 datetime string and attach UTC timezone."""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid datetime format: '{value}'. Expected ISO-8601, e.g. 2024-01-01T08:00:00"
        )
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log file slicer — filter by time range and severity.",
    )
    parser.add_argument("file", help="Path to the log file")
    parser.add_argument(
        "--start",
        type=_parse_dt,
        default=None,
        metavar="DATETIME",
        help="Include entries at or after this timestamp (ISO-8601)",
    )
    parser.add_argument(
        "--end",
        type=_parse_dt,
        default=None,
        metavar="DATETIME",
        help="Include entries at or before this timestamp (ISO-8601)",
    )
    parser.add_argument(
        "--min-severity",
        dest="min_severity",
        default=None,
        metavar="LEVEL",
        help="Minimum severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["plain", "colored", "json"],
        default="plain",
        help="Output format (default: plain)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        default=False,
        help="Print a summary of statistics after the log entries",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run_pipeline(
            path=args.file,
            start=args.start,
            end=args.end,
            min_severity=args.min_severity,
            fmt=args.fmt,
            output=sys.stdout,
            show_stats=args.stats,
        )
    except FileNotFoundError:
        print(f"logslice: error: file not found: {args.file}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
