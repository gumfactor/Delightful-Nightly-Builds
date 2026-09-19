"""Pure aggregation functions over a list of reporter_client.Project.

No I/O, no network, no randomness — every function here is deterministic
and fully covered by hand-computed fixtures in tests/test_aggregate.py.
"""
from __future__ import annotations

from collections import defaultdict


def funding_by_year(projects: list) -> dict:
    """Total award amount and project count per fiscal year, across all given projects."""
    by_year = defaultdict(lambda: {"total_amount": 0.0, "count": 0})
    for project in projects:
        entry = by_year[project.fiscal_year]
        entry["total_amount"] += project.award_amount
        entry["count"] += 1
    return dict(by_year)


def funding_by_year_per_topic(projects: list) -> dict:
    """funding_by_year, grouped by topic first — used for the per-topic trend chart."""
    by_topic = defaultdict(list)
    for project in projects:
        by_topic[project.topic].append(project)
    return {topic: funding_by_year(topic_projects) for topic, topic_projects in by_topic.items()}


def year_over_year_growth(year_totals: dict) -> dict:
    """Percentage change in total_amount from the prior year, for each year present.

    The earliest year in `year_totals` always maps to None (no prior year to
    compare against). A year whose prior-year total was exactly 0 also maps
    to None rather than raising or returning an infinite/undefined percentage.
    """
    years = sorted(year_totals.keys())
    growth = {}
    for index, year in enumerate(years):
        if index == 0:
            growth[year] = None
            continue
        prior_total = year_totals[years[index - 1]]["total_amount"]
        current_total = year_totals[year]["total_amount"]
        if prior_total == 0:
            growth[year] = None
        else:
            growth[year] = ((current_total - prior_total) / prior_total) * 100.0
    return growth


def top_institutions(projects: list, n: int = 10) -> list:
    """Top `n` institutions by total award amount, as (org_name, total_amount, count) tuples.

    Ties break alphabetically by org_name for a deterministic order.
    """
    totals = defaultdict(lambda: {"total_amount": 0.0, "count": 0})
    for project in projects:
        entry = totals[project.org_name]
        entry["total_amount"] += project.award_amount
        entry["count"] += 1
    ranked = sorted(
        ((name, data["total_amount"], data["count"]) for name, data in totals.items()),
        key=lambda row: (-row[1], row[0]),
    )
    return ranked[:n]


def top_pis(projects: list, n: int = 10) -> list:
    """Top `n` principal investigators by total award amount, as (pi_name, total_amount, count).

    A project with multiple co-PIs attributes the project's full award amount
    to each named PI (a documented simplification — RePORTER does not expose
    a per-PI budget split), so summing this table's totals will generally
    exceed the true total funding for multi-PI-heavy topics.
    """
    totals = defaultdict(lambda: {"total_amount": 0.0, "count": 0})
    for project in projects:
        for pi_name in project.pi_names:
            entry = totals[pi_name]
            entry["total_amount"] += project.award_amount
            entry["count"] += 1
    ranked = sorted(
        ((name, data["total_amount"], data["count"]) for name, data in totals.items()),
        key=lambda row: (-row[1], row[0]),
    )
    return ranked[:n]


def agency_breakdown(projects: list) -> dict:
    """Total award amount and project count per funding agency/IC."""
    totals = defaultdict(lambda: {"total_amount": 0.0, "count": 0})
    for project in projects:
        entry = totals[project.agency_ic]
        entry["total_amount"] += project.award_amount
        entry["count"] += 1
    return dict(totals)


def total_funding(projects: list) -> float:
    return sum(project.award_amount for project in projects)
