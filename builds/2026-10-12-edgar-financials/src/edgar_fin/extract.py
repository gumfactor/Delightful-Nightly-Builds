"""Turn a raw SEC companyfacts payload into clean annual series."""
from __future__ import annotations

from datetime import date

from .concepts import ANNUAL_FORMS, CONCEPTS
from .metrics import derive


def _parse(day: str) -> date | None:
    try:
        return date.fromisoformat(day)
    except (TypeError, ValueError):
        return None


def fiscal_year(end: date) -> int:
    """Label a fiscal year by the calendar year in which it mostly falls.

    Year-ends in January/February (retailers) belong to the prior year, matching how
    those companies name their years (fiscal 2023 ends Jan 2024).
    """
    return end.year - 1 if end.month <= 2 else end.year


def _annual_entries(entries: list[dict], kind: str) -> dict[date, dict]:
    """Keep one value per period end: annual, from an annual form, latest filing wins."""
    best: dict[date, dict] = {}
    for entry in entries:
        if entry.get("form") not in ANNUAL_FORMS or "val" not in entry:
            continue
        end = _parse(entry.get("end"))
        if end is None:
            continue
        if kind == "flow":
            start = _parse(entry.get("start"))
            if start is None or not 340 <= (end - start).days <= 380:
                continue
        current = best.get(end)
        if current is None or str(entry.get("filed", "")) >= str(current.get("filed", "")):
            best[end] = entry
    return best


def _series_for_tag(facts: dict, tag: str, kind: str, unit: str) -> dict[int, tuple[float, date]]:
    node = facts.get("us-gaap", {}).get(tag)
    if not node:
        return {}
    entries = node.get("units", {}).get(unit, [])
    by_end = _annual_entries(entries, kind)
    series: dict[int, tuple[float, date]] = {}
    for end in sorted(by_end):
        series[fiscal_year(end)] = (float(by_end[end]["val"]), end)  # later end wins a label clash
    return series


def extract_company(payload: dict, ticker: str, cik: int, years: int = 5) -> dict:
    facts = payload.get("facts", {})
    metrics: dict[str, dict[int, float]] = {}
    end_dates: dict[int, str] = {}
    for name, spec in CONCEPTS.items():
        merged: dict[int, float] = {}
        for tag in spec["tags"]:
            for year, (value, end) in _series_for_tag(facts, tag, spec["kind"], spec["unit"]).items():
                if year not in merged:
                    merged[year] = value
                    end_dates.setdefault(year, end.isoformat())
        metrics[name] = merged

    if "capex" in metrics:
        metrics["capex"] = {y: abs(v) for y, v in metrics["capex"].items()}
    if not metrics["gross_profit"]:
        metrics["gross_profit"] = {
            y: metrics["revenue"][y] - metrics["cost_of_revenue"][y]
            for y in metrics["revenue"] if y in metrics["cost_of_revenue"]}
    else:
        for y, cost in metrics["cost_of_revenue"].items():
            if y not in metrics["gross_profit"] and y in metrics["revenue"]:
                metrics["gross_profit"][y] = metrics["revenue"][y] - cost

    anchor_years = sorted(set(metrics["revenue"]) | set(metrics["net_income"]) | set(metrics["total_assets"]))
    window = anchor_years[-years:]
    # keep one extra prior year internally so the first shown year has a growth rate
    prior = anchor_years[-years - 1:-years]
    keep = set(window) | set(prior)
    metrics = {m: {y: v for y, v in series.items() if y in keep} for m, series in metrics.items()}

    company = {
        "ticker": ticker.upper(), "cik": cik,
        "name": payload.get("entityName") or ticker.upper(),
        "years": window, "metrics": metrics,
        "end_dates": {y: end_dates[y] for y in window if y in end_dates},
    }
    company["derived"] = derive(metrics, window)
    company["metrics"] = {m: {y: v for y, v in s.items() if y in window} for m, s in metrics.items()}
    return company
