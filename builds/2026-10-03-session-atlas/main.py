"""Session Atlas: explore Claude Code session logs."""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from atlas.demo import generate_demo_logs  # noqa: E402
from atlas.pricing import load_prices  # noqa: E402
from atlas.report import write_report  # noqa: E402
from atlas.store import Store  # noqa: E402
from atlas.summarize import SummarizeError, summarize_missing  # noqa: E402

DEFAULT_LOGS = Path.home() / ".claude" / "projects"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="atlas", description="Explore your Claude Code session logs.")
    parser.add_argument("command", nargs="?", default="report", choices=["report", "search", "stats"])
    parser.add_argument("query", nargs="*", help="search terms (search command)")
    parser.add_argument("--logs", type=Path, default=DEFAULT_LOGS, help="log root (default ~/.claude/projects)")
    parser.add_argument("--db", type=Path, default=Path("atlas.db"), help="SQLite index path")
    parser.add_argument("--out", type=Path, default=Path("atlas.html"), help="HTML output path")
    parser.add_argument("--since", help="only sessions starting on/after this date, e.g. 2026-09-01")
    parser.add_argument("--tz-offset", type=float, default=0.0, help="hours from UTC for day/hour bucketing (Toronto: -4)")
    parser.add_argument("--idle-gap", type=int, default=300, help="seconds of silence not counted as active time")
    parser.add_argument("--prices", type=Path, help="JSON file overriding the price table")
    parser.add_argument("--summarize", action="store_true", help="AI 'where I left off' summaries (needs ANTHROPIC_API_KEY)")
    parser.add_argument("--summarize-limit", type=int, default=25)
    parser.add_argument("--demo", action="store_true", help="use synthetic logs instead of real ones")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        prices = load_prices(args.prices)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    logs = args.logs
    if args.demo:
        logs = Path(tempfile.mkdtemp(prefix="atlas-demo-"))
        created = generate_demo_logs(logs)
        print(f"Generated {created} synthetic sessions in {logs}")
    if not logs.is_dir():
        print(f"error: log directory not found: {logs}", file=sys.stderr)
        return 2

    store = Store(args.db)
    try:
        counts = store.index_directory(logs, prices, args.idle_gap)
        store.reprice(prices)
        print(f"Indexed: {counts['parsed']} parsed, {counts['skipped']} unchanged, "
              f"{counts['removed']} removed, {counts['empty']} empty")

        if args.command == "search":
            query = " ".join(args.query)
            hits = store.search(query)
            if not hits:
                print("No matches.")
            for hit in hits:
                print(f"{hit['ts'][:16]}  {hit['project']:<24} {hit['snippet'].replace(chr(10), ' ')}")
            return 0

        if args.summarize:
            try:
                result = summarize_missing(store, store.sessions(args.since), limit=args.summarize_limit)
                print(f"Summaries: {result['summarized']} new, {result['failed']} failed")
            except SummarizeError as exc:
                print(f"warning: skipping summaries: {exc}", file=sys.stderr)

        if args.command == "stats":
            from atlas.stats import build_stats
            totals = build_stats(store.sessions(args.since), args.tz_offset)["totals"]
            for key, value in totals.items():
                print(f"{key:>12}: {value}")
            return 0

        path = write_report(store, args.out, args.since, args.tz_offset)
        print(f"Wrote {path.resolve()}")
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
