#!/usr/bin/env python3
"""CanEcon Pulse — live Canadian economic indicators dashboard.

Usage:
    python3 canecon_pulse.py sync   [--db PATH] [--recent N]
    python3 canecon_pulse.py show   [--db PATH]
    python3 canecon_pulse.py render [--db PATH] [--out PATH] [--no-ai]
    python3 canecon_pulse.py run    [--db PATH] [--out PATH] [--recent N] [--no-ai]

See Manual.md for full documentation.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

from src.briefing import generate_briefing
from src.deltas import compute_deltas
from src.html_report import IndicatorSnapshot, render_dashboard
from src.indicators import INDICATORS
from src.storage import connect, get_history, get_latest_fetched_at, insert_observations

DEFAULT_DB_PATH = "output/canecon.db"
DEFAULT_OUT_PATH = "output/dashboard.html"
DEFAULT_RECENT = 30


def cmd_sync(db_path: str, recent: int) -> None:
    conn = connect(db_path)
    try:
        total_new = 0
        for indicator in INDICATORS:
            observations = indicator.fetch(recent)
            if not observations:
                print(f"  [skip] {indicator.label}: no data returned (API unreachable or empty)")
                continue
            new_count = insert_observations(conn, observations)
            total_new += new_count
            print(f"  [ok]   {indicator.label}: {len(observations)} fetched, {new_count} new")
        print(f"Sync complete. {total_new} new observation(s) stored in {db_path}.")
    finally:
        conn.close()


def _build_snapshots(conn) -> list[IndicatorSnapshot]:
    snapshots = []
    for indicator in INDICATORS:
        history = get_history(conn, indicator.series_id)
        deltas = compute_deltas(history)
        last_fetched_at = get_latest_fetched_at(conn, indicator.series_id)
        snapshots.append(
            IndicatorSnapshot(
                indicator=indicator,
                history=history,
                deltas=deltas,
                last_fetched_at=last_fetched_at,
            )
        )
    return snapshots


def cmd_show(db_path: str) -> None:
    conn = connect(db_path)
    try:
        snapshots = _build_snapshots(conn)
    finally:
        conn.close()

    any_data = False
    for snap in snapshots:
        print(f"\n{snap.indicator.label} ({snap.indicator.unit})")
        if snap.deltas is None:
            print("  No data yet — run `sync` first.")
            continue
        any_data = True
        d = snap.deltas
        print(f"  Latest: {d.latest_value:g} as of {d.latest_date.isoformat()}")
        for label in ("day", "week", "month"):
            period = getattr(d, label)
            if period is None:
                print(f"  {label:<6}: n/a")
            else:
                pct = f"{period.pct_change:+.2f}%" if period.pct_change is not None else "n/a"
                print(f"  {label:<6}: {period.change:+g} ({pct}) vs {period.compare_date.isoformat()}")

    if not any_data:
        print("\nNo indicators have any history yet. Run `sync` to fetch live data.")


def cmd_render(db_path: str, out_path: str, use_ai: bool) -> str:
    conn = connect(db_path)
    try:
        snapshots = _build_snapshots(conn)
    finally:
        conn.close()

    deltas_by_label = {snap.indicator.label: snap.deltas for snap in snapshots}
    api_key = os.environ.get("ANTHROPIC_API_KEY") if use_ai else None
    briefing_text, briefing_source = generate_briefing(deltas_by_label, api_key)

    html_doc = render_dashboard(
        snapshots=snapshots,
        briefing_text=briefing_text,
        briefing_source=briefing_source,
        generated_at=datetime.now(timezone.utc),
    )

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(html_doc)

    print(f"Dashboard written to {out_path} (briefing source: {briefing_source})")
    return out_path


def cmd_run(db_path: str, out_path: str, recent: int, use_ai: bool) -> None:
    cmd_sync(db_path, recent)
    cmd_render(db_path, out_path, use_ai)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CanEcon Pulse — Canadian economic indicators dashboard")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Fetch latest indicator data and store it locally")
    sync_parser.add_argument("--db", default=DEFAULT_DB_PATH)
    sync_parser.add_argument("--recent", type=int, default=DEFAULT_RECENT)

    show_parser = subparsers.add_parser("show", help="Print a terminal summary of stored indicators")
    show_parser.add_argument("--db", default=DEFAULT_DB_PATH)

    render_parser = subparsers.add_parser("render", help="Render the HTML dashboard from stored data")
    render_parser.add_argument("--db", default=DEFAULT_DB_PATH)
    render_parser.add_argument("--out", default=DEFAULT_OUT_PATH)
    render_parser.add_argument("--no-ai", action="store_true", help="Skip the AI briefing even if a key is set")

    run_parser = subparsers.add_parser("run", help="sync followed by render")
    run_parser.add_argument("--db", default=DEFAULT_DB_PATH)
    run_parser.add_argument("--out", default=DEFAULT_OUT_PATH)
    run_parser.add_argument("--recent", type=int, default=DEFAULT_RECENT)
    run_parser.add_argument("--no-ai", action="store_true", help="Skip the AI briefing even if a key is set")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "sync":
        cmd_sync(args.db, args.recent)
    elif args.command == "show":
        cmd_show(args.db)
    elif args.command == "render":
        cmd_render(args.db, args.out, use_ai=not args.no_ai)
    elif args.command == "run":
        cmd_run(args.db, args.out, args.recent, use_ai=not args.no_ai)
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
