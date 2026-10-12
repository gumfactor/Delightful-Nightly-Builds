"""CSV exports: long format, wide per-company, and one-row-per-company summary."""
from __future__ import annotations

import csv
import re
from pathlib import Path

from .concepts import STATEMENT_GROUPS, label
from .metrics import summarize

LONG_HEADER = ["ticker", "fiscal_year", "period_end", "metric", "label", "value"]
SUMMARY_FIELDS = ["ticker", "name", "latest_year", "revenue", "net_income", "free_cash_flow",
                  "gross_margin", "operating_margin", "net_margin", "roe", "debt_to_equity",
                  "revenue_cagr", "net_income_cagr", "eps_cagr"]


def all_metric_names() -> list[str]:
    return [m for _, names in STATEMENT_GROUPS for m in names]


def value_of(company: dict, metric: str, year: int) -> float | None:
    if year in company["metrics"].get(metric, {}):
        return company["metrics"][metric][year]
    return company["derived"].get(metric, {}).get(year)


def _cell(value: float | None) -> str:
    return "" if value is None else repr(float(value))


def safe_filename(ticker: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", ticker)


def write_long_csv(companies: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(LONG_HEADER)
        for company in companies:
            for year in company["years"]:
                for metric in all_metric_names():
                    value = value_of(company, metric, year)
                    if value is not None:
                        writer.writerow([company["ticker"], year, company["end_dates"].get(year, ""),
                                         metric, label(metric), _cell(value)])


def write_wide_csv(company: dict, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", *company["years"]])
        for metric in all_metric_names():
            row = [value_of(company, metric, y) for y in company["years"]]
            if any(v is not None for v in row):
                writer.writerow([label(metric), *(_cell(v) for v in row)])


def write_summary_csv(companies: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for company in companies:
            row = summarize(company)
            writer.writerow({k: ("" if row[k] is None else row[k]) for k in SUMMARY_FIELDS})


def write_all(companies: list[dict], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = [out_dir / "financials_long.csv", out_dir / "summary.csv"]
    write_long_csv(companies, written[0])
    write_summary_csv(companies, written[1])
    for company in companies:
        path = out_dir / f"{safe_filename(company['ticker'])}_financials.csv"
        write_wide_csv(company, path)
        written.append(path)
    return written
