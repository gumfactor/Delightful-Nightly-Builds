"""Fetch stock data from Yahoo Finance and normalize it into TickerData."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TickerData:
    symbol: str
    name: str
    price: float | None
    change_pct: float | None       # 1-day % change
    week52_high: float | None
    week52_low: float | None
    pe_ratio: float | None
    market_cap: int | None         # raw integer
    volume: int | None
    history: list[float]           # up to 90 daily closes, oldest first
    currency: str
    error: str | None              # non-None if fetch failed


def _nan_to_none(value: Any) -> Any:
    """Convert float NaN to None; pass other values through."""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def normalize_info(info: dict[str, Any], history_closes: list[float], label: str | None = None) -> TickerData:
    """
    Build a TickerData from a yfinance info dict and a list of closing prices.
    All potentially-missing fields are gracefully handled.
    """
    symbol = info.get("symbol", "")
    name = label or info.get("longName") or info.get("shortName") or symbol
    price = _nan_to_none(info.get("currentPrice") or info.get("regularMarketPrice"))
    currency = info.get("currency", "USD") or "USD"

    # 1-day % change: (currentPrice - previousClose) / previousClose * 100
    prev_close = _nan_to_none(info.get("previousClose") or info.get("regularMarketPreviousClose"))
    change_pct: float | None = None
    if price is not None and prev_close and prev_close != 0:
        change_pct = (price - prev_close) / prev_close * 100.0

    week52_high = _nan_to_none(info.get("fiftyTwoWeekHigh"))
    week52_low = _nan_to_none(info.get("fiftyTwoWeekLow"))
    pe_ratio = _nan_to_none(info.get("trailingPE") or info.get("forwardPE"))
    market_cap = _nan_to_none(info.get("marketCap"))
    volume = _nan_to_none(info.get("volume") or info.get("regularMarketVolume"))

    if market_cap is not None:
        market_cap = int(market_cap)
    if volume is not None:
        volume = int(volume)

    return TickerData(
        symbol=symbol,
        name=name,
        price=price,
        change_pct=change_pct,
        week52_high=week52_high,
        week52_low=week52_low,
        pe_ratio=pe_ratio,
        market_cap=market_cap,
        volume=volume,
        history=history_closes,
        currency=currency,
        error=None,
    )


def fetch_ticker(symbol: str, label: str | None = None) -> TickerData:
    """
    Fetch current info and 3-month history for a single ticker.
    Returns a TickerData with error set if the fetch fails.
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}

        # Fetch 3 months of daily closes (approx 90 trading days)
        hist = ticker.history(period="3mo", interval="1d", auto_adjust=True)
        history_closes: list[float] = []
        if hist is not None and not hist.empty and "Close" in hist.columns:
            history_closes = [float(v) for v in hist["Close"].dropna().tolist()]

        return normalize_info(info, history_closes, label=label or symbol)

    except Exception as exc:
        return TickerData(
            symbol=symbol,
            name=label or symbol,
            price=None,
            change_pct=None,
            week52_high=None,
            week52_low=None,
            pe_ratio=None,
            market_cap=None,
            volume=None,
            history=[],
            currency="USD",
            error=str(exc),
        )


# ── Formatters ────────────────────────────────────────────────────────────────

def format_price(price: float | None, currency: str = "USD") -> str:
    """Format a price as a currency string, e.g. '$150.23' or '—'."""
    if price is None:
        return "—"
    symbol = "$" if currency in ("USD", "CAD") else currency + " "
    return f"{symbol}{price:,.2f}"


def format_change(change_pct: float | None) -> str:
    """Format a 1-day % change with sign, e.g. '+2.45%' or '-0.87%' or '—'."""
    if change_pct is None:
        return "—"
    sign = "+" if change_pct >= 0 else ""
    return f"{sign}{change_pct:.2f}%"


def format_market_cap(market_cap: int | None) -> str:
    """Format market cap with T/B/M suffix, e.g. '2.85T' or '—'."""
    if market_cap is None:
        return "—"
    cap = float(market_cap)
    if cap >= 1e12:
        return f"{cap / 1e12:.2f}T"
    if cap >= 1e9:
        return f"{cap / 1e9:.2f}B"
    if cap >= 1e6:
        return f"{cap / 1e6:.2f}M"
    return f"{cap:,.0f}"


def format_volume(volume: int | None) -> str:
    """Format volume with K/M suffix for readability."""
    if volume is None:
        return "—"
    vol = float(volume)
    if vol >= 1e6:
        return f"{vol / 1e6:.1f}M"
    if vol >= 1e3:
        return f"{vol / 1e3:.0f}K"
    return str(volume)


def format_pe(pe_ratio: float | None) -> str:
    """Format P/E ratio to 1 decimal place, or '—'."""
    if pe_ratio is None:
        return "—"
    return f"{pe_ratio:.1f}"


def format_52w_range(low: float | None, high: float | None) -> str:
    """Format a 52-week range as 'LOW — HIGH'."""
    if low is None and high is None:
        return "—"
    low_str = f"{low:,.2f}" if low is not None else "?"
    high_str = f"{high:,.2f}" if high is not None else "?"
    return f"{low_str} — {high_str}"
