"""NIH RePORTER API v2 client — free, public, no authentication required.

Docs: https://api.reporter.nih.gov/
This module builds search requests, executes them via urllib.request, and
parses the JSON response into flat project records matching db.py's schema.
No third-party HTTP library is used.
"""

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

API_URL = "https://api.reporter.nih.gov/v2/projects/search"
REQUEST_TIMEOUT_SECONDS = 20
PAGE_SIZE = 50

INCLUDE_FIELDS = [
    "ProjectNum",
    "ProjectTitle",
    "AbstractText",
    "ContactPiName",
    "OrgName",
    "OrgCity",
    "OrgState",
    "AgencyIcAdmin",
    "ActivityCode",
    "AwardAmount",
    "FiscalYear",
    "ProjectStartDate",
    "ProjectEndDate",
]


class ApiClientError(Exception):
    """Raised when the NIH RePORTER API cannot be reached or returns an unusable response."""


def build_request_payload(
    search_text: str,
    fiscal_years: List[int],
    offset: int = 0,
    limit: int = PAGE_SIZE,
) -> Dict[str, Any]:
    """Build the JSON request body for a single search page."""
    return {
        "criteria": {
            "advanced_text_search": {
                "operator": "and",
                "search_field": "projecttitle,terms,abstracttext",
                "search_text": search_text,
            },
            "fiscal_years": list(fiscal_years),
        },
        "include_fields": INCLUDE_FIELDS,
        "offset": offset,
        "limit": limit,
        "sort_field": "fiscal_year",
        "sort_order": "desc",
    }


def _extract_ic_admin(raw_ic: Any) -> Optional[str]:
    if isinstance(raw_ic, dict):
        code = raw_ic.get("Code") or raw_ic.get("code")
        name = raw_ic.get("Name") or raw_ic.get("name")
        return code or name
    if isinstance(raw_ic, str) and raw_ic:
        return raw_ic
    return None


def _extract_pi_name(raw_result: Dict[str, Any]) -> Optional[str]:
    contact_pi = raw_result.get("ContactPiName")
    if contact_pi:
        return contact_pi
    pis = raw_result.get("PrincipalInvestigators")
    if isinstance(pis, list) and pis:
        first = pis[0]
        if isinstance(first, dict):
            first_name = first.get("FirstName", "")
            last_name = first.get("LastName", "")
            full = f"{first_name} {last_name}".strip()
            return full or None
    return None


def parse_project(raw_result: Dict[str, Any], topic_key: str) -> Optional[Dict[str, Any]]:
    """Convert one raw NIH RePORTER result record into our flat project schema.

    Returns None if the record has no usable project number (required primary key).
    """
    project_num = raw_result.get("ProjectNum")
    if not project_num:
        return None

    org = raw_result.get("Organization") or {}
    org_name = org.get("OrgName") if isinstance(org, dict) else raw_result.get("OrgName")
    org_city = org.get("OrgCity") if isinstance(org, dict) else raw_result.get("OrgCity")
    org_state = org.get("OrgState") if isinstance(org, dict) else raw_result.get("OrgState")

    return {
        "project_num": project_num,
        "topic": topic_key,
        "title": raw_result.get("ProjectTitle") or "(untitled project)",
        "abstract": raw_result.get("AbstractText") or "",
        "pi_name": _extract_pi_name(raw_result),
        "org_name": org_name or raw_result.get("OrgName"),
        "org_city": org_city,
        "org_state": org_state,
        "ic_admin": _extract_ic_admin(raw_result.get("AgencyIcAdmin")),
        "activity_code": raw_result.get("ActivityCode"),
        "award_amount": raw_result.get("AwardAmount"),
        "fiscal_year": raw_result.get("FiscalYear"),
        "project_start": raw_result.get("ProjectStartDate"),
        "project_end": raw_result.get("ProjectEndDate"),
    }


def _post_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise ApiClientError(f"NIH RePORTER API returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise ApiClientError(f"Could not reach NIH RePORTER API: {exc.reason}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ApiClientError("NIH RePORTER API returned malformed JSON") from exc


def fetch_projects(
    topic_key: str,
    search_text: str,
    fiscal_years: List[int],
    max_results: int = 100,
) -> List[Dict[str, Any]]:
    """Fetch up to max_results projects for a topic, paginating as needed.

    Raises ApiClientError on network/HTTP/parsing failure. Returns an empty
    list (not an error) when the query legitimately has zero results.
    """
    projects: List[Dict[str, Any]] = []
    offset = 0

    while len(projects) < max_results:
        page_limit = min(PAGE_SIZE, max_results - len(projects))
        payload = build_request_payload(search_text, fiscal_years, offset=offset, limit=page_limit)
        response = _post_json(payload)

        results = response.get("results")
        if not isinstance(results, list):
            raise ApiClientError("NIH RePORTER API response missing 'results' list")

        if not results:
            break

        for raw_result in results:
            parsed = parse_project(raw_result, topic_key)
            if parsed is not None:
                projects.append(parsed)

        if len(results) < page_limit:
            break

        offset += page_limit

    return projects
