"""Command line interface."""
from __future__ import annotations

import argparse
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfoNotFoundError

from .analyze import analyze
from .demo import write_demo
from .parse import default_root, load_sessions
from .pricing import PriceTable, PricingError
from .report import html_report, text_summary, to_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="burnrate", description="Cost and waste analysis for Claude Code transcripts.")
    parser.add_argument("command", choices=["report", "summary", "json", "doctor", "demo"])
    parser.add_argument("--root", type=Path, help="transcripts directory (default: ~/.claude/projects)")
    parser.add_argument("--since", type=int, metavar="DAYS", help="only include the last N days")
    parser.add_argument("--tz", default="America/Toronto", help="timezone for day buckets")
    parser.add_argument("--pricing", type=Path, help="custom pricing.json")
    parser.add_argument("--out", type=Path, default=Path("burnrate.html"), help="HTML output path (report/demo)")
    return parser


def _run(root: Path, args: argparse.Namespace) -> tuple[dict, object]:
    prices = PriceTable.load(args.pricing)
    sessions, stats = load_sessions(root)
    since = datetime.now(timezone.utc) - timedelta(days=args.since) if args.since else None
    return analyze(sessions, stats, prices, args.tz, since), stats


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "demo":
            with tempfile.TemporaryDirectory() as tmp:
                root = write_demo(Path(tmp) / "projects")
                result, _ = _run(root, args)
            args.out.write_text(html_report(result), encoding="utf-8")
            print(text_summary(result))
            print(f"\nDemo dashboard written to {args.out}")
            return 0
        root = args.root or default_root()
        if not root.is_dir():
            print(f"error: transcripts directory not found: {root}", file=sys.stderr)
            return 2
        result, stats = _run(root, args)
    except (PricingError, ZoneInfoNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.command == "doctor":
        for name, value in result["scan"].items():
            print(f"{name}: {value}")
        print(f"unpriced models: {', '.join(result['unpriced_models']) or 'none'}")
        return 1 if stats.turns == 0 else 0
    if args.command == "json":
        print(to_json(result))
    elif args.command == "summary":
        print(text_summary(result))
    else:
        args.out.write_text(html_report(result), encoding="utf-8")
        print(text_summary(result))
        print(f"\nDashboard written to {args.out}")
    return 0
