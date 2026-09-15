"""Yahoo Finance price history fetch, isolated behind one function so tests
never need a live network call.
"""

from __future__ import annotations


class DataFetchError(Exception):
    """Raised when Yahoo Finance data can't be retrieved or is malformed."""


def fetch_price_history(tickers: list, period: str = "9mo") -> dict:
    """Fetch daily close prices for every ticker over `period`.

    Returns dict[ticker -> list[(date_str, close_float)]], all tickers
    aligned to the same trading-day dates (rows with any missing ticker
    are dropped so every series has equal length, as compute_rs_lines
    requires).

    Requires the `yfinance` package and network access at runtime; this
    function is the sole place that touches yfinance, so tests mock it
    directly rather than mocking network calls.
    """
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - exercised only without the dependency installed
        raise DataFetchError(
            "The 'yfinance' package is required. Install it with: pip install -r requirements.txt"
        ) from exc

    try:
        raw = yf.download(
            tickers,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
        )
    except Exception as exc:  # noqa: BLE001 - surface the underlying API error verbatim
        raise DataFetchError(f"Yahoo Finance request failed: {exc}") from exc

    if raw is None or raw.empty:
        raise DataFetchError("Yahoo Finance returned no data for the requested tickers")

    result = {}
    for ticker in tickers:
        try:
            closes = raw[ticker]["Close"] if len(tickers) > 1 else raw["Close"]
        except KeyError as exc:
            raise DataFetchError(f"No 'Close' data returned for '{ticker}'") from exc
        closes = closes.dropna()
        if closes.empty:
            raise DataFetchError(f"No usable price history returned for '{ticker}'")
        result[ticker] = [
            (idx.strftime("%Y-%m-%d"), float(value)) for idx, value in closes.items()
        ]

    # Align every ticker to the intersection of dates present for all of them.
    common_dates = set(result[tickers[0]][i][0] for i in range(len(result[tickers[0]])))
    for ticker in tickers[1:]:
        common_dates &= {d for d, _ in result[ticker]}
    if not common_dates:
        raise DataFetchError("No overlapping trading dates across the requested tickers")

    aligned = {
        ticker: [(d, v) for d, v in series if d in common_dates]
        for ticker, series in result.items()
    }
    return aligned
