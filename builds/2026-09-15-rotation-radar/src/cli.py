"""Command-line entry point wiring data fetch -> analytics -> storage -> AI -> report."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from . import ai, analytics, report, storage
from .data import fetch_price_history


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rotation-radar",
        description="Sector Relative Rotation Graph explorer using free Yahoo Finance data.",
    )
    parser.add_argument("--benchmark", default=analytics.DEFAULT_BENCHMARK, help="Benchmark ticker (default: SPY)")
    parser.add_argument(
        "--sectors",
        nargs="+",
        default=None,
        help="Sector tickers to analyze (default: the 11 SPDR sector ETFs)",
    )
    parser.add_argument("--period", default="9mo", help="yfinance lookback period (default: 9mo)")
    parser.add_argument("--ratio-window", type=int, default=10, help="RS smoothing window in trading days (default: 10)")
    parser.add_argument("--momentum-window", type=int, default=10, help="Momentum lookback window in trading days (default: 10)")
    parser.add_argument("--tail-length", type=int, default=10, help="Number of trailing points to plot per sector (default: 10)")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI commentary even if ANTHROPIC_API_KEY is set")
    parser.add_argument("--output", default="rotation_radar.html", help="Output HTML file path")
    parser.add_argument("--db-path", default="rotation_radar.db", help="SQLite database path for run history")
    return parser


def run(args: argparse.Namespace, fetch_fn=None, ai_fn=None) -> dict:
    """Execute one full rotation-radar pass. Returns a result dict for callers/tests.

    `fetch_fn` and `ai_fn` are injectable for testing; production callers leave
    them as None to use the real implementations.
    """
    fetch = fetch_fn if fetch_fn is not None else fetch_price_history
    generate_commentary = ai_fn if ai_fn is not None else ai.generate_commentary

    sectors = args.sectors if args.sectors else list(analytics.DEFAULT_SECTORS)
    tickers = [args.benchmark] + sectors

    raw_prices = fetch(tickers, period=args.period)
    snapshots = analytics.compute_rotation(
        raw_prices,
        benchmark=args.benchmark,
        ratio_window=args.ratio_window,
        momentum_window=args.momentum_window,
        tail_length=args.tail_length,
    )

    conn = storage.connect(args.db_path)
    previous = storage.get_previous_run_snapshot(conn)
    transitions = storage.compute_transitions(previous, snapshots)
    run_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    run_id = storage.save_run(conn, run_timestamp, snapshots)

    commentary = (
        ai.generate_commentary(snapshots, transitions, api_key="")
        if args.no_ai
        else generate_commentary(snapshots, transitions)
    )

    html_text = report.build_html(
        snapshots, transitions, commentary, args.benchmark, run_timestamp, args.tail_length
    )
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_text)

    history_rows = []
    for ticker in sorted(snapshots.keys()):
        history_rows.extend(
            (ticker, ts, r, m, q) for ts, r, m, q in storage.get_history(conn, ticker)
        )
    csv_path = args.output.rsplit(".", 1)[0] + "_history.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        f.write(report.build_csv(history_rows))

    conn.close()
    return {
        "run_id": run_id,
        "html_path": args.output,
        "csv_path": csv_path,
        "db_path": args.db_path,
        "snapshots": snapshots,
        "transitions": transitions,
        "commentary": commentary,
    }


def main(argv=None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001 - surface a clean error instead of a traceback
        print(f"rotation-radar failed: {exc}", file=sys.stderr)
        return 1

    changed = [t for t in result["transitions"] if t.changed]
    print(f"Rotation Radar: {len(result['snapshots'])} sectors analyzed vs. {args.benchmark}.")
    if changed:
        print(f"{len(changed)} sector(s) changed quadrant since the last run:")
        for t in changed:
            print(f"  {t.ticker}: {t.previous_quadrant} -> {t.current_quadrant}")
    else:
        print("No quadrant changes since the last run.")
    print(f"Dashboard written to {result['html_path']}")
    print(f"History CSV written to {result['csv_path']}")
    return 0
