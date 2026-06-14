#!/usr/bin/env python3
"""Investment Thesis Journal — CLI personal knowledge tool for tracking investment research notes."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import yfinance as yf
    _YFINANCE_AVAILABLE = True
except ImportError:
    yf = None  # type: ignore[assignment]
    _YFINANCE_AVAILABLE = False

DATA_FILE = Path(__file__).parent / "theses.json"

USAGE = """Investment Thesis Journal — track research notes by ticker symbol

Usage:
  python main.py add TICKER "note text"    Add a research note (captures live price)
  python main.py show TICKER               Show all notes + live price for a ticker
  python main.py list                      List all tickers with note counts
  python main.py search QUERY              Search notes by keyword (case-insensitive)
  python main.py delete TICKER ID          Delete a specific note by ID

Examples:
  python main.py add NVDA "Strong GPU moat in AI training. Peak valuation risk but thesis is multi-year."
  python main.py show NVDA
  python main.py search moat
  python main.py delete NVDA 1
"""


class ThesisStore:
    """Persists and queries investment thesis notes in a local JSON file."""

    def __init__(self, path: Path = DATA_FILE):
        self.path = path
        self._data: dict[str, list[dict]] = self._load()

    def _load(self) -> dict[str, list[dict]]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def add(self, ticker: str, note: str, price: Optional[float] = None) -> dict:
        """Add a note for a ticker and return the created entry."""
        ticker = ticker.upper()
        if ticker not in self._data:
            self._data[ticker] = []
        entries = self._data[ticker]
        entry_id = max((e["id"] for e in entries), default=0) + 1
        entry: dict = {
            "id": entry_id,
            "date": datetime.now(timezone.utc).isoformat(),
            "note": note,
            "price_at_note": price,
        }
        entries.append(entry)
        self._save()
        return entry

    def get(self, ticker: str) -> list[dict]:
        """Return all notes for a ticker (empty list if none)."""
        return self._data.get(ticker.upper(), [])

    def list_tickers(self) -> list[tuple[str, int, str]]:
        """Return (ticker, note_count, last_entry_date) for every ticker, sorted alphabetically."""
        result = []
        for ticker, entries in sorted(self._data.items()):
            if entries:
                last_date = max(e["date"] for e in entries)
                result.append((ticker, len(entries), last_date))
        return result

    def search(self, query: str) -> list[tuple[str, dict]]:
        """Return (ticker, entry) pairs where the note contains query (case-insensitive)."""
        query_lower = query.lower()
        results = []
        for ticker, entries in sorted(self._data.items()):
            for entry in entries:
                if query_lower in entry["note"].lower():
                    results.append((ticker, entry))
        return results

    def delete(self, ticker: str, entry_id: int) -> bool:
        """Remove note with entry_id from ticker. Returns True if a note was removed."""
        ticker = ticker.upper()
        entries = self._data.get(ticker, [])
        original_len = len(entries)
        self._data[ticker] = [e for e in entries if e["id"] != entry_id]
        if not self._data[ticker]:
            del self._data[ticker]
        removed = len(self._data.get(ticker, [])) < original_len
        if removed:
            self._save()
        return removed


def fetch_quote(ticker: str) -> Optional[dict]:
    """Fetch current price, change%, and market cap from Yahoo Finance. Returns None on failure."""
    if not _YFINANCE_AVAILABLE or yf is None:
        return None
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if price is None:
            return None
        return {
            "price": float(price),
            "change_pct": info.get("regularMarketChangePercent"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency", "USD"),
        }
    except Exception:
        return None


def format_market_cap(market_cap: Optional[int]) -> str:
    """Format a market cap integer into a human-readable string."""
    if market_cap is None:
        return "N/A"
    if market_cap >= 1_000_000_000_000:
        return f"${market_cap / 1_000_000_000_000:.1f}T"
    if market_cap >= 1_000_000_000:
        return f"${market_cap / 1_000_000_000:.1f}B"
    if market_cap >= 1_000_000:
        return f"${market_cap / 1_000_000:.1f}M"
    return f"${market_cap:,}"


def format_date(iso_date: str) -> str:
    """Format an ISO datetime string to a readable UTC label."""
    try:
        dt = datetime.fromisoformat(iso_date)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return iso_date


def cmd_add(store: ThesisStore, args: list[str]) -> None:
    if len(args) < 2:
        print('Usage: python main.py add TICKER "note text"')
        sys.exit(1)
    ticker = args[0].upper()
    note = args[1]

    quote = fetch_quote(ticker)
    price = quote["price"] if quote else None

    entry = store.add(ticker, note, price)
    print(f"Added note #{entry['id']} for {ticker}.")

    if quote:
        currency = quote.get("currency", "USD")
        change_str = ""
        if quote.get("change_pct") is not None:
            sign = "+" if quote["change_pct"] >= 0 else ""
            change_str = f" ({sign}{quote['change_pct']:.2f}%)"
        print(f"Price at time of note: {currency} {price:.2f}{change_str}")
    else:
        print("(Live price unavailable — note saved without price context.)")


def cmd_show(store: ThesisStore, args: list[str]) -> None:
    if not args:
        print("Usage: python main.py show TICKER")
        sys.exit(1)
    ticker = args[0].upper()
    entries = store.get(ticker)

    if not entries:
        print(f"No notes for {ticker}.")
        return

    quote = fetch_quote(ticker)

    print(f"\n{'=' * 60}")
    print(f"  {ticker}")
    if quote:
        currency = quote.get("currency", "USD")
        change_str = ""
        if quote.get("change_pct") is not None:
            sign = "+" if quote["change_pct"] >= 0 else ""
            change_str = f"  {sign}{quote['change_pct']:.2f}%"
        mktcap_str = f"  Market Cap: {format_market_cap(quote.get('market_cap'))}"
        print(f"  Live: {currency} {quote['price']:.2f}{change_str}{mktcap_str}")
    else:
        print("  (live price unavailable)")
    print(f"{'=' * 60}")

    for entry in entries:
        print(f"\n  [{entry['id']}] {format_date(entry['date'])}")
        if entry.get("price_at_note") is not None:
            print(f"  Price at note: {entry['price_at_note']:.2f}")
        print(f"  {entry['note']}")
    print()


def cmd_list(store: ThesisStore, args: list[str]) -> None:
    tickers = store.list_tickers()
    if not tickers:
        print('No investment notes yet. Try: python main.py add TICKER "your thesis"')
        return

    print(f"\n{'Ticker':<12} {'Notes':>5}  {'Last Entry'}")
    print("-" * 40)
    for ticker, count, last_date in tickers:
        date_str = format_date(last_date)[:10]
        print(f"{ticker:<12} {count:>5}  {date_str}")
    print()


def cmd_search(store: ThesisStore, args: list[str]) -> None:
    if not args:
        print("Usage: python main.py search QUERY")
        sys.exit(1)
    query = " ".join(args)
    results = store.search(query)

    if not results:
        print(f'No notes matching "{query}".')
        return

    print(f'\nFound {len(results)} result(s) for "{query}":\n')
    for ticker, entry in results:
        print(f"  [{ticker}] #{entry['id']} — {format_date(entry['date'])}")
        if entry.get("price_at_note") is not None:
            print(f"  Price at note: {entry['price_at_note']:.2f}")
        print(f"  {entry['note']}")
        print()


def cmd_delete(store: ThesisStore, args: list[str]) -> None:
    if len(args) < 2:
        print("Usage: python main.py delete TICKER ID")
        sys.exit(1)
    ticker = args[0].upper()
    try:
        entry_id = int(args[1])
    except ValueError:
        print(f'Error: ID must be an integer, got "{args[1]}".')
        sys.exit(1)

    if store.delete(ticker, entry_id):
        print(f"Deleted note #{entry_id} for {ticker}.")
    else:
        print(f"No note #{entry_id} found for {ticker}.")


COMMANDS = {
    "add": cmd_add,
    "show": cmd_show,
    "list": cmd_list,
    "search": cmd_search,
    "delete": cmd_delete,
}


def main(argv: Optional[list[str]] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in ("-h", "--help"):
        print(USAGE)
        return

    command = argv[0].lower()
    if command not in COMMANDS:
        print(f"Unknown command: {command}\n")
        print(USAGE)
        sys.exit(1)

    store = ThesisStore()
    COMMANDS[command](store, argv[1:])


if __name__ == "__main__":
    main()
