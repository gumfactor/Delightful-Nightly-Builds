"""GitHub API client for fetching repos and Actions workflow runs."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.environ.get("GITHUB_TOKEN", "")
        if not self._token:
            print("ERROR: GITHUB_TOKEN is not set.", file=sys.stderr)
            raise EnvironmentError("GITHUB_TOKEN required")

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        url = f"{self.BASE_URL}{path}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ci-pulse/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                print(f"Rate limited or forbidden: {exc}", file=sys.stderr)
                return None
            if exc.code == 404:
                return None
            raise
        except (urllib.error.URLError, OSError) as exc:
            print(f"Network error: {exc}", file=sys.stderr)
            return None

    def _get_paginated(self, path: str, params: dict[str, str] | None = None, max_pages: int = 5) -> list[Any]:
        results: list[Any] = []
        page = 1
        while page <= max_pages:
            p = dict(params or {})
            p["page"] = str(page)
            p.setdefault("per_page", "100")
            data = self._get(path, p)
            if not data:
                break
            if isinstance(data, dict):
                items = data.get("workflow_runs") or data.get("jobs") or []
            else:
                items = data
            if not items:
                break
            results.extend(items)
            if len(items) < int(p["per_page"]):
                break
            page += 1
        return results

    def get_authenticated_user(self) -> dict[str, Any] | None:
        return self._get("/user")

    def list_repos(self) -> list[dict[str, Any]]:
        """Fetch all repos for the authenticated user."""
        return self._get_paginated("/user/repos", {"type": "owner", "sort": "pushed"})

    def list_workflow_runs(
        self,
        owner: str,
        repo: str,
        since_days: int = 30,
    ) -> list[dict[str, Any]]:
        """Fetch completed workflow runs within the last `since_days` days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        created_param = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
        path = f"/repos/{owner}/{repo}/actions/runs"
        all_runs = self._get_paginated(
            path,
            {"status": "completed", "created": f">={created_param}", "per_page": "50"},
            max_pages=3,
        )
        return all_runs


def filter_repos_with_recent_push(
    repos: list[dict[str, Any]],
    since_days: int = 30,
) -> list[dict[str, Any]]:
    """Filter repos to those pushed to within the last `since_days` days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    result = []
    for repo in repos:
        pushed_at = repo.get("pushed_at")
        if not pushed_at:
            continue
        try:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            if pushed >= cutoff and not repo.get("archived", False):
                result.append(repo)
        except (ValueError, TypeError):
            continue
    return result


def group_runs_by_workflow(
    runs: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group run objects by their workflow name."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        name = run.get("name") or run.get("workflow_id", "unknown")
        key = str(name)
        groups.setdefault(key, []).append(run)
    return groups
