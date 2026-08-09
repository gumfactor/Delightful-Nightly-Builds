"""Portfolio Lab — real market data fetcher.

Run this locally (not in the build container — see PRD.md) to pull real
historical prices for a fixed, diversified 12-asset teaching basket via
`yfinance`, compute annualized return/volatility/covariance/correlation,
and write `data.js` for the browser app to load directly.

Usage:
    python fetch_data.py [--years N] [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252

# A fixed, diversified 12-asset teaching basket: 8 equity sectors plus a
# gold ETF and a long-term Treasury ETF specifically chosen because they
# tend to have low or negative correlation with equities — the app's
# correlation heatmap and two-asset mixer are much more instructive when
# at least a couple of pairs behave very differently from "everything
# moves together." AAPL/MSFT are deliberately both included (both
# large-cap tech) as the counter-example: a highly-correlated pair that
# does NOT diversify much.
DEFAULT_TICKERS = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology"},
    "MSFT": {"name": "Microsoft Corp.", "sector": "Technology"},
    "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Financials"},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare"},
    "XOM": {"name": "Exxon Mobil Corp.", "sector": "Energy"},
    "PG": {"name": "Procter & Gamble Co.", "sector": "Consumer Staples"},
    "HD": {"name": "Home Depot Inc.", "sector": "Consumer Discretionary"},
    "CAT": {"name": "Caterpillar Inc.", "sector": "Industrials"},
    "NEE": {"name": "NextEra Energy Inc.", "sector": "Utilities"},
    "AMT": {"name": "American Tower Corp.", "sector": "Real Estate"},
    "GLD": {"name": "SPDR Gold Shares", "sector": "Commodities (Gold ETF)"},
    "TLT": {"name": "iShares 20+ Year Treasury Bond ETF", "sector": "Fixed Income"},
}

MIN_TICKERS_REQUIRED = 4


def fetch_price_series(ticker: str, years: int, downloader) -> Optional[pd.Series]:
    """Fetch a single ticker's daily close series. Returns None on failure
    instead of raising, so one bad ticker never aborts the whole run.

    `downloader` is injected (defaults to yfinance) so tests can supply a
    fake with no network access.
    """
    try:
        history = downloader(ticker, period=f"{years}y", interval="1d", auto_adjust=True)
    except Exception as exc:  # noqa: BLE001 - any network/library failure is non-fatal here
        print(f"  ! {ticker}: fetch failed ({exc}) — skipping", file=sys.stderr)
        return None

    if history is None or history.empty or "Close" not in history:
        print(f"  ! {ticker}: no data returned — skipping", file=sys.stderr)
        return None

    series = history["Close"].dropna()
    if len(series) < 30:
        print(f"  ! {ticker}: only {len(series)} rows — skipping", file=sys.stderr)
        return None

    series.name = ticker
    return series


def align_log_returns(price_series_by_ticker: dict[str, pd.Series]) -> pd.DataFrame:
    """Compute daily log returns per ticker and align on common trading
    days (inner join), dropping any date where a ticker is missing so the
    covariance matrix is computed on a fully-rectangular, consistent
    sample."""
    prices = pd.concat(price_series_by_ticker.values(), axis=1, join="inner")
    prices.columns = list(price_series_by_ticker.keys())
    log_returns = np.log(prices / prices.shift(1))
    return log_returns.dropna()


def compute_stats(returns: pd.DataFrame) -> dict:
    """Given a DataFrame of aligned daily log returns (columns = tickers),
    compute annualized mean return, annualized volatility, and the
    annualized covariance + correlation matrices, in a fixed ticker order."""
    tickers = list(returns.columns)
    mean_daily = returns.mean()
    mean_return = (mean_daily * TRADING_DAYS_PER_YEAR).to_dict()
    volatility = (returns.std(ddof=1) * (TRADING_DAYS_PER_YEAR ** 0.5)).to_dict()

    cov_daily = returns.cov()
    cov_annual = cov_daily * TRADING_DAYS_PER_YEAR
    corr = returns.corr()

    cov_matrix = [[float(cov_annual.loc[a, b]) for b in tickers] for a in tickers]
    corr_matrix = [[float(corr.loc[a, b]) for b in tickers] for a in tickers]

    return {
        "tickers": tickers,
        "mean_return": {t: float(mean_return[t]) for t in tickers},
        "volatility": {t: float(volatility[t]) for t in tickers},
        "cov_matrix": cov_matrix,
        "corr_matrix": corr_matrix,
    }


def build_dataset(
    years: int,
    ticker_meta: dict[str, dict],
    downloader,
    now: Optional[datetime] = None,
) -> dict:
    """Fetch, align, and compute the full dataset dict ready to serialize.
    Raises ValueError if too few tickers survive fetching to build a
    meaningful covariance matrix."""
    prices_by_ticker: dict[str, pd.Series] = {}
    for ticker in ticker_meta:
        series = fetch_price_series(ticker, years, downloader)
        if series is not None:
            prices_by_ticker[ticker] = series

    if len(prices_by_ticker) < MIN_TICKERS_REQUIRED:
        raise ValueError(
            f"Only {len(prices_by_ticker)} of {len(ticker_meta)} tickers returned usable data "
            f"(need at least {MIN_TICKERS_REQUIRED}). Check network access and ticker symbols."
        )

    returns = align_log_returns(prices_by_ticker)
    if len(returns) < 30:
        raise ValueError(f"Only {len(returns)} aligned trading days after joining — need at least 30.")

    stats = compute_stats(returns)
    meta = {t: ticker_meta[t] for t in stats["tickers"]}

    generated_at = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "generated_at": generated_at,
        "years": years,
        "tickers": stats["tickers"],
        "meta": meta,
        "mean_return": stats["mean_return"],
        "volatility": stats["volatility"],
        "cov_matrix": stats["cov_matrix"],
        "corr_matrix": stats["corr_matrix"],
    }


def write_data_js(dataset: dict, path: Path) -> None:
    payload = json.dumps(dataset, indent=2)
    path.write_text(
        "// Generated by fetch_data.py — real historical market data.\n"
        "// Do not edit by hand; re-run fetch_data.py to refresh.\n"
        f"window.PORTFOLIO_DATA = {payload};\n",
        encoding="utf-8",
    )


def write_dataset_json(dataset: dict, path: Path) -> None:
    path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")


def default_downloader(ticker: str, period: str, interval: str, auto_adjust: bool):
    import yfinance as yf

    return yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=auto_adjust)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch real market data for Portfolio Lab.")
    parser.add_argument("--years", type=int, default=3, help="Years of daily history to fetch (default: 3)")
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parent / "data.js", help="Path to write data.js (default: ./data.js)"
    )
    args = parser.parse_args(argv)

    print(f"Fetching {args.years} year(s) of daily data for {len(DEFAULT_TICKERS)} tickers...")
    try:
        dataset = build_dataset(args.years, DEFAULT_TICKERS, default_downloader)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    write_data_js(dataset, args.out)
    json_path = args.out.parent / "data" / "dataset.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    write_dataset_json(dataset, json_path)

    print(f"Wrote {args.out} and {json_path}")
    print(f"Tickers used: {', '.join(dataset['tickers'])}")
    print(f"Trading days in sample: {len(dataset['tickers'])} assets aligned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
