"""Price-delta and sector-aggregate calculations. All functions are None-safe."""
from datetime import date
from typing import Dict, List, Optional, Tuple

MIN_DAYS_FOR_RELIABLE_1Y = 300


def _mean(values: List[Optional[float]]) -> Optional[float]:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return sum(present) / len(present)


def compute_price_deltas(history: List[Tuple[str, float]]) -> Dict[str, Optional[float]]:
    """Compute 1-day and ~1-year percent price changes from a date-ordered history list."""
    result = {
        "latest": None,
        "since_prev_pct": None,
        "since_1y_pct": None,
        "since_1y_reliable": False,
    }
    if not history:
        return result

    latest_date_str, latest = history[-1]
    result["latest"] = latest

    if len(history) >= 2:
        prev = history[-2][1]
        if prev:
            result["since_prev_pct"] = (latest - prev) / prev * 100

    first_date_str, first = history[0]
    if first:
        result["since_1y_pct"] = (latest - first) / first * 100
        try:
            span_days = (
                date.fromisoformat(latest_date_str) - date.fromisoformat(first_date_str)
            ).days
            result["since_1y_reliable"] = span_days >= MIN_DAYS_FOR_RELIABLE_1Y
        except ValueError:
            result["since_1y_reliable"] = False

    return result


def compute_sector_aggregates(enriched_snapshots: List[Dict]) -> Dict:
    """Compute sector-wide aggregates from a list of snapshot dicts.

    Each dict may optionally include 'since_1y_pct' (from compute_price_deltas)
    to enable top-mover/laggard identification.
    """
    market_caps = [s.get("market_cap") for s in enriched_snapshots]
    pes = [s.get("pe_trailing") for s in enriched_snapshots]
    margins = [s.get("profit_margin") for s in enriched_snapshots]
    growth_positive = sum(
        1 for s in enriched_snapshots if (s.get("revenue_growth") or 0) > 0
    )

    movers = [
        s for s in enriched_snapshots if s.get("since_1y_pct") is not None
    ]
    top_mover = max(movers, key=lambda s: s["since_1y_pct"], default=None)
    laggard = min(movers, key=lambda s: s["since_1y_pct"], default=None)

    total_market_cap = sum(v for v in market_caps if v is not None) or None

    return {
        "total_market_cap": total_market_cap,
        "avg_pe_trailing": _mean(pes),
        "avg_profit_margin": _mean(margins),
        "growth_positive_count": growth_positive,
        "companies_tracked": len(enriched_snapshots),
        "top_mover": (
            {"ticker": top_mover["ticker"], "name": top_mover["name"], "pct": top_mover["since_1y_pct"]}
            if top_mover
            else None
        ),
        "laggard": (
            {"ticker": laggard["ticker"], "name": laggard["name"], "pct": laggard["since_1y_pct"]}
            if laggard
            else None
        ),
    }
