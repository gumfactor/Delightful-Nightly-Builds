"""
Investment Watchlist Dashboard — main entry point.

Usage:
  python3 main.py                    # fetch and save output/dashboard.html
  python3 main.py --text             # print text table to stdout
  python3 main.py --output PATH      # save HTML to a custom path
  python3 main.py --watchlist FILE   # use an alternate watchlist JSON
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Allow running from the build folder root
sys.path.insert(0, str(Path(__file__).parent))

from src.fetcher import fetch_all
from src.processor import process_ticker_data
from src.renderer import render_html, render_text


def load_watchlist(path: Path) -> list[dict]:
    """Load and validate a watchlist JSON file."""
    if not path.exists():
        print(f"Error: watchlist file not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, list) or not data:
        print(f"Error: {path} must contain a non-empty JSON array", file=sys.stderr)
        sys.exit(1)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Yahoo Finance data for a watchlist and render a dashboard."
    )
    parser.add_argument(
        "--watchlist",
        default=str(Path(__file__).parent / "watchlist.json"),
        help="Path to watchlist JSON file (default: watchlist.json in build folder)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for HTML file (default: output/dashboard.html)",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Print a plain-text table to stdout instead of writing HTML",
    )
    args = parser.parse_args()

    watchlist_path = Path(args.watchlist)
    watchlist = load_watchlist(watchlist_path)

    print(f"Fetching data for {len(watchlist)} tickers...", flush=True)

    raw_results = fetch_all(watchlist)

    tickers: list[dict] = []
    for item, info in raw_results:
        symbol = item.get("symbol", "").upper().strip()
        label = item.get("label", symbol)
        notes = item.get("notes", "")
        if info is None:
            print(f"  Warning: no data returned for {symbol} — skipping", file=sys.stderr)
            # Include a minimal placeholder so the symbol at least appears
            tickers.append({
                "symbol": symbol, "label": label, "name": symbol, "notes": notes,
                "price": None, "prev_close": None, "change_abs": None, "change_pct": None,
                "volume": None, "week52_low": None, "week52_high": None,
                "week52_position": None, "market_cap": None, "pe_ratio": None,
                "analyst_target": None,
                "fmt_price": "N/A", "fmt_change_abs": "N/A", "fmt_change_pct": "N/A",
                "fmt_volume": "N/A", "fmt_market_cap": "N/A", "fmt_pe": "N/A",
                "fmt_target": "N/A", "fmt_52low": "N/A", "fmt_52high": "N/A",
            })
        else:
            tickers.append(process_ticker_data(symbol, label, notes, info))

    if args.text:
        print(render_text(tickers))
        return

    html = render_html(tickers)

    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "dashboard.html"

    output_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
