"""Command-line interface for logslice."""

import argparse
import sys
from datetime import datetime

from logslice.slicer import slice_file

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _parse_dt(value: str) -> datetime:
    try:
        return datetime.strptime(value, TIMESTAMP_FORMAT)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid datetime '{value}'. Expected format: YYYY-MM-DDTHH:MM:SS"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Filter a log file by time range and/or severity level.",
    )
    parser.add_argument("file", help="Path to the log file to slice.")
    parser.add_argument(
        "--start",
        metavar="DATETIME",
        type=_parse_dt,
        default=None,
        help="Include entries at or after this timestamp (YYYY-MM-DDTHH:MM:SS).",
    )
    parser.add_argument(
        "--end",
        metavar="DATETIME",
        type=_parse_dt,
        default=None,
        help="Include entries at or before this timestamp (YYYY-MM-DDTHH:MM:SS).",
    )
    parser.add_argument(
        "--severity",
        metavar="LEVEL",
        default=None,
        help="Minimum severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        entries = slice_file(
            args.file,
            start=args.start,
            end=args.end,
            min_severity=args.severity,
        )
        count = 0
        for entry in entries:
            print(entry.raw)
            count += 1
        if count == 0:
            print("No matching log entries found.", file=sys.stderr)
        return 0
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
