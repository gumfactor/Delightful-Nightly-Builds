"""
Pure functions for processing raw yfinance info dicts into structured ticker records.
No I/O, no network calls — fully testable without mocking external services.
"""

from typing import Optional


def format_price(value: Optional[float]) -> str:
    """Format a dollar price value, returning 'N/A' for None."""
    if value is None:
        return "N/A"
    return f"${value:,.2f}"


def format_change_pct(value: Optional[float]) -> str:
    """Format a percentage change with sign prefix, returning 'N/A' for None."""
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def format_change_abs(value: Optional[float]) -> str:
    """Format an absolute dollar change with sign prefix, returning 'N/A' for None."""
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}${abs(value):,.2f}"


def format_market_cap(value: Optional[float]) -> str:
    """Format a market cap in human-readable billions/trillions, 'N/A' for None."""
    if value is None:
        return "N/A"
    if value >= 1e12:
        return f"${value / 1e12:.2f}T"
    if value >= 1e9:
        return f"${value / 1e9:.2f}B"
    if value >= 1e6:
        return f"${value / 1e6:.2f}M"
    return f"${value:,.0f}"


def format_volume(value: Optional[float]) -> str:
    """Format volume in human-readable millions, 'N/A' for None."""
    if value is None:
        return "N/A"
    if value >= 1e6:
        return f"{value / 1e6:.1f}M"
    if value >= 1e3:
        return f"{value / 1e3:.1f}K"
    return str(int(value))


def format_pe(value: Optional[float]) -> str:
    """Format a P/E ratio to one decimal place, 'N/A' for None."""
    if value is None:
        return "N/A"
    return f"{value:.1f}x"


def calc_52week_position(
    price: Optional[float],
    low: Optional[float],
    high: Optional[float],
) -> Optional[float]:
    """
    Return how far price sits within the 52-week range as a 0–100 percentage.
    Returns None if any input is None or if low == high (degenerate range).
    """
    if price is None or low is None or high is None:
        return None
    if high <= low:
        return None
    position = (price - low) / (high - low) * 100
    # Clamp to [0, 100] in case price is outside the stated range (data lag)
    return max(0.0, min(100.0, position))


def process_ticker_data(symbol: str, label: str, notes: str, info: dict) -> dict:
    """
    Extract and compute all display fields from a raw yfinance info dict.

    All computed fields default to None when the source key is absent — callers
    should handle None via the format_* helpers above.
    """
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")

    if price is not None and prev_close is not None:
        change_abs: Optional[float] = price - prev_close
        change_pct: Optional[float] = (change_abs / prev_close) * 100 if prev_close != 0 else None
    else:
        change_abs = None
        change_pct = None

    week52_low: Optional[float] = info.get("fiftyTwoWeekLow")
    week52_high: Optional[float] = info.get("fiftyTwoWeekHigh")
    week52_position = calc_52week_position(price, week52_low, week52_high)

    return {
        "symbol": symbol,
        "label": label,
        "name": info.get("longName") or info.get("shortName") or symbol,
        "price": price,
        "prev_close": prev_close,
        "change_abs": change_abs,
        "change_pct": change_pct,
        "volume": info.get("regularMarketVolume") or info.get("volume"),
        "week52_low": week52_low,
        "week52_high": week52_high,
        "week52_position": week52_position,
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "analyst_target": info.get("targetMeanPrice"),
        "notes": notes,
        # Preformatted display strings
        "fmt_price": format_price(price),
        "fmt_change_abs": format_change_abs(change_abs),
        "fmt_change_pct": format_change_pct(change_pct),
        "fmt_volume": format_volume(info.get("regularMarketVolume") or info.get("volume")),
        "fmt_market_cap": format_market_cap(info.get("marketCap")),
        "fmt_pe": format_pe(info.get("trailingPE")),
        "fmt_target": format_price(info.get("targetMeanPrice")),
        "fmt_52low": format_price(week52_low),
        "fmt_52high": format_price(week52_high),
    }
