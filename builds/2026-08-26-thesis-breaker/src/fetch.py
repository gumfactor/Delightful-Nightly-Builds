"""Real fundamentals fetch layer for Thesis Breaker.

The live path calls yfinance, which requires network access the user has
locally but the build/test container does not. Every function here takes
the ticker factory as a parameter so tests can substitute a fake object
shaped like yfinance.Ticker without any network call ever occurring.
"""
from __future__ import annotations

from typing import Any, Callable, Optional


def _safe_get(info: dict, *keys: str) -> Optional[float]:
    for key in keys:
        value = info.get(key)
        if value is not None:
            return value
    return None


def _quarterly_series(financials: Any, row_names: list[str]) -> Optional[list[float]]:
    """Pull a row from a yfinance quarterly statement DataFrame by trying
    each candidate row name in order. Returns values most-recent-quarter-first,
    or None if the statement is unavailable or none of the row names match.
    """
    if financials is None:
        return None
    try:
        index = list(financials.index)
    except AttributeError:
        return None
    for name in row_names:
        if name in index:
            row = financials.loc[name]
            values = [float(v) for v in row.tolist() if v is not None and v == v]
            return values if values else None
    return None


def _yoy_growth(revenue_by_quarter: Optional[list[float]]) -> Optional[list[float]]:
    """Given raw quarterly revenue (most-recent-first, needs 5 points to
    derive 4 YoY comparisons against the same quarter a year earlier),
    return YoY growth rates most-recent-first. None if insufficient data.
    """
    if revenue_by_quarter is None or len(revenue_by_quarter) < 5:
        return None
    growth = []
    for i in range(4):
        current = revenue_by_quarter[i]
        year_ago = revenue_by_quarter[i + 4] if i + 4 < len(revenue_by_quarter) else None
        if year_ago is None or year_ago == 0:
            break
        growth.append((current - year_ago) / abs(year_ago))
    return growth if growth else None


def _insider_transactions(raw: Any) -> Optional[list[dict]]:
    if raw is None:
        return None
    try:
        records = raw.to_dict("records")
    except AttributeError:
        return None
    result = []
    for row in records:
        insider = row.get("Insider") or row.get("Name")
        transaction = row.get("Transaction") or row.get("Text")
        shares = row.get("Shares")
        value = row.get("Value")
        if insider is None or transaction is None:
            continue
        result.append({
            "insider": str(insider),
            "transaction": str(transaction),
            "shares": float(shares) if shares is not None else None,
            "value": float(value) if value is not None else None,
        })
    return result if result else None


def fetch_ticker_data(ticker: str, ticker_factory: Callable[[str], Any]) -> dict:
    """Fetch real fundamentals for `ticker` using `ticker_factory` (normally
    yfinance.Ticker, injected so tests can substitute a fake).

    Missing fields are None, never guessed or defaulted to zero.
    """
    handle = ticker_factory(ticker)
    info = getattr(handle, "info", None) or {}

    revenue_by_quarter = _quarterly_series(
        getattr(handle, "quarterly_income_stmt", None) or getattr(handle, "quarterly_financials", None),
        ["Total Revenue", "TotalRevenue"],
    )
    operating_income = _quarterly_series(
        getattr(handle, "quarterly_income_stmt", None) or getattr(handle, "quarterly_financials", None),
        ["Operating Income", "OperatingIncome"],
    )

    operating_margin = None
    if revenue_by_quarter and operating_income:
        n = min(len(revenue_by_quarter), len(operating_income))
        operating_margin = [
            operating_income[i] / revenue_by_quarter[i]
            for i in range(n)
            if revenue_by_quarter[i]
        ] or None

    return {
        "ticker": ticker.upper(),
        "sector": info.get("sector"),
        "trailing_pe": _safe_get(info, "trailingPE"),
        "forward_pe": _safe_get(info, "forwardPE"),
        "price_to_sales": _safe_get(info, "priceToSalesTrailing12Months"),
        "debt_to_equity": _safe_get(info, "debtToEquity"),
        "quarterly_revenue_yoy_growth": _yoy_growth(revenue_by_quarter),
        "quarterly_operating_margin": operating_margin,
        "insider_transactions": _insider_transactions(getattr(handle, "insider_transactions", None)),
    }
