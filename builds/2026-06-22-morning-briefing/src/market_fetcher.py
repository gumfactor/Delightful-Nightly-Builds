"""Market data fetcher — yfinance wrapper with price change classification."""
from __future__ import annotations

from typing import Any

import yfinance as yf


def calculate_change_pct(current: float, previous: float) -> float:
    """Return percentage change from previous to current price, or 0.0 if previous is 0."""
    if previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, 2)


def classify_move(change_pct: float, threshold: float = 1.0) -> str:
    """Return 'up', 'down', or 'flat' based on change percentage and threshold."""
    if change_pct >= threshold:
        return "up"
    if change_pct <= -threshold:
        return "down"
    return "flat"


def format_price(price: float, currency: str = "USD") -> str:
    """Format price with dollar sign for USD/CAD currencies."""
    symbol = "$" if currency in ("USD", "CAD") else ""
    return f"{symbol}{price:,.2f}"


def fetch_ticker_data(ticker: str) -> dict[str, Any]:
    """Fetch current price and previous close for a single ticker via yfinance."""
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        current = getattr(info, "last_price", None) or getattr(info, "regularMarketPrice", None)
        prev_close = getattr(info, "previous_close", None) or getattr(info, "regularMarketPreviousClose", None)
        currency = getattr(info, "currency", "USD") or "USD"

        if current is None or prev_close is None:
            return {"ticker": ticker, "error": "price data unavailable"}

        change_pct = calculate_change_pct(float(current), float(prev_close))
        move = classify_move(change_pct)
        return {
            "ticker": ticker,
            "current": round(float(current), 2),
            "prev_close": round(float(prev_close), 2),
            "change_pct": change_pct,
            "move": move,
            "currency": currency,
            "formatted_price": format_price(float(current), currency),
            "formatted_change": f"{'+' if change_pct >= 0 else ''}{change_pct:.2f}%",
        }
    except Exception as exc:
        return {"ticker": ticker, "error": str(exc)}


def fetch_portfolio_data(watchlist: list[str]) -> dict:
    """Fetch price data for all tickers and compute summary statistics."""
    results = []
    errors = []
    for ticker in watchlist:
        data = fetch_ticker_data(ticker)
        if "error" in data:
            errors.append(data)
        else:
            results.append(data)

    movers_up = sorted(
        [r for r in results if r["move"] == "up"],
        key=lambda x: x["change_pct"],
        reverse=True,
    )
    movers_down = sorted(
        [r for r in results if r["move"] == "down"],
        key=lambda x: x["change_pct"],
    )

    return {
        "tickers": results,
        "errors": errors,
        "top_gainers": movers_up[:3],
        "top_losers": movers_down[:3],
        "total_up": len(movers_up),
        "total_down": len(movers_down),
        "total_flat": len([r for r in results if r["move"] == "flat"]),
    }
