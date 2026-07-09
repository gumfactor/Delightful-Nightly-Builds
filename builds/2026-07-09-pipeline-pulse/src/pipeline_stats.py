"""Combines catalog records with git reconciliation data into dashboard-ready stats."""
from __future__ import annotations

from datetime import date as date_cls
from datetime import datetime
from typing import Optional, TypedDict

from catalog_parser import CatalogRecord


class BuildStatus(TypedDict):
    date: str
    category: str
    complexity: str
    title: str
    description: str
    tech: str
    status: str
    rating: Optional[int]
    notes: str
    folder: Optional[str]
    merged: bool
    branch: Optional[str]
    backlog_days: Optional[int]


def _parse_date(value: str) -> Optional[date_cls]:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def reconcile(
    records: list[CatalogRecord],
    folders_on_default_branch: set[str],
    folder_branch_map: dict[str, str],
    today: date_cls,
) -> list[BuildStatus]:
    """For each catalog record, determine whether its build folder has landed
    on the default branch, or which open branch is still carrying it."""
    statuses: list[BuildStatus] = []
    for record in records:
        prefix = record["date"]
        merged_match = next(
            (f for f in sorted(folders_on_default_branch) if f.startswith(prefix)), None
        )
        if merged_match is not None:
            folder, merged, branch = merged_match, True, None
        else:
            backlog_match = next(
                (f for f in sorted(folder_branch_map) if f.startswith(prefix)), None
            )
            if backlog_match is not None:
                folder, merged, branch = backlog_match, False, folder_branch_map[backlog_match]
            else:
                folder, merged, branch = None, False, None

        backlog_days = None
        if not merged:
            parsed = _parse_date(record["date"])
            if parsed is not None:
                backlog_days = (today - parsed).days

        statuses.append(
            BuildStatus(
                date=record["date"],
                category=record["category"],
                complexity=record["complexity"],
                title=record["title"],
                description=record["description"],
                tech=record["tech"],
                status=record["status"],
                rating=record["rating"],
                notes=record["notes"],
                folder=folder,
                merged=merged,
                branch=branch,
                backlog_days=backlog_days,
            )
        )
    return statuses


class Summary(TypedDict):
    total: int
    merged_count: int
    backlog_count: int
    merged_pct: float
    backlog_pct: float
    oldest_unmerged: Optional[BuildStatus]
    rated_count: int
    rating_coverage_pct: float
    average_rating: Optional[float]
    category_distribution: dict[str, int]
    complexity_distribution: dict[str, int]
    status_distribution: dict[str, int]
    rating_trend: list[tuple[str, int]]
    needs_attention: list[BuildStatus]


#: Statuses that were never expected to merge (intentionally abandoned) — excluded
#: from backlog metrics so they don't read as builds "waiting for review".
NON_ACTIONABLE_STATUSES = {"discarded", "aborted"}


def summarize(statuses: list[BuildStatus], attention_limit: int = 10) -> Summary:
    total = len(statuses)
    merged = [s for s in statuses if s["merged"]]
    unmerged = [
        s
        for s in statuses
        if not s["merged"] and s["status"].lower() not in NON_ACTIONABLE_STATUSES
    ]
    rated = [s for s in statuses if s["rating"] is not None]

    oldest_unmerged = None
    if unmerged:
        with_age = [s for s in unmerged if s["backlog_days"] is not None]
        if with_age:
            oldest_unmerged = max(with_age, key=lambda s: s["backlog_days"])

    category_distribution: dict[str, int] = {}
    complexity_distribution: dict[str, int] = {}
    status_distribution: dict[str, int] = {}
    for s in statuses:
        category_distribution[s["category"]] = category_distribution.get(s["category"], 0) + 1
        complexity_distribution[s["complexity"]] = complexity_distribution.get(s["complexity"], 0) + 1
        status_distribution[s["status"]] = status_distribution.get(s["status"], 0) + 1

    rating_trend = sorted(
        ((s["date"], s["rating"]) for s in rated if s["date"]), key=lambda pair: pair[0]
    )

    needs_attention = sorted(
        (s for s in unmerged if s["backlog_days"] is not None),
        key=lambda s: s["backlog_days"],
        reverse=True,
    )[:attention_limit]

    return Summary(
        total=total,
        merged_count=len(merged),
        backlog_count=len(unmerged),
        merged_pct=(len(merged) / total * 100) if total else 0.0,
        backlog_pct=(len(unmerged) / total * 100) if total else 0.0,
        oldest_unmerged=oldest_unmerged,
        rated_count=len(rated),
        rating_coverage_pct=(len(rated) / total * 100) if total else 0.0,
        average_rating=(sum(s["rating"] for s in rated) / len(rated)) if rated else None,
        category_distribution=category_distribution,
        complexity_distribution=complexity_distribution,
        status_distribution=status_distribution,
        rating_trend=rating_trend,
        needs_attention=needs_attention,
    )
