"""
Thin wrapper around yfinance. Returns raw info dicts per ticker.
All network I/O is isolated here so processor.py and renderer.py stay testable.
"""

import sys
from typing import Optional
import yfinance as yf


def fetch_ticker_info(symbol: str) -> Optional[dict]:
    """
    Fetch raw info dict for a single ticker symbol via yfinance.

    Returns None if yfinance returns an empty or obviously invalid response
    (e.g., the ticker does not exist or a network error occurs).
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        # yfinance returns {"trailingPegRatio": None} or similar minimal dicts for bad symbols
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            # Check if we have at least a previous close — ETFs sometimes lack currentPrice
            if info.get("previousClose") is None and info.get("navPrice") is None:
                return None
        return info
    except Exception as exc:
        print(f"  Warning: could not fetch {symbol}: {exc}", file=sys.stderr)
        return None


def fetch_all(watchlist: list[dict]) -> list[tuple[dict, Optional[dict]]]:
    """
    Fetch info for every item in watchlist.

    Returns list of (watchlist_item, info_dict) tuples.
    info_dict is None when fetch failed for that ticker.
    """
    results = []
    for item in watchlist:
        symbol = item.get("symbol", "").upper().strip()
        if not symbol:
            continue
        info = fetch_ticker_info(symbol)
        results.append((item, info))
    return results
