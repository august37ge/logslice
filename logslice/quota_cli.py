"""CLI entry-point for quota-enforced log slicing."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.parser import parse_line
from logslice.quota import QuotaConfig, quota_entries
from logslice.report_quota import format_quota_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-quota",
        description="Emit log entries up to per-severity / per-source / total limits.",
    )
    p.add_argument("file", nargs="?", default="-", help="Log file (default: stdin)")
    p.add_argument(
        "--per-severity",
        type=int,
        default=None,
        metavar="N",
        help="Maximum entries to emit per severity level.",
    )
    p.add_argument(
        "--per-source",
        type=int,
        default=None,
        metavar="N",
        help="Maximum entries to emit per source.",
    )
    p.add_argument(
        "--total",
        type=int,
        default=None,
        metavar="N",
        help="Hard cap on total entries emitted.",
    )
    p.add_argument(
        "--report",
        action="store_true",
        help="Print a quota enforcement report to stderr.",
    )
    return p


def _open_input(path: str):
    """Open *path* for reading, or return ``sys.stdin`` when *path* is ``'-'``.

    Returns a tuple of ``(stream, should_close)`` so the caller knows whether
    it is responsible for closing the stream.
    """
    if path == "-":
        return sys.stdin, False
    try:
        return open(path, "r", encoding="utf-8"), True  # noqa: WPS515
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        cfg = QuotaConfig(
            per_severity=args.per_severity,
            per_source=args.per_source,
            total=args.total,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        stream, should_close = _open_input(args.file)
    except OSError:
        return 1

    try:
        raw_entries = [e for line in stream if (e := parse_line(line)) is not None]
    finally:
        if should_close:
            stream.close()

    kept, result = quota_entries(raw_entries, cfg)

    for entry in kept:
        print(entry.raw)

    if args.report:
        print(format_quota_report(result), file=sys.stderr)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
