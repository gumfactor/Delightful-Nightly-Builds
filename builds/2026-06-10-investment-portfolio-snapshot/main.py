"""
Investment Research Platform — entry point.

Report mode (default):
  python3 main.py [--watchlist FILE] [--output FILE] [--open]

Thesis commands:
  python3 main.py add TICKER "note text"
  python3 main.py show TICKER
  python3 main.py list
  python3 main.py search QUERY
  python3 main.py delete TICKER ID
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from src.fetcher import fetch_ticker, format_price
from src.report import generate_report
from src.theses import ThesisStore


_BUILD_DIR = Path(__file__).parent
_THESES_PATH = _BUILD_DIR / "theses.json"

_THESIS_COMMANDS = {"add", "show", "list", "search", "delete"}


# ── Report mode ───────────────────────────────────────────────────────────────

def load_watchlist(path: Path) -> list[dict]:
    """Load and validate watchlist.json; return list of {symbol, label?} dicts."""
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


def run_report(args: argparse.Namespace, store: ThesisStore) -> None:
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
            price_display = f"${data.price:.2f}" if data.price is not None else "no price"
            print(f"ok ({price_display})")
        ticker_data.append(data)

    html = generate_report(ticker_data, theses=store.all_data())
    output_path.write_text(html, encoding="utf-8")
    print(f"\nReport written to: {output_path}")
    print(f"File size: {output_path.stat().st_size:,} bytes")

    if args.open_browser:
        webbrowser.open(output_path.resolve().as_uri())


# ── Thesis commands ───────────────────────────────────────────────────────────

def _format_date(iso_date: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_date)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return iso_date


def cmd_add(store: ThesisStore, argv: list[str]) -> None:
    if len(argv) < 2:
        print('Usage: python3 main.py add TICKER "note text"')
        sys.exit(1)
    ticker = argv[0].upper()
    note = argv[1]

    print(f"Fetching live price for {ticker}... ", end="", flush=True)
    td = fetch_ticker(ticker)
    price = td.price if not td.error else None
    if price is not None:
        print(f"${price:.2f}")
    else:
        print("unavailable")

    entry = store.add(ticker, note, price)
    print(f"Added note #{entry['id']} for {ticker}.")
    if price is not None:
        print(f"Price at time of note: {format_price(price, td.currency)}")
    else:
        print("(Note saved without price context — live data unavailable.)")


def cmd_show(store: ThesisStore, argv: list[str]) -> None:
    if not argv:
        print("Usage: python3 main.py show TICKER")
        sys.exit(1)
    ticker = argv[0].upper()
    entries = store.get(ticker)
    if not entries:
        print(f"No notes for {ticker}.")
        return

    print(f"\n{'=' * 60}")
    print(f"  {ticker}")
    td = fetch_ticker(ticker)
    if not td.error and td.price is not None:
        change_str = ""
        if td.change_pct is not None:
            sign = "+" if td.change_pct >= 0 else ""
            change_str = f"  {sign}{td.change_pct:.2f}%"
        print(f"  Live: {format_price(td.price, td.currency)}{change_str}")
    else:
        print("  (live price unavailable)")
    print(f"{'=' * 60}")

    for entry in entries:
        print(f"\n  [{entry['id']}] {_format_date(entry['date'])}")
        if entry.get("price_at_note") is not None:
            noted_at = entry["price_at_note"]
            price_line = f"  Price at note: ${noted_at:.2f}"
            if not td.error and td.price is not None and noted_at > 0:
                pct = (td.price - noted_at) / noted_at * 100.0
                sign = "+" if pct >= 0 else ""
                price_line += f"  ({sign}{pct:.1f}% since)"
            print(price_line)
        print(f"  {entry['note']}")
    print()


def cmd_list(store: ThesisStore, _argv: list[str]) -> None:
    tickers = store.list_tickers()
    if not tickers:
        print('No investment notes yet. Try: python3 main.py add TICKER "your thesis"')
        return
    print(f"\n{'Ticker':<12} {'Notes':>5}  Last Entry")
    print("-" * 40)
    for ticker, count, last_date in tickers:
        print(f"{ticker:<12} {count:>5}  {last_date[:10]}")
    print()


def cmd_search(store: ThesisStore, argv: list[str]) -> None:
    if not argv:
        print("Usage: python3 main.py search QUERY")
        sys.exit(1)
    query = " ".join(argv)
    results = store.search(query)
    if not results:
        print(f'No notes matching "{query}".')
        return
    print(f'\nFound {len(results)} result(s) for "{query}":\n')
    for ticker, entry in results:
        print(f"  [{ticker}] #{entry['id']} — {_format_date(entry['date'])}")
        if entry.get("price_at_note") is not None:
            print(f"  Price at note: ${entry['price_at_note']:.2f}")
        print(f"  {entry['note']}")
        print()


def cmd_delete(store: ThesisStore, argv: list[str]) -> None:
    if len(argv) < 2:
        print("Usage: python3 main.py delete TICKER ID")
        sys.exit(1)
    ticker = argv[0].upper()
    try:
        entry_id = int(argv[1])
    except ValueError:
        print(f'Error: ID must be an integer, got "{argv[1]}".')
        sys.exit(1)
    if store.delete(ticker, entry_id):
        print(f"Deleted note #{entry_id} for {ticker}.")
    else:
        print(f"No note #{entry_id} found for {ticker}.")


_THESIS_DISPATCH = {
    "add": cmd_add,
    "show": cmd_show,
    "list": cmd_list,
    "search": cmd_search,
    "delete": cmd_delete,
}


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    store = ThesisStore(_THESES_PATH)

    # Route thesis subcommands before argparse sees the args
    if len(sys.argv) > 1 and sys.argv[1].lower() in _THESIS_COMMANDS:
        _THESIS_DISPATCH[sys.argv[1].lower()](store, sys.argv[2:])
        return

    parser = argparse.ArgumentParser(
        description="Investment Research Platform — watchlist report + thesis journal."
    )
    parser.add_argument(
        "--watchlist",
        default=str(_BUILD_DIR / "watchlist.json"),
        help="Path to watchlist.json (default: watchlist.json in build folder)",
    )
    parser.add_argument(
        "--output",
        default=str(_BUILD_DIR / "report.html"),
        help="Output path for the HTML report (default: report.html in build folder)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        dest="open_browser",
        help="Open the report in the default browser after generating",
    )
    args = parser.parse_args()
    run_report(args, store)


if __name__ == "__main__":
    main()
