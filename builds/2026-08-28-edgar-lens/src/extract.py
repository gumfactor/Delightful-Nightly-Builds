"""Tag-resolution and fiscal-year extraction over SEC EDGAR XBRL companyfacts JSON.

Filers do not all use the same US-GAAP tag for the same financial statement
line item (e.g. some report revenue as "Revenues", others as
"RevenueFromContractWithCustomerExcludingAssessedTax"), and some switch tags
partway through their filing history. This module tries every candidate tag
in a documented priority order and merges them *per fiscal year* -- a
higher-priority tag's value wins for a year it covers, but a lower-priority
tag can still fill in a year the higher-priority tag has no data for.

SEC's own fy/fp/form fields describe the filing that reported a value, not
necessarily that value's own reporting period -- a single 10-K's XBRL
includes multi-year comparative figures that are not guaranteed to carry
their own distinct fy. So facts are grouped by their actual (start, end)
period first, and the fiscal-year label used everywhere in this module is
derived from that period's own end date, never trusted verbatim from the
fy field.
"""

from __future__ import annotations

from datetime import date
from typing import Any

# Priority-ordered US-GAAP tag candidates per financial concept. Tried in
# order and merged per fiscal year -- see module docstring.
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

# 10-K/A amendments (e.g. financial restatements) must be considered, or a
# re-sync would keep the original, superseded value forever.
ANNUAL_FORMS = {"10-K", "10-K/A"}


def resolve_tag(usgaap_facts: dict[str, Any], candidates: list[str]) -> str | None:
    """Return the first candidate tag present in usgaap_facts with a USD unit.

    Standalone utility (independently tested) -- not used to select a
    single company-wide tag for extraction, since a tag merely existing
    does not mean it has usable annual data for every year; see
    extract_annual_financials, which merges all candidates per year instead.
    """
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
    return fact.get("form") in ANNUAL_FORMS and fact.get("fp") == "FY" and fact.get("fy") is not None


def _latest_filed_wins(existing: dict[str, Any] | None, candidate: dict[str, Any]) -> dict[str, Any]:
    if existing is None or (candidate.get("filed") or "") >= (existing.get("filed") or ""):
        return candidate
    return existing


def _extract_duration_facts_for_tag(usgaap_facts: dict[str, Any], tag: str) -> dict[int, dict[str, Any]]:
    """Map end-date-derived fiscal year -> best annual fact, for one tag."""
    by_period: dict[tuple[date, date], dict[str, Any]] = {}
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
        period = (start, end)
        by_period[period] = _latest_filed_wins(by_period.get(period), fact)

    by_fiscal_year: dict[int, dict[str, Any]] = {}
    for (_start, end), fact in by_period.items():
        fiscal_year = end.year
        by_fiscal_year[fiscal_year] = _latest_filed_wins(by_fiscal_year.get(fiscal_year), fact)
    return by_fiscal_year


def _extract_instant_facts_for_tag(usgaap_facts: dict[str, Any], tag: str) -> dict[int, dict[str, Any]]:
    """Map end-date-derived fiscal year -> best annual fact, for one tag."""
    by_period: dict[date, dict[str, Any]] = {}
    facts = usgaap_facts.get(tag, {}).get("units", {}).get("USD", [])
    for fact in facts:
        if not _is_annual_fact(fact):
            continue
        end = _parse_date(fact.get("end"))
        if not end:
            continue
        by_period[end] = _latest_filed_wins(by_period.get(end), fact)

    by_fiscal_year: dict[int, dict[str, Any]] = {}
    for end, fact in by_period.items():
        fiscal_year = end.year
        by_fiscal_year[fiscal_year] = _latest_filed_wins(by_fiscal_year.get(fiscal_year), fact)
    return by_fiscal_year


def _merge_candidate_tags(
    usgaap_facts: dict[str, Any],
    candidates: list[str],
    extractor,
) -> dict[int, dict[str, Any]]:
    """Merge every candidate tag's per-fiscal-year facts.

    A higher-priority (earlier) candidate's value for a given fiscal year
    always wins; a lower-priority candidate only fills in years the
    higher-priority tag has no usable annual data for.
    """
    merged: dict[int, dict[str, Any]] = {}
    for tag in candidates:
        for fiscal_year, fact in extractor(usgaap_facts, tag).items():
            if fiscal_year not in merged:
                merged[fiscal_year] = fact
    return merged


def extract_annual_financials(companyfacts: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract one annual row per fiscal year from a companyfacts document.

    Returns rows sorted by fiscal_year ascending, each with the resolved
    concept values (None where no candidate tag had usable annual data for
    that year), plus the most recent filed date/accn seen for that year.
    """
    usgaap = companyfacts.get("facts", {}).get("us-gaap", {})
    if not usgaap:
        return []

    per_concept_by_fy: dict[str, dict[int, dict[str, Any]]] = {}

    for concept, candidates in DURATION_CONCEPT_TAGS.items():
        per_concept_by_fy[concept] = _merge_candidate_tags(usgaap, candidates, _extract_duration_facts_for_tag)

    for concept, candidates in INSTANT_CONCEPT_TAGS.items():
        per_concept_by_fy[concept] = _merge_candidate_tags(usgaap, candidates, _extract_instant_facts_for_tag)

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
