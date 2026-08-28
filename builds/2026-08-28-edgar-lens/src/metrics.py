"""Deterministic ratio math and year-over-year anomaly flagging.

Every threshold here is a named constant, chosen and documented up front,
never fit to a specific dataset after the fact. All math guards against
division by zero / missing data by returning None ("not meaningful")
rather than raising or producing NaN/inf.
"""

from __future__ import annotations

from typing import Any

REVENUE_DECLINE_THRESHOLD = -0.10
MARGIN_COMPRESSION_THRESHOLD = -0.05
LEVERAGE_SPIKE_THRESHOLD = 0.5


def safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def net_margin(revenue: float | None, net_income: float | None) -> float | None:
    return safe_divide(net_income, revenue)


def operating_margin(revenue: float | None, operating_income: float | None) -> float | None:
    return safe_divide(operating_income, revenue)


def debt_to_equity(liabilities: float | None, equity: float | None) -> float | None:
    if equity is None or equity <= 0:
        return None
    return safe_divide(liabilities, equity)


def yoy_change(current: float | None, previous: float | None) -> float | None:
    """Fractional change from previous to current (e.g. 0.12 = +12%)."""
    return safe_divide(
        None if current is None or previous is None else current - previous,
        previous,
    )


def compute_yearly_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach derived ratio/YoY fields to a fiscal-year-ascending list of rows.

    Does not mutate the input rows; returns new dicts with metrics merged in.
    """
    enriched: list[dict[str, Any]] = []
    prev: dict[str, Any] | None = None

    for row in rows:
        current = dict(row)
        current["net_margin"] = net_margin(row.get("revenue"), row.get("net_income"))
        current["operating_margin"] = operating_margin(row.get("revenue"), row.get("operating_income"))
        current["debt_to_equity"] = debt_to_equity(row.get("liabilities"), row.get("equity"))
        current["revenue_yoy"] = None
        current["net_margin_delta"] = None
        current["debt_to_equity_delta"] = None

        # Only compare to an immediately preceding fiscal year. A gap (e.g.
        # FY2021 -> FY2023 because FY2022 had no usable tag data) is not a
        # true year-over-year comparison and must not be labeled as one.
        if prev is not None and row["fiscal_year"] == prev["fiscal_year"] + 1:
            current["revenue_yoy"] = yoy_change(row.get("revenue"), prev.get("revenue"))
            if current["net_margin"] is not None and prev.get("net_margin") is not None:
                current["net_margin_delta"] = current["net_margin"] - prev["net_margin"]
            if current["debt_to_equity"] is not None and prev.get("debt_to_equity") is not None:
                current["debt_to_equity_delta"] = current["debt_to_equity"] - prev["debt_to_equity"]

        enriched.append(current)
        prev = current

    return enriched


def flag_anomalies(enriched_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a list of anomaly dicts across all fiscal years in enriched_rows.

    Each anomaly: {fiscal_year, type, detail}. enriched_rows must already
    carry the derived fields from compute_yearly_metrics.
    """
    anomalies: list[dict[str, Any]] = []
    prev_net_income: float | None = None
    prev_fiscal_year: int | None = None

    for row in enriched_rows:
        fy = row["fiscal_year"]

        revenue_yoy = row.get("revenue_yoy")
        if revenue_yoy is not None and revenue_yoy <= REVENUE_DECLINE_THRESHOLD:
            anomalies.append({
                "fiscal_year": fy,
                "type": "revenue_decline",
                "detail": f"Revenue fell {abs(revenue_yoy):.1%} year-over-year",
            })

        margin_delta = row.get("net_margin_delta")
        if margin_delta is not None and margin_delta <= MARGIN_COMPRESSION_THRESHOLD:
            anomalies.append({
                "fiscal_year": fy,
                "type": "margin_compression",
                "detail": f"Net margin dropped {abs(margin_delta) * 100:.1f} percentage points year-over-year",
            })

        leverage_delta = row.get("debt_to_equity_delta")
        if leverage_delta is not None and leverage_delta >= LEVERAGE_SPIKE_THRESHOLD:
            anomalies.append({
                "fiscal_year": fy,
                "type": "leverage_spike",
                "detail": f"Debt-to-equity rose {leverage_delta:.2f}x year-over-year",
            })

        equity = row.get("equity")
        if equity is not None and equity <= 0:
            anomalies.append({
                "fiscal_year": fy,
                "type": "negative_equity",
                "detail": f"Stockholders' equity is {'exactly zero' if equity == 0 else 'negative'} (${'-' if equity < 0 else ''}{abs(equity):,.0f})",
            })

        net_income = row.get("net_income")
        if (
            net_income is not None
            and prev_net_income is not None
            and prev_fiscal_year is not None
            and fy == prev_fiscal_year + 1
            and net_income < 0
            and prev_net_income >= 0
        ):
            anomalies.append({
                "fiscal_year": fy,
                "type": "swing_to_loss",
                "detail": f"Swung from net income of ${prev_net_income:,.0f} to a net loss of ${abs(net_income):,.0f}",
            })

        if net_income is not None:
            prev_net_income = net_income
            prev_fiscal_year = fy

    return anomalies
