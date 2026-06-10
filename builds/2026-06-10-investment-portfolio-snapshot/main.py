"""
Investment Portfolio Snapshot — entry point.

Usage:
  python3 main.py [--watchlist path/to/watchlist.json] [--output report.html]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.fetcher import fetch_ticker
from src.report import generate_report


def load_watchlist(path: Path) -> list[dict]:
    """Load and validate watchlist.json; returns list of {symbol, label?} dicts."""
    if not path.exists():
        print(f"Error: watchlist file not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in watchlist: {exc}", file=sys.stderr)
        sys.exit(1)

    if "tickers" not in data or not isinstance(data["tickers"], list):
        print("Error: watchlist.json must have a 'tickers' list", file=sys.stderr)
        sys.exit(1)

    if not data["tickers"]:
        print("Warning: watchlist is empty — nothing to fetch.", file=sys.stderr)
        return []

    return data["tickers"]


def main() -> None:
    build_dir = Path(__file__).parent

    parser = argparse.ArgumentParser(description="Generate a stock watchlist snapshot HTML report.")
    parser.add_argument(
        "--watchlist",
        default=str(build_dir / "watchlist.json"),
        help="Path to watchlist.json (default: watchlist.json in build folder)",
    )
    parser.add_argument(
        "--output",
        default=str(build_dir / "report.html"),
        help="Output path for the HTML report (default: report.html in build folder)",
    )
    args = parser.parse_args()

    watchlist = load_watchlist(Path(args.watchlist))
    output_path = Path(args.output)

    print(f"Fetching data for {len(watchlist)} ticker(s)...")
    ticker_data = []
    for entry in watchlist:
        symbol = entry.get("symbol", "").strip().upper()
        label = entry.get("label") or symbol
        if not symbol:
            print("Warning: skipping entry with no symbol", file=sys.stderr)
            continue
        print(f"  {symbol}... ", end="", flush=True)
        data = fetch_ticker(symbol, label=label)
        if data.error:
            print(f"FAILED ({data.error})")
        else:
            price_display = f"${data.price:.2f}" if data.price else "no price"
            print(f"ok ({price_display})")
        ticker_data.append(data)

    html = generate_report(ticker_data)
    output_path.write_text(html, encoding="utf-8")
    print(f"\nReport written to: {output_path}")
    print(f"File size: {output_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
