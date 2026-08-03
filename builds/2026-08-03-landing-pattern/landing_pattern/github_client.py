"""Thin GitHub REST API client. All HTTP calls go through `_api_get`, which
tests monkeypatch — nothing in this module makes a real network call during
the test suite. Read-only: no merge, close, or comment endpoints are used.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

API_ROOT = "https://api.github.com"


class GitHubAPIError(RuntimeError):
    """Raised when the GitHub API returns a non-2xx response."""


def _api_get(path: str, token: str, params: dict[str, str] | None = None) -> Any:
    """GET a GitHub API path and return the parsed JSON body."""
    url = f"{API_ROOT}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "landing-pattern",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise GitHubAPIError(f"GitHub API error {exc.code} for {path}: {detail}") from exc


def _paginate(path: str, token: str, per_page: int = 100) -> list[Any]:
    items: list[Any] = []
    page = 1
    while True:
        body = _api_get(path, token, params={"per_page": str(per_page), "page": str(page)})
        if not body:
            break
        items.extend(body)
        if len(body) < per_page:
            break
        page += 1
    return items


def fetch_open_prs(repo: str, token: str) -> list[dict[str, Any]]:
    """List summaries for every open PR on `repo` (owner/name)."""
    return _paginate(f"/repos/{repo}/pulls?state=open", token)


def fetch_pr_detail(repo: str, number: int, token: str) -> dict[str, Any]:
    """Full detail for one PR, including `mergeable` / `mergeable_state`."""
    return _api_get(f"/repos/{repo}/pulls/{number}", token)


def fetch_pr_files(repo: str, number: int, token: str) -> list[str]:
    """Changed file paths for one PR."""
    files = _paginate(f"/repos/{repo}/pulls/{number}/files", token)
    return [f["filename"] for f in files]


def fetch_ci_state(repo: str, sha: str, token: str) -> str:
    """One of: success, failure, pending, error, none."""
    status_body = _api_get(f"/repos/{repo}/commits/{sha}/status", token)
    if status_body.get("total_count", 0) > 0:
        return status_body.get("state", "none")

    check_runs = _api_get(f"/repos/{repo}/commits/{sha}/check-runs", token)
    runs = check_runs.get("check_runs", [])
    if not runs:
        return "none"
    conclusions = [r.get("conclusion") for r in runs]
    if any(c in ("failure", "timed_out", "cancelled", "action_required") for c in conclusions):
        return "failure"
    if any(c is None for c in conclusions):
        return "pending"
    return "success"


def fetch_review_state(repo: str, number: int, token: str, requested_reviewers: int = 0) -> str:
    """One of: approved, changes_requested, review_required, none."""
    reviews = _paginate(f"/repos/{repo}/pulls/{number}/reviews", token)
    latest_by_user: dict[str, str] = {}
    for review in reviews:
        user = review.get("user", {}).get("login", "")
        state = review.get("state", "")
        if state in ("APPROVED", "CHANGES_REQUESTED"):
            latest_by_user[user] = state

    states = set(latest_by_user.values())
    if "CHANGES_REQUESTED" in states:
        return "changes_requested"
    if "APPROVED" in states:
        return "approved"
    if requested_reviewers > 0:
        return "review_required"
    return "none"


def fetch_repo_prs_full(repo: str, token: str) -> list[dict[str, Any]]:
    """Fetch every open PR on `repo`, fully resolved for `landing_pattern.analysis`."""
    summaries = fetch_open_prs(repo, token)
    resolved: list[dict[str, Any]] = []
    for summary in summaries:
        number = summary["number"]
        detail = fetch_pr_detail(repo, number, token)
        files = fetch_pr_files(repo, number, token)
        sha = detail.get("head", {}).get("sha", "")
        ci_state = fetch_ci_state(repo, sha, token) if sha else "none"
        requested_reviewers = len(detail.get("requested_reviewers", []))
        review_state = fetch_review_state(repo, number, token, requested_reviewers)
        resolved.append(
            {
                "number": number,
                "title": detail.get("title", summary.get("title", "")),
                "url": detail.get("html_url", summary.get("html_url", "")),
                "created_at": detail.get("created_at", summary.get("created_at", "")),
                "draft": detail.get("draft", False),
                "mergeable_state": detail.get("mergeable_state") or "unknown",
                "ci_state": ci_state,
                "review_state": review_state,
                "files": files,
            }
        )
    return resolved
