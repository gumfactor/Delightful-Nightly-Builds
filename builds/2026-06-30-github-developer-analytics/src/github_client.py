"""GitHub API client for fetching repo and commit data."""

import os
import time
from datetime import datetime, timezone
from typing import Any
import requests


BASE_URL = "https://api.github.com"
DEFAULT_PER_PAGE = 100


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{BASE_URL}{path}"
        for attempt in range(3):
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code == 403:
                # Rate limit: retry after waiting. Permission denied: return None immediately.
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 1))
                if remaining == 0 and attempt < 2:
                    reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                    wait = max(1, reset - int(time.time()))
                    time.sleep(min(wait, 30))
                    continue
                return None  # Permission denied — caller receives None/empty
            if resp.status_code in (404, 409):
                # 404 = not found; 409 = empty repository (no commits)
                return None
            resp.raise_for_status()
            return resp.json()
        return None

    def get_authenticated_user(self) -> dict[str, Any]:
        result = self._get("/user")
        return result or {}

    def get_repos(self, max_repos: int = 50) -> list[dict[str, Any]]:
        """Fetch user-owned repos sorted by most recently pushed."""
        repos: list[dict[str, Any]] = []
        page = 1
        while len(repos) < max_repos:
            batch = self._get("/user/repos", params={
                "type": "owner",
                "sort": "pushed",
                "direction": "desc",
                "per_page": min(DEFAULT_PER_PAGE, max_repos - len(repos)),
                "page": page,
            })
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < DEFAULT_PER_PAGE:
                break
            page += 1
        return repos[:max_repos]

    def get_commits(
        self,
        owner: str,
        repo: str,
        author_login: str,
        since_iso: str,
    ) -> list[dict[str, Any]]:
        """Fetch commits by the given author since the given ISO date."""
        commits: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = self._get(f"/repos/{owner}/{repo}/commits", params={
                "author": author_login,
                "since": since_iso,
                "per_page": DEFAULT_PER_PAGE,
                "page": page,
            })
            if not batch:
                break  # None (permission error / not found) or empty list
            if not isinstance(batch, list):
                break
            commits.extend(batch)
            if len(batch) < DEFAULT_PER_PAGE:
                break
            page += 1
        return commits

    def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        """Fetch language byte counts for a repo."""
        result = self._get(f"/repos/{owner}/{repo}/languages")
        return result if isinstance(result, dict) else {}

    @staticmethod
    def parse_commit_timestamp(commit: dict[str, Any]) -> datetime | None:
        """Extract UTC datetime from a GitHub commit object."""
        try:
            date_str = commit["commit"]["author"]["date"]
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc)
        except (KeyError, ValueError, TypeError):
            return None

    @staticmethod
    def build_since_iso(months_back: int) -> str:
        """Return ISO 8601 timestamp for N months ago (approximate)."""
        now = datetime.now(timezone.utc)
        year = now.year
        month = now.month - months_back
        while month <= 0:
            month += 12
            year -= 1
        try:
            since = now.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            since = now.replace(year=year, month=month, day=28, hour=0, minute=0, second=0, microsecond=0)
        return since.strftime("%Y-%m-%dT%H:%M:%SZ")
