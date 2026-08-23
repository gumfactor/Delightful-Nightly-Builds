#!/usr/bin/env python3
"""Trading Book CLI — a live Interactive Brokers portfolio dashboard.

    python main.py sync                  # pull a snapshot from TWS/IB Gateway
    python main.py show                  # print the latest snapshot
    python main.py history --days 14     # print the day-over-day trend
    python main.py render --ai-briefing  # build dashboard.html
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src import ai_briefing, report, storage
from src.ibkr_client import IBKRConnectionError, fetch_snapshot

DB_PATH = Path(__file__).parent / "trading_book.db"
DASHBOARD_PATH = Path(__file__).parent / "dashboard.html"


def cmd_sync(args: argparse.Namespace) -> int:
    try:
        snapshot = fetch_snapshot(
            host=args.host, port=args.port, client_id=args.client_id, timeout=args.timeout
        )
    except IBKRConnectionError as exc:
        print(f"Sync failed: {exc}", file=sys.stderr)
        return 1

    conn = storage.connect(str(DB_PATH))
    storage.init_db(conn)
    snapshot_id = storage.sync_snapshot(conn, snapshot)
    conn.close()
    print(
        f"Synced snapshot {snapshot_id} for account {snapshot['account_id']} "
        f"({len(snapshot['positions'])} positions)."
    )
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    conn = storage.connect(str(DB_PATH))
    storage.init_db(conn)
    latest = storage.get_latest_snapshot(conn)
    conn.close()

    if latest is None:
        print("No snapshot yet. Run `python main.py sync` first.")
        return 0

    print(f"Snapshot: {latest['snapshot_date']} (synced {latest['synced_at']})")
    print(f"Account:            {latest['account_id']}")
    print(f"Net Liquidation:    {latest['net_liquidation']:,.2f}")
    print(f"Total Cash:         {latest['total_cash']:,.2f}")
    print(f"Unrealized P&L:     {latest['unrealized_pnl']:,.2f}")
    print(f"Realized P&L:       {latest['realized_pnl']:,.2f}")
    print(f"Buying Power:       {latest['buying_power']:,.2f}")
    print(f"Positions:          {len(latest['positions'])}")
    for position in latest["positions"][:10]:
        print(
            f"  {position['symbol']:<8} {position['sec_type']:<5} "
            f"qty={position['quantity']:<10g} mkt_value={position['market_value']:,.2f}"
        )
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    conn = storage.connect(str(DB_PATH))
    storage.init_db(conn)
    rows = storage.get_history(conn, days=args.days)
    conn.close()

    if not rows:
        print("No history yet. Run `python main.py sync` first.")
        return 0

    print(f"{'Date':<12} {'Net Liquidation':>16} {'Unrealized P&L':>16}")
    for row in rows:
        print(f"{row['snapshot_date']:<12} {row['net_liquidation']:>16,.2f} {row['unrealized_pnl']:>16,.2f}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    conn = storage.connect(str(DB_PATH))
    storage.init_db(conn)
    snapshots = storage.get_all_snapshots_with_positions(conn)
    conn.close()

    ai_note = None
    if args.ai_briefing and snapshots:
        summary = report.build_aggregate_summary(snapshots)
        ai_note = ai_briefing.build_briefing(summary)

    html = report.render_dashboard(snapshots, ai_note)
    output_path = Path(args.output) if args.output else DASHBOARD_PATH
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py", description="Trading Book — a live IBKR portfolio dashboard."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Pull a snapshot from TWS/IB Gateway.")
    sync_parser.add_argument("--host", default="127.0.0.1")
    sync_parser.add_argument("--port", type=int, default=7497)
    sync_parser.add_argument("--client-id", type=int, default=1)
    sync_parser.add_argument("--timeout", type=float, default=10.0)
    sync_parser.set_defaults(func=cmd_sync)

    show_parser = subparsers.add_parser("show", help="Print the latest snapshot.")
    show_parser.set_defaults(func=cmd_show)

    history_parser = subparsers.add_parser("history", help="Print the day-over-day trend.")
    history_parser.add_argument("--days", type=int, default=None)
    history_parser.set_defaults(func=cmd_history)

    render_parser = subparsers.add_parser("render", help="Build the HTML dashboard.")
    render_parser.add_argument("--output", default=None)
    render_parser.add_argument("--ai-briefing", action="store_true")
    render_parser.set_defaults(func=cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
