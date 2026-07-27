"""yfinance data access, isolated behind an injectable factory for testing."""
from typing import Callable, Dict, List, Optional, Tuple

METRIC_FIELDS = (
    "price",
    "market_cap",
    "pe_trailing",
    "pe_forward",
    "peg_ratio",
    "profit_margin",
    "revenue_growth",
    "target_mean_price",
    "week52_low",
    "week52_high",
)

_INFO_MAP = {
    "market_cap": "marketCap",
    "pe_trailing": "trailingPE",
    "pe_forward": "forwardPE",
    "peg_ratio": "pegRatio",
    "profit_margin": "profitMargins",
    "revenue_growth": "revenueGrowth",
    "target_mean_price": "targetMeanPrice",
    "week52_low": "fiftyTwoWeekLow",
    "week52_high": "fiftyTwoWeekHigh",
}


def _default_factory():
    import yfinance
    return yfinance.Ticker


def empty_snapshot_metrics() -> Dict[str, Optional[float]]:
    return {field: None for field in METRIC_FIELDS}


def fetch_snapshot(
    ticker: str, ticker_factory: Optional[Callable[[str], object]] = None
) -> Dict[str, Optional[float]]:
    """Fetch current valuation/margin metrics for one ticker.

    Never raises — any failure (network, missing fields, malformed response)
    results in a metrics dict of all None values, so a sync run can continue
    with the remaining tickers.
    """
    factory = ticker_factory or _default_factory()
    metrics = empty_snapshot_metrics()
    try:
        info = factory(ticker).info or {}
    except Exception:
        return metrics

    price = info.get("currentPrice")
    if price is None:
        price = info.get("regularMarketPrice")
    metrics["price"] = _to_float(price)

    for field, info_key in _INFO_MAP.items():
        metrics[field] = _to_float(info.get(info_key))

    return metrics


def fetch_price_history(
    ticker: str,
    ticker_factory: Optional[Callable[[str], object]] = None,
    period: str = "1y",
) -> List[Tuple[str, float]]:
    """Fetch daily closing prices as a plain list of (YYYY-MM-DD, close) tuples.

    Never raises — a fetch failure returns an empty list.
    """
    factory = ticker_factory or _default_factory()
    try:
        history = factory(ticker).history(period=period)
    except Exception:
        return []

    rows: List[Tuple[str, float]] = []
    if history is None:
        return rows

    try:
        for index, row in history.iterrows():
            close = _to_float(row.get("Close") if hasattr(row, "get") else row["Close"])
            if close is None:
                continue
            date_str = index.strftime("%Y-%m-%d") if hasattr(index, "strftime") else str(index)[:10]
            rows.append((date_str, close))
    except Exception:
        return []

    return rows


def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result:  # NaN check without importing math
        return None
    return result
