"""Derived metrics. Every function returns None instead of raising on bad inputs."""
from __future__ import annotations


def safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def growth(current: float | None, previous: float | None) -> float | None:
    """YoY growth. Undefined for a non-positive base (loss to profit is not a % change)."""
    if current is None or previous is None or previous <= 0:
        return None
    return current / previous - 1


def cagr(first: float | None, last: float | None, periods: int) -> float | None:
    if first is None or last is None or first <= 0 or last <= 0 or periods < 1:
        return None
    return (last / first) ** (1 / periods) - 1


def derive(metrics: dict[str, dict[int, float]], years: list[int]) -> dict[str, dict[int, float]]:
    """Compute ratios for each year in `years`; metrics may hold one earlier year for growth."""
    def val(name: str, year: int) -> float | None:
        return metrics.get(name, {}).get(year)

    out: dict[str, dict[int, float]] = {k: {} for k in (
        "free_cash_flow", "gross_margin", "operating_margin", "net_margin", "roe", "roa",
        "debt_to_equity", "revenue_growth", "net_income_growth")}

    def put(name: str, year: int, value: float | None) -> None:
        if value is not None:
            out[name][year] = value

    for year in years:
        revenue = val("revenue", year)
        ocf, capex = val("operating_cash_flow", year), val("capex", year)
        if ocf is not None and capex is not None:
            put("free_cash_flow", year, ocf - capex)
        put("gross_margin", year, safe_div(val("gross_profit", year), revenue))
        put("operating_margin", year, safe_div(val("operating_income", year), revenue))
        put("net_margin", year, safe_div(val("net_income", year), revenue))
        equity = val("equity", year)
        put("roe", year, safe_div(val("net_income", year), equity) if equity and equity > 0 else None)
        put("roa", year, safe_div(val("net_income", year), val("total_assets", year)))
        put("debt_to_equity", year,
            safe_div(val("long_term_debt", year), equity) if equity and equity > 0 else None)
        put("revenue_growth", year, growth(revenue, val("revenue", year - 1)))
        put("net_income_growth", year, growth(val("net_income", year), val("net_income", year - 1)))
    return out


def summarize(company: dict) -> dict:
    """One-row summary: latest values and multi-year CAGRs."""
    years = company["years"]
    metrics, derived = company["metrics"], company["derived"]
    latest = years[-1] if years else None

    def latest_of(name: str) -> float | None:
        source = metrics.get(name) or {}
        if latest is not None and latest in source:
            return source[latest]
        return (derived.get(name) or {}).get(latest)

    def span_cagr(name: str) -> float | None:
        series = metrics.get(name, {})
        have = [y for y in years if y in series]
        if len(have) < 2:
            return None
        return cagr(series[have[0]], series[have[-1]], have[-1] - have[0])

    return {
        "ticker": company["ticker"], "name": company["name"], "latest_year": latest,
        "revenue": latest_of("revenue"), "net_income": latest_of("net_income"),
        "free_cash_flow": latest_of("free_cash_flow"),
        "gross_margin": latest_of("gross_margin"), "operating_margin": latest_of("operating_margin"),
        "net_margin": latest_of("net_margin"), "roe": latest_of("roe"),
        "debt_to_equity": latest_of("debt_to_equity"),
        "revenue_cagr": span_cagr("revenue"), "net_income_cagr": span_cagr("net_income"),
        "eps_cagr": span_cagr("eps_diluted"),
    }
