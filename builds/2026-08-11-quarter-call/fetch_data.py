"""Fetch real historical stock data for Quarter Call and bake it into data/rounds-data.js.

This repo's build container has no network access to Yahoo Finance (the egress
proxy returns 403 on query1.finance.yahoo.com), so this file ships with
ROUNDS_DATA = null. Run this script on your own machine to populate it with
real historical data:

    pip install -r requirements.txt
    python3 fetch_data.py

Every round uses genuine daily closing prices for a curated list of well-known
tickers and a historical decision date at least one full quarter in the past —
nothing here is synthetic or fabricated.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

TRADING_DAYS_PER_YEAR = 252
CHART_WINDOW_DAYS = 126  # ~6 trading months shown before the decision date
FORWARD_WINDOW_DAYS = 63  # ~1 trading quarter after the decision date
FLAT_BAND_PCT = 5.0  # |pct change| below this over the forward quarter => "flat"
MIN_CHART_DAYS = 100  # below this much trailing history, skip the round
MIN_FORWARD_DAYS = 50  # below this much forward history, skip the round

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "rounds-data.js"


@dataclass(frozen=True)
class RoundSpec:
    ticker: str
    decision_date: str  # YYYY-MM-DD
    company: str
    sector: str
    industry: str


# 48 hand-curated (ticker, historical decision date) pairs across 11 sectors,
# spanning 2016-2023 so every forward quarter is fully settled. Sector/industry
# and company name are hand-verified rather than pulled from yfinance's often
# inconsistent .info dict, which changes shape between library versions.
CURATED_ROUNDS = [
    RoundSpec("AAPL", "2019-03-29", "Apple Inc.", "Technology", "Consumer Electronics"),
    RoundSpec("MSFT", "2016-06-30", "Microsoft Corporation", "Technology", "Software—Infrastructure"),
    RoundSpec("NVDA", "2018-12-31", "NVIDIA Corporation", "Technology", "Semiconductors"),
    RoundSpec("INTC", "2020-09-30", "Intel Corporation", "Technology", "Semiconductors"),
    RoundSpec("ADBE", "2017-06-30", "Adobe Inc.", "Technology", "Software—Application"),
    RoundSpec("JNJ", "2018-03-30", "Johnson & Johnson", "Healthcare", "Drug Manufacturers—General"),
    RoundSpec("PFE", "2016-09-30", "Pfizer Inc.", "Healthcare", "Drug Manufacturers—General"),
    RoundSpec("UNH", "2019-06-28", "UnitedHealth Group Inc.", "Healthcare", "Healthcare Plans"),
    RoundSpec("MRK", "2020-06-30", "Merck & Co. Inc.", "Healthcare", "Drug Manufacturers—General"),
    RoundSpec("ABT", "2017-12-29", "Abbott Laboratories", "Healthcare", "Medical Devices"),
    RoundSpec("JPM", "2018-06-29", "JPMorgan Chase & Co.", "Financial Services", "Banks—Diversified"),
    RoundSpec("BAC", "2016-12-30", "Bank of America Corp.", "Financial Services", "Banks—Diversified"),
    RoundSpec("GS", "2019-09-30", "The Goldman Sachs Group Inc.", "Financial Services", "Capital Markets"),
    RoundSpec("WFC", "2017-03-31", "Wells Fargo & Company", "Financial Services", "Banks—Diversified"),
    RoundSpec("AXP", "2020-12-31", "American Express Company", "Financial Services", "Credit Services"),
    RoundSpec("XOM", "2016-06-30", "Exxon Mobil Corporation", "Energy", "Oil & Gas Integrated"),
    RoundSpec("CVX", "2018-09-28", "Chevron Corporation", "Energy", "Oil & Gas Integrated"),
    RoundSpec("COP", "2020-03-31", "ConocoPhillips", "Energy", "Oil & Gas E&P"),
    RoundSpec("SLB", "2019-06-28", "SLB (Schlumberger)", "Energy", "Oil & Gas Equipment & Services"),
    RoundSpec("AMZN", "2017-09-29", "Amazon.com Inc.", "Consumer Discretionary", "Internet Retail"),
    RoundSpec("HD", "2016-12-30", "The Home Depot Inc.", "Consumer Discretionary", "Home Improvement Retail"),
    RoundSpec("NKE", "2018-05-31", "Nike Inc.", "Consumer Discretionary", "Footwear & Accessories"),
    RoundSpec("MCD", "2019-12-31", "McDonald's Corporation", "Consumer Discretionary", "Restaurants"),
    RoundSpec("SBUX", "2020-09-30", "Starbucks Corporation", "Consumer Discretionary", "Restaurants"),
    RoundSpec("PG", "2017-06-30", "The Procter & Gamble Company", "Consumer Staples", "Household & Personal Products"),
    RoundSpec("KO", "2016-03-31", "The Coca-Cola Company", "Consumer Staples", "Beverages—Non-Alcoholic"),
    RoundSpec("WMT", "2019-03-29", "Walmart Inc.", "Consumer Staples", "Discount Stores"),
    RoundSpec("PEP", "2018-12-31", "PepsiCo Inc.", "Consumer Staples", "Beverages—Non-Alcoholic"),
    RoundSpec("BA", "2017-12-29", "The Boeing Company", "Industrials", "Aerospace & Defense"),
    RoundSpec("HON", "2016-09-30", "Honeywell International Inc.", "Industrials", "Conglomerates"),
    RoundSpec("UPS", "2019-06-28", "United Parcel Service Inc.", "Industrials", "Integrated Freight & Logistics"),
    RoundSpec("CAT", "2020-12-31", "Caterpillar Inc.", "Industrials", "Farm & Heavy Construction Machinery"),
    RoundSpec("NEE", "2017-09-29", "NextEra Energy Inc.", "Utilities", "Utilities—Regulated Electric"),
    RoundSpec("DUK", "2019-03-29", "Duke Energy Corporation", "Utilities", "Utilities—Regulated Electric"),
    RoundSpec("SO", "2016-06-30", "The Southern Company", "Utilities", "Utilities—Regulated Electric"),
    RoundSpec("AEP", "2020-06-30", "American Electric Power Co.", "Utilities", "Utilities—Regulated Electric"),
    RoundSpec("LIN", "2018-06-29", "Linde plc", "Materials", "Specialty Chemicals"),
    RoundSpec("NEM", "2019-12-31", "Newmont Corporation", "Materials", "Gold"),
    RoundSpec("DD", "2017-03-31", "DuPont de Nemours Inc.", "Materials", "Specialty Chemicals"),
    RoundSpec("FCX", "2020-09-30", "Freeport-McMoRan Inc.", "Materials", "Copper"),
    RoundSpec("PLD", "2018-09-28", "Prologis Inc.", "Real Estate", "REIT—Industrial"),
    RoundSpec("SPG", "2016-12-30", "Simon Property Group Inc.", "Real Estate", "REIT—Retail"),
    RoundSpec("AMT", "2019-06-28", "American Tower Corporation", "Real Estate", "REIT—Specialty"),
    RoundSpec("O", "2020-03-31", "Realty Income Corporation", "Real Estate", "REIT—Retail"),
    RoundSpec("DIS", "2017-12-29", "The Walt Disney Company", "Communication Services", "Entertainment"),
    RoundSpec("VZ", "2016-03-31", "Verizon Communications Inc.", "Communication Services", "Telecom Services"),
    RoundSpec("CMCSA", "2019-09-30", "Comcast Corporation", "Communication Services", "Telecom Services"),
    RoundSpec("T", "2020-12-31", "AT&T Inc.", "Communication Services", "Telecom Services"),
]


def classify_outcome(pct_change: float) -> str:
    """Classify a forward-quarter percent change as up / down / flat."""
    if pct_change > FLAT_BAND_PCT:
        return "up"
    if pct_change < -FLAT_BAND_PCT:
        return "down"
    return "flat"


def annualized_volatility(closes: list[float]) -> float:
    """Annualized volatility (%) from daily log returns of a close-price series."""
    if len(closes) < 3:
        return 0.0
    log_returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    mean = sum(log_returns) / len(log_returns)
    variance = sum((r - mean) ** 2 for r in log_returns) / (len(log_returns) - 1)
    daily_std = math.sqrt(variance)
    return daily_std * math.sqrt(TRADING_DAYS_PER_YEAR) * 100


def trailing_return_pct(closes: list[float]) -> float:
    """Simple percent return from the first to the last close in a series."""
    if not closes or closes[0] == 0:
        return 0.0
    return (closes[-1] - closes[0]) / closes[0] * 100


def build_round(spec: RoundSpec, history: list[tuple[str, float]]) -> Optional[dict]:
    """Build one game round from a spec plus a sorted (date_str, close) history.

    `history` must be sorted ascending by date and should span well before and
    after `spec.decision_date`. Returns None if there isn't enough real data
    on either side of the decision date to build a full round.
    """
    dates = [d for d, _ in history]
    decision_idx = next((i for i, d in enumerate(dates) if d >= spec.decision_date), None)
    if decision_idx is None:
        return None

    chart_start = max(0, decision_idx - CHART_WINDOW_DAYS)
    chart_slice = history[chart_start : decision_idx + 1]
    if len(chart_slice) < MIN_CHART_DAYS:
        return None

    forward_end_idx = decision_idx + FORWARD_WINDOW_DAYS
    if forward_end_idx >= len(history):
        return None
    forward_slice = history[decision_idx : forward_end_idx + 1]
    if len(forward_slice) < MIN_FORWARD_DAYS:
        return None

    decision_close = chart_slice[-1][1]
    forward_close = forward_slice[-1][1]
    pct_change = (forward_close - decision_close) / decision_close * 100
    closes_for_metrics = [c for _, c in chart_slice]

    return {
        "id": f"{spec.ticker}-{spec.decision_date}",
        "ticker": spec.ticker,
        "company": spec.company,
        "sector": spec.sector,
        "industry": spec.industry,
        "decisionDate": spec.decision_date,
        "chart": [{"date": d, "close": round(c, 2)} for d, c in chart_slice],
        "metrics": {
            "trailingReturnPct": round(trailing_return_pct(closes_for_metrics), 1),
            "annualizedVolatilityPct": round(annualized_volatility(closes_for_metrics), 1),
        },
        "forward": {
            "endDate": forward_slice[-1][0],
            "endClose": round(forward_close, 2),
            "pctChange": round(pct_change, 1),
            "outcome": classify_outcome(pct_change),
            "chart": [{"date": d, "close": round(c, 2)} for d, c in forward_slice],
        },
    }


def fetch_history(ticker: str, decision_date: str) -> list[tuple[str, float]]:
    """Fetch real daily closes around decision_date from Yahoo Finance via yfinance."""
    import yfinance as yf

    start = (datetime.strptime(decision_date, "%Y-%m-%d") - timedelta(days=260)).strftime("%Y-%m-%d")
    end = (datetime.strptime(decision_date, "%Y-%m-%d") + timedelta(days=140)).strftime("%Y-%m-%d")
    df = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=True)
    if df is None or df.empty:
        return []
    return [(idx.strftime("%Y-%m-%d"), float(row["Close"])) for idx, row in df.iterrows()]


def to_js(rounds: list[dict]) -> str:
    payload = json.dumps(rounds, indent=2)
    return (
        "// Generated by fetch_data.py from real Yahoo Finance history. Do not hand-edit.\n"
        "// Re-run `python3 fetch_data.py` to refresh.\n"
        f"const ROUNDS_DATA = {payload};\n"
    )


def main() -> int:
    rounds: list[dict] = []
    skipped: list[str] = []

    for spec in CURATED_ROUNDS:
        try:
            history = fetch_history(spec.ticker, spec.decision_date)
        except Exception as exc:  # a single ticker's network/API failure isn't fatal
            print(f"  ! {spec.ticker} ({spec.decision_date}): fetch failed — {exc}", file=sys.stderr)
            skipped.append(spec.ticker)
            continue

        result = build_round(spec, history)
        if result is None:
            print(f"  ! {spec.ticker} ({spec.decision_date}): insufficient history, skipped", file=sys.stderr)
            skipped.append(spec.ticker)
            continue

        rounds.append(result)
        outcome = result["forward"]["outcome"]
        pct = result["forward"]["pctChange"]
        print(f"  + {spec.ticker} ({spec.decision_date}): {outcome} {pct:+.1f}%")

    if not rounds:
        print("No rounds could be built — check your network connection and try again.", file=sys.stderr)
        return 1

    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(to_js(rounds))
    print(
        f"\nWrote {len(rounds)} rounds to {OUTPUT_FILE} "
        f"({len(skipped)} skipped: {', '.join(skipped) if skipped else 'none'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
