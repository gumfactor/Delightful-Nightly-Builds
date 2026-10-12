"""Synthetic companyfacts payloads, used by --demo and by the tests.

The companies are fictional. Numbers are generated, not real SEC data.
"""
from __future__ import annotations


def _flow(tag_values: dict[int, float], month_end: str = "12-31", form: str = "10-K") -> list[dict]:
    return [{"start": f"{y}-01-01", "end": f"{y}-{month_end}", "val": v, "form": form,
             "filed": f"{y + 1}-02-15", "fp": "FY", "fy": y} for y, v in tag_values.items()]


def _instant(tag_values: dict[int, float], form: str = "10-K") -> list[dict]:
    return [{"end": f"{y}-12-31", "val": v, "form": form, "filed": f"{y + 1}-02-15",
             "fp": "FY", "fy": y} for y, v in tag_values.items()]


def make_payload(name: str, years: list[int], revenue0: float, growth: float, gross: float,
                 operating: float, net: float, capex_ratio: float, debt_ratio: float,
                 shares: float = 1e9) -> dict:
    revenue = {y: revenue0 * (1 + growth) ** i for i, y in enumerate(years)}
    us_gaap = {
        "Revenues": {"units": {"USD": _flow(revenue)}},
        "CostOfRevenue": {"units": {"USD": _flow({y: v * (1 - gross) for y, v in revenue.items()})}},
        "OperatingIncomeLoss": {"units": {"USD": _flow({y: v * operating for y, v in revenue.items()})}},
        "NetIncomeLoss": {"units": {"USD": _flow({y: v * net for y, v in revenue.items()})}},
        "EarningsPerShareDiluted": {"units": {"USD/shares": _flow({y: v * net / shares for y, v in revenue.items()})}},
        "NetCashProvidedByUsedInOperatingActivities": {
            "units": {"USD": _flow({y: v * (net + 0.04) for y, v in revenue.items()})}},
        "PaymentsToAcquirePropertyPlantAndEquipment": {
            "units": {"USD": _flow({y: v * capex_ratio for y, v in revenue.items()})}},
        "Assets": {"units": {"USD": _instant({y: v * 1.6 for y, v in revenue.items()})}},
        "Liabilities": {"units": {"USD": _instant({y: v * 0.9 for y, v in revenue.items()})}},
        "StockholdersEquity": {"units": {"USD": _instant({y: v * 0.7 for y, v in revenue.items()})}},
        "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": _instant({y: v * 0.15 for y, v in revenue.items()})}},
        "LongTermDebtNoncurrent": {"units": {"USD": _instant({y: v * debt_ratio for y, v in revenue.items()})}},
    }
    return {"cik": 0, "entityName": name, "facts": {"us-gaap": us_gaap}}


DEMO_YEARS = [2019, 2020, 2021, 2022, 2023, 2024]

DEMO_COMPANIES: dict[str, dict] = {
    "NWND": {"cik": 9000001, "payload": make_payload(
        "Northwind Sample Corp (synthetic)", DEMO_YEARS, 41e9, 0.12, 0.62, 0.31, 0.24, 0.04, 0.20)},
    "FBRK": {"cik": 9000002, "payload": make_payload(
        "Fabrikam Demo Inc (synthetic)", DEMO_YEARS, 118e9, 0.04, 0.38, 0.14, 0.10, 0.07, 0.45)},
    "CNTS": {"cik": 9000003, "payload": make_payload(
        "Contoso Example Ltd (synthetic)", DEMO_YEARS, 9.5e9, 0.21, 0.71, 0.05, 0.02, 0.03, 0.12)},
}
