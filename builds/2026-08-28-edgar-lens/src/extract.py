"""Tag-resolution and fiscal-year extraction over SEC EDGAR XBRL companyfacts JSON.

Filers do not all use the same US-GAAP tag for the same financial statement
line item (e.g. some report revenue as "Revenues", others as
"RevenueFromContractWithCustomerExcludingAssessedTax"). This module tries a
documented priority list of alternate tags per concept and extracts one
annual value per concept per fiscal year, restricted to 10-K/FY facts.
"""

from __future__ import annotations

from datetime import date
from typing import Any

# Priority-ordered US-GAAP tag candidates per financial concept. The first
# tag present in a company's facts (with a USD unit) wins.
DURATION_CONCEPT_TAGS: dict[str, list[str]] = {
    "revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
    ],
    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
    ],
}

INSTANT_CONCEPT_TAGS: dict[str, list[str]] = {
    "assets": ["Assets"],
    "liabilities": ["Liabilities"],
    "equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
}

MIN_ANNUAL_DURATION_DAYS = 350
MAX_ANNUAL_DURATION_DAYS = 380


def resolve_tag(usgaap_facts: dict[str, Any], candidates: list[str]) -> str | None:
    """Return the first candidate tag present in usgaap_facts with a USD unit."""
    for tag in candidates:
        entry = usgaap_facts.get(tag)
        if entry and isinstance(entry.get("units"), dict) and "USD" in entry["units"]:
            return tag
    return None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _is_annual_fact(fact: dict[str, Any]) -> bool:
    return fact.get("form") == "10-K" and fact.get("fp") == "FY" and fact.get("fy") is not None


def _extract_duration_values(usgaap_facts: dict[str, Any], tag: str) -> dict[int, dict[str, Any]]:
    """Map fiscal_year -> best fact for a duration (income-statement) concept."""
    results: dict[int, dict[str, Any]] = {}
    facts = usgaap_facts.get(tag, {}).get("units", {}).get("USD", [])
    for fact in facts:
        if not _is_annual_fact(fact):
            continue
        start = _parse_date(fact.get("start"))
        end = _parse_date(fact.get("end"))
        if not start or not end:
            continue
        duration_days = (end - start).days
        if not (MIN_ANNUAL_DURATION_DAYS <= duration_days <= MAX_ANNUAL_DURATION_DAYS):
            continue
        fy = int(fact["fy"])
        existing = results.get(fy)
        if existing is None or (fact.get("filed") or "") >= (existing.get("filed") or ""):
            results[fy] = fact
    return results


def _extract_instant_values(usgaap_facts: dict[str, Any], tag: str) -> dict[int, dict[str, Any]]:
    """Map fiscal_year -> best fact for an instant (balance-sheet) concept."""
    results: dict[int, dict[str, Any]] = {}
    facts = usgaap_facts.get(tag, {}).get("units", {}).get("USD", [])
    for fact in facts:
        if not _is_annual_fact(fact):
            continue
        if not fact.get("end"):
            continue
        fy = int(fact["fy"])
        existing = results.get(fy)
        if existing is None or (fact.get("filed") or "") >= (existing.get("filed") or ""):
            results[fy] = fact
    return results


def extract_annual_financials(companyfacts: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract one annual row per fiscal year from a companyfacts document.

    Returns rows sorted by fiscal_year ascending, each with the resolved
    concept values (None where no candidate tag had data for that year),
    plus the tag used per concept and the most recent filed/accn seen.
    """
    usgaap = companyfacts.get("facts", {}).get("us-gaap", {})
    if not usgaap:
        return []

    per_concept_by_fy: dict[str, dict[int, dict[str, Any]]] = {}
    tag_used: dict[str, str | None] = {}

    for concept, candidates in DURATION_CONCEPT_TAGS.items():
        tag = resolve_tag(usgaap, candidates)
        tag_used[concept] = tag
        per_concept_by_fy[concept] = _extract_duration_values(usgaap, tag) if tag else {}

    for concept, candidates in INSTANT_CONCEPT_TAGS.items():
        tag = resolve_tag(usgaap, candidates)
        tag_used[concept] = tag
        per_concept_by_fy[concept] = _extract_instant_values(usgaap, tag) if tag else {}

    all_fiscal_years: set[int] = set()
    for by_fy in per_concept_by_fy.values():
        all_fiscal_years.update(by_fy.keys())

    rows: list[dict[str, Any]] = []
    for fy in sorted(all_fiscal_years):
        row: dict[str, Any] = {"fiscal_year": fy}
        filed_dates: list[str] = []
        accn = None
        for concept in list(DURATION_CONCEPT_TAGS) + list(INSTANT_CONCEPT_TAGS):
            fact = per_concept_by_fy[concept].get(fy)
            if fact is not None:
                row[concept] = fact.get("val")
                if fact.get("filed"):
                    filed_dates.append(fact["filed"])
                if accn is None and fact.get("accn"):
                    accn = fact["accn"]
            else:
                row[concept] = None
        row["filed_date"] = max(filed_dates) if filed_dates else None
        row["accn"] = accn
        rows.append(row)

    return rows
