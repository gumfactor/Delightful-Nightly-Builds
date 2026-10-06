from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .demo import demo_transactions
from .detect import detect
from .forecast import to_ics, upcoming_charges
from .parsers import ParseError, dedupe, parse_file
from .report import build_json, render_html
from .rules import Rules, RulesError, load_rules

DEMO_RULES = Rules(cancelled={"Goodlife Fitness": date(2026, 7, 1)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recurring",
        description="Detect recurring charges in bank/credit-card CSV exports. Runs fully offline.",
    )
    parser.add_argument("files", nargs="*", help="CSV statement exports")
    parser.add_argument("--demo", action="store_true", help="use synthetic demo data")
    parser.add_argument("--rules", help="rules JSON (ignore / aliases / cancelled)")
    parser.add_argument("--out", default="recurring-report.html", help="HTML report path")
    parser.add_argument("--ics", help="write upcoming charges to this .ics file")
    parser.add_argument("--json", dest="json_out", help="write detected series to this JSON file")
    parser.add_argument("--days", type=int, default=60, help="forecast window in days (default 60)")
    parser.add_argument("--today", help="override today's date (YYYY-MM-DD)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        today = date.fromisoformat(args.today) if args.today else date.today()
    except ValueError:
        print("error: --today must be YYYY-MM-DD", file=sys.stderr)
        return 2
    if args.days < 1:
        print("error: --days must be at least 1", file=sys.stderr)
        return 2
    if not args.files and not args.demo:
        print("error: give at least one CSV file or use --demo", file=sys.stderr)
        return 2

    try:
        rules = load_rules(args.rules)
        if args.demo:
            transactions = demo_transactions()
            today = date(2026, 10, 6) if not args.today else today
            if not args.rules:
                rules = DEMO_RULES
        else:
            transactions = []
            for name in args.files:
                transactions.extend(parse_file(name))
            transactions = dedupe(transactions)
    except (ParseError, RulesError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    as_of = max(t.date for t in transactions)
    series = detect(transactions, rules, as_of=as_of)
    upcoming = upcoming_charges(series, max(today, as_of) if args.demo else today, args.days)

    Path(args.out).write_text(render_html(series, upcoming, today, len(transactions)), encoding="utf-8")
    if args.ics:
        Path(args.ics).write_text(to_ics(upcoming), encoding="utf-8", newline="")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(build_json(series, upcoming), indent=2), encoding="utf-8")

    active = [s for s in series if s.status in ("active", "zombie")]
    monthly = sum(s.monthly_cost for s in active)
    print(f"Read {len(transactions)} purchases; found {len(series)} recurring charges "
          f"({len(active)} live, ~${monthly:,.2f}/month).")
    print(f"Report: {args.out}")
    return 0
