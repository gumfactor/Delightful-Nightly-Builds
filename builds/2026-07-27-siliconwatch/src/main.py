"""SiliconWatch CLI — sector-comparative dashboard over AI-infrastructure/semiconductor companies."""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence

from ai_narrative import build_template_narrative, generate_narrative
from config import ConfigError, load_tickers
from data_fetch import fetch_price_history, fetch_snapshot
from dashboard import render_dashboard
from metrics import compute_price_deltas, compute_sector_aggregates
from storage import SiliconWatchDB


def utc_today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_universe(config_path: Optional[str], tickers_arg: Optional[str]) -> List[dict]:
    universe = load_tickers(config_path)
    if not tickers_arg:
        return universe

    requested = [t.strip().upper() for t in tickers_arg.split(",") if t.strip()]
    by_ticker = {u["ticker"]: u for u in universe}
    return [
        by_ticker.get(t, {"ticker": t, "name": t, "subsector": "Custom"})
        for t in requested
    ]


def cmd_sync(args: argparse.Namespace) -> None:
    universe = resolve_universe(args.config, args.tickers)
    snapshot_date = utc_today_str()
    fetched_at = utc_now_iso()

    db = SiliconWatchDB(args.db)
    try:
        synced = 0
        failed = []
        for entry in universe:
            metrics = fetch_snapshot(entry["ticker"])
            if metrics["price"] is None:
                failed.append(entry["ticker"])
            row = {**entry, "snapshot_date": snapshot_date, "fetched_at": fetched_at, **metrics}
            db.upsert_snapshot(row)
            history = fetch_price_history(entry["ticker"])
            db.insert_price_history(entry["ticker"], history)
            synced += 1
    finally:
        db.close()

    print(f"Synced {synced} ticker(s) for {snapshot_date}.")
    if failed:
        print(f"Warning: no price data returned for: {', '.join(failed)}")


def cmd_report(args: argparse.Namespace) -> None:
    db = SiliconWatchDB(args.db)
    try:
        latest = db.get_latest_snapshots()
        if not latest:
            print("No data yet — run `sync` first.")
            sys.exit(1)

        enriched = []
        price_history_by_ticker = {}
        for row in latest:
            history = db.get_price_history(row["ticker"])
            price_history_by_ticker[row["ticker"]] = history
            deltas = compute_price_deltas(history)
            enriched.append({**row, **deltas})

        aggregates = compute_sector_aggregates(enriched)
        sector_pe_trend = db.sector_pe_by_date()
    finally:
        db.close()

    if args.ai:
        narrative, narrative_source = generate_narrative(aggregates)
    else:
        narrative, narrative_source = build_template_narrative(aggregates), "template"

    html_out = render_dashboard(
        enriched,
        price_history_by_ticker,
        sector_pe_trend,
        aggregates,
        narrative,
        narrative_source,
        generated_at=utc_now_iso(),
    )
    Path(args.output).write_text(html_out)
    print(f"Wrote dashboard to {args.output}")


def cmd_list(args: argparse.Namespace) -> None:
    universe = load_tickers(args.config)
    for entry in universe:
        print(f"{entry['ticker']:<6} {entry['subsector']:<30} {entry['name']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="siliconwatch")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Fetch live data and store a snapshot")
    sync_parser.add_argument("--db", default="siliconwatch.db")
    sync_parser.add_argument("--config", help="Path to a custom ticker JSON config")
    sync_parser.add_argument("--tickers", help="Comma-separated ticker list to sync instead of the full universe")
    sync_parser.set_defaults(func=cmd_sync)

    report_parser = subparsers.add_parser("report", help="Render the HTML dashboard from stored data")
    report_parser.add_argument("--db", default="siliconwatch.db")
    report_parser.add_argument("--output", default="siliconwatch_report.html")
    report_parser.add_argument("--ai", action="store_true", help="Generate an AI sector narrative via ANTHROPIC_API_KEY")
    report_parser.set_defaults(func=cmd_report)

    list_parser = subparsers.add_parser("list", help="Print the configured ticker universe")
    list_parser.add_argument("--config", help="Path to a custom ticker JSON config")
    list_parser.set_defaults(func=cmd_list)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
