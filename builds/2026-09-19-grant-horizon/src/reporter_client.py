"""NIH RePORTER v2 projects/search client.

Public, no-auth REST API (https://api.reporter.nih.gov/v2/projects/search).
The HTTP transport is injected as `http_post` everywhere so the rest of the
module — and every test — never depends on real network access. Only
`default_http_post` performs a real request, and it is exercised solely at
runtime by the user, never in the test suite.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

REPORTER_SEARCH_URL = "https://api.reporter.nih.gov/v2/projects/search"
PAGE_SIZE = 500


class ReporterAPIError(Exception):
    """Raised when the NIH RePORTER API returns an error, or a record can't be normalized."""


@dataclass
class Project:
    topic: str
    project_num: str
    core_project_num: str
    title: str
    fiscal_year: int
    award_amount: float
    org_name: str
    org_city: str
    org_state: str
    org_country: str
    pi_names: list
    agency_ic: str
    start_date: Optional[str]
    end_date: Optional[str]


HttpPostFn = Callable[[str, dict], dict]


def default_http_post(url: str, body: dict) -> dict:
    """Real transport: POST JSON to `url`, return the parsed JSON response."""
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise ReporterAPIError(f"NIH RePORTER request failed: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReporterAPIError(f"NIH RePORTER returned malformed JSON: {exc}") from exc


def normalize_project(topic: str, raw: dict) -> Project:
    """Normalize one raw RePORTER v2 result record into a Project.

    Defensive against missing/null optional fields so a partial or
    slightly-different-shaped record never crashes a sync.
    """
    org = raw.get("organization") or {}
    agency = raw.get("agency_ic_admin") or {}
    pis_raw = raw.get("principal_investigators") or []

    pi_names = []
    for pi in pis_raw:
        if not isinstance(pi, dict):
            continue
        full = pi.get("full_name")
        if not full:
            first = pi.get("first_name") or ""
            last = pi.get("last_name") or ""
            full = f"{first} {last}".strip()
        if full:
            pi_names.append(full)

    project_num = raw.get("project_num") or raw.get("core_project_num")
    if not project_num:
        raise ReporterAPIError("RePORTER record missing both project_num and core_project_num")

    try:
        fiscal_year = int(raw.get("fiscal_year"))
    except (TypeError, ValueError) as exc:
        raise ReporterAPIError(f"RePORTER record {project_num!r} missing a valid fiscal_year") from exc

    raw_amount = raw.get("award_amount")
    try:
        award_amount = float(raw_amount) if raw_amount is not None else 0.0
    except (TypeError, ValueError):
        award_amount = 0.0

    return Project(
        topic=topic,
        project_num=str(project_num),
        core_project_num=str(raw.get("core_project_num") or project_num),
        title=raw.get("project_title") or "(untitled project)",
        fiscal_year=fiscal_year,
        award_amount=award_amount,
        org_name=org.get("org_name") or "Unknown institution",
        org_city=org.get("org_city") or "",
        org_state=org.get("org_state") or "",
        org_country=org.get("org_country") or "",
        pi_names=pi_names,
        agency_ic=agency.get("name") or agency.get("code") or "Unknown agency",
        start_date=raw.get("project_start_date"),
        end_date=raw.get("project_end_date"),
    )


def fetch_all_projects(
    topic: str,
    fiscal_years: Iterable[int],
    http_post: HttpPostFn,
    page_size: int = PAGE_SIZE,
) -> list:
    """Page through NIH RePORTER's project search for one topic across the given fiscal years."""
    fiscal_years = list(fiscal_years)
    if not fiscal_years:
        raise ValueError("fiscal_years must be non-empty")

    projects = []
    offset = 0
    while True:
        body = {
            "criteria": {
                "advanced_text_search": {
                    "operator": "and",
                    "search_field": "projecttitle,terms,abstracttext",
                    "search_text": topic,
                },
                "fiscal_years": fiscal_years,
            },
            "include_fields": [
                "ProjectTitle", "ProjectNum", "CoreProjectNum", "FiscalYear",
                "AwardAmount", "Organization", "PrincipalInvestigators",
                "AgencyIcAdmin", "ProjectStartDate", "ProjectEndDate",
            ],
            "offset": offset,
            "limit": page_size,
            "sort_field": "fiscal_year",
            "sort_order": "desc",
        }
        response = http_post(REPORTER_SEARCH_URL, body)
        if not isinstance(response, dict):
            raise ReporterAPIError("NIH RePORTER response was not a JSON object")
        results = response.get("results")
        if results is None:
            raise ReporterAPIError("NIH RePORTER response missing 'results'")

        for raw in results:
            projects.append(normalize_project(topic, raw))

        if len(results) < page_size:
            break
        offset += page_size

    return projects
