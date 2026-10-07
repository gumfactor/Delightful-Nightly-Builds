"""Indicator catalogue. Edit here to add or swap series."""
from __future__ import annotations

from typing import Any

VALET_BASE = "https://www.bankofcanada.ca/valet/observations"
WDS_URL = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVectorsAndLatestNPeriods"
WDS_INFO_URL = "https://www150.statcan.gc.ca/t1/wds/rest/getSeriesInfoFromVector"

# higher_is: "good" | "bad" | "neutral" — used to colour signals.
# freq: "D" daily, "M" monthly (determines staleness limit in days).
INDICATORS: list[dict[str, Any]] = [
    {"id": "cpi", "label": "CPI (all items)", "unit": "index", "source": "statcan",
     "vector": 41690973, "freq": "M", "higher_is": "neutral", "expect": "consumer price",
     "table": "18-10-0004-01", "group": "Prices"},
    {"id": "policy_rate", "label": "BoC policy rate", "unit": "%", "source": "valet",
     "series": "V39079", "freq": "D", "higher_is": "neutral", "group": "Rates"},
    {"id": "gov10y", "label": "GoC 10-yr yield", "unit": "%", "source": "valet",
     "series": "BD.CDN.10YR.DQ.YLD", "freq": "D", "higher_is": "neutral", "group": "Rates"},
    {"id": "gov2y", "label": "GoC 2-yr yield", "unit": "%", "source": "valet",
     "series": "BD.CDN.2YR.DQ.YLD", "freq": "D", "higher_is": "neutral", "group": "Rates"},
    {"id": "usdcad", "label": "USD/CAD", "unit": "CAD per USD", "source": "valet",
     "series": "FXUSDCAD", "freq": "D", "higher_is": "neutral", "group": "Currency"},
    {"id": "unemployment", "label": "Unemployment rate", "unit": "%", "source": "statcan",
     "vector": 2062815, "freq": "M", "higher_is": "bad", "expect": "unemployment",
     "table": "14-10-0287-01", "group": "Labour"},
    {"id": "participation", "label": "Participation rate", "unit": "%", "source": "statcan",
     "vector": 2062816, "freq": "M", "higher_is": "good", "expect": "participation",
     "table": "14-10-0287-01", "group": "Labour"},
    {"id": "gdp", "label": "Real GDP (monthly)", "unit": "$ millions (chained)", "source": "statcan",
     "vector": 65201210, "freq": "M", "higher_is": "good", "expect": "all industries",
     "table": "36-10-0434-01", "group": "Output"},
    {"id": "retail", "label": "Retail sales", "unit": "$ thousands", "source": "statcan",
     "vector": 52367097, "freq": "M", "higher_is": "good", "expect": "retail",
     "table": "20-10-0008-01", "group": "Output"},
    {"id": "housing", "label": "New housing price index", "unit": "index", "source": "statcan",
     "vector": 111955442, "freq": "M", "higher_is": "neutral", "expect": "new housing",
     "table": "18-10-0205-01", "group": "Housing"},
]

# Derived series computed after fetch.
DERIVED: list[dict[str, Any]] = [
    {"id": "real_rate", "label": "Real policy rate", "unit": "pp", "freq": "M",
     "higher_is": "neutral", "group": "Rates",
     "note": "BoC policy rate minus CPI year-over-year inflation (monthly)."},
    {"id": "curve", "label": "Yield curve (10y–2y)", "unit": "pp", "freq": "D",
     "higher_is": "neutral", "group": "Rates",
     "note": "Negative = inverted curve, historically a recession warning."},
]

# Age (days) after which a latest observation is flagged stale.
STALE_DAYS = {"D": 7, "M": 75}

EVENTS = [
    {"date": "2020-03-11", "label": "COVID-19 pandemic declared"},
    {"date": "2022-03-02", "label": "BoC begins hiking cycle"},
    {"date": "2024-06-05", "label": "BoC first cut"},
]
