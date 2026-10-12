"""XBRL tag aliases for each normalised metric.

Aliases are tried in priority order, independently for every fiscal year, so a
company that switched tags (e.g. ASC 606 revenue adoption) still gets a full series.
"""

# kind: "flow" = duration over a period, "instant" = balance at a date
# unit: key into the SEC "units" dict
CONCEPTS: dict[str, dict] = {
    "revenue": {
        "kind": "flow", "unit": "USD", "label": "Revenue",
        "tags": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                 "RevenueFromContractWithCustomerIncludingAssessedTax",
                 "SalesRevenueNet", "SalesRevenueGoodsNet"],
    },
    "cost_of_revenue": {
        "kind": "flow", "unit": "USD", "label": "Cost of revenue",
        "tags": ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"],
    },
    "gross_profit": {
        "kind": "flow", "unit": "USD", "label": "Gross profit",
        "tags": ["GrossProfit"],
    },
    "operating_income": {
        "kind": "flow", "unit": "USD", "label": "Operating income",
        "tags": ["OperatingIncomeLoss"],
    },
    "net_income": {
        "kind": "flow", "unit": "USD", "label": "Net income",
        "tags": ["NetIncomeLoss", "ProfitLoss"],
    },
    "eps_diluted": {
        "kind": "flow", "unit": "USD/shares", "label": "Diluted EPS",
        "tags": ["EarningsPerShareDiluted", "EarningsPerShareBasicAndDiluted"],
    },
    "operating_cash_flow": {
        "kind": "flow", "unit": "USD", "label": "Operating cash flow",
        "tags": ["NetCashProvidedByUsedInOperatingActivities",
                 "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    },
    "capex": {
        "kind": "flow", "unit": "USD", "label": "Capital expenditures",
        "tags": ["PaymentsToAcquirePropertyPlantAndEquipment",
                 "PaymentsToAcquireProductiveAssets"],
    },
    "total_assets": {
        "kind": "instant", "unit": "USD", "label": "Total assets",
        "tags": ["Assets"],
    },
    "total_liabilities": {
        "kind": "instant", "unit": "USD", "label": "Total liabilities",
        "tags": ["Liabilities"],
    },
    "equity": {
        "kind": "instant", "unit": "USD", "label": "Shareholders' equity",
        "tags": ["StockholdersEquity",
                 "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    },
    "cash": {
        "kind": "instant", "unit": "USD", "label": "Cash & equivalents",
        "tags": ["CashAndCashEquivalentsAtCarryingValue",
                 "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    },
    "long_term_debt": {
        "kind": "instant", "unit": "USD", "label": "Long-term debt",
        "tags": ["LongTermDebtNoncurrent", "LongTermDebt", "LongTermDebtAndCapitalLeaseObligations"],
    },
}

ANNUAL_FORMS = ("10-K", "10-K/A", "10-KT", "20-F", "40-F")

# Metrics shown in statements, grouped for the report.
STATEMENT_GROUPS: list[tuple[str, list[str]]] = [
    ("Income statement", ["revenue", "cost_of_revenue", "gross_profit", "operating_income",
                          "net_income", "eps_diluted"]),
    ("Cash flow", ["operating_cash_flow", "capex", "free_cash_flow"]),
    ("Balance sheet", ["total_assets", "total_liabilities", "equity", "cash", "long_term_debt"]),
    ("Ratios", ["gross_margin", "operating_margin", "net_margin", "roe", "roa",
                "debt_to_equity", "revenue_growth", "net_income_growth"]),
]

RATIO_METRICS = {"gross_margin", "operating_margin", "net_margin", "roe", "roa",
                 "revenue_growth", "net_income_growth"}
MULTIPLE_METRICS = {"debt_to_equity"}
PER_SHARE_METRICS = {"eps_diluted"}

DERIVED_LABELS = {
    "free_cash_flow": "Free cash flow",
    "gross_margin": "Gross margin", "operating_margin": "Operating margin",
    "net_margin": "Net margin", "roe": "Return on equity", "roa": "Return on assets",
    "debt_to_equity": "Debt / equity", "revenue_growth": "Revenue growth (YoY)",
    "net_income_growth": "Net income growth (YoY)",
}


def label(metric: str) -> str:
    if metric in CONCEPTS:
        return CONCEPTS[metric]["label"]
    return DERIVED_LABELS.get(metric, metric)
