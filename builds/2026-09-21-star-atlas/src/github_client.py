"""GitHub starred-repos API client.

Uses only the stdlib (urllib) so the tool has zero runtime dependencies
beyond Python itself. All network calls go through a single injectable
`opener` function so tests can fully mock GitHub without ever hitting
the network.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional

API_ROOT = "https://api.github.com"
STAR_ACCEPT_HEADER = "application/vnd.github.star+json"
PER_PAGE = 100


class MissingTokenError(RuntimeError):
    """Raised when no GitHub token is available."""


class GitHubAPIError(RuntimeError):
    """Raised when the GitHub API returns a non-2xx response."""

    def __init__(self, status: int, message: str):
        super().__init__(f"GitHub API error {status}: {message}")
        self.status = status


@dataclass(frozen=True)
class StarredRepo:
    id: int
    full_name: str
    description: Optional[str]
    html_url: str
    language: Optional[str]
    topics: list
    stargazers_count: int
    starred_at: str


OpenerFn = Callable[[urllib.request.Request], "_Response"]


class _Response:
    """Minimal stand-in for what urlopen's context-manager returns."""

    def __init__(self, status: int, body: bytes):
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _default_opener(request: urllib.request.Request) -> _Response:
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            return _Response(resp.status, resp.read())
    except urllib.error.HTTPError as exc:
        raise GitHubAPIError(exc.code, exc.reason) from exc
    except urllib.error.URLError as exc:
        raise GitHubAPIError(0, str(exc.reason)) from exc


def _parse_repo(entry: dict) -> StarredRepo:
    repo = entry["repo"]
    return StarredRepo(
        id=repo["id"],
        full_name=repo["full_name"],
        description=repo.get("description"),
        html_url=repo["html_url"],
        language=repo.get("language"),
        topics=list(repo.get("topics") or []),
        stargazers_count=repo.get("stargazers_count", 0),
        starred_at=entry["starred_at"],
    )


def fetch_starred(
    token: Optional[str],
    since: Optional[str] = None,
    opener: OpenerFn = _default_opener,
    per_page: int = PER_PAGE,
    max_pages: int = 100,
) -> list:
    """Fetch the authenticated user's starred repos, newest-first.

    If `since` (an ISO 8601 `starred_at` timestamp) is given, stops
    paginating once a page contains no repo starred after `since` and
    only returns repos strictly newer than `since`. Otherwise fetches
    every starred repo.
    """
    if not token:
        raise MissingTokenError(
            "No GitHub token provided. Pass --token or set the GITHUB_TOKEN "
            "environment variable."
        )

    results: list = []
    page = 1
    while page <= max_pages:
        request = urllib.request.Request(
            f"{API_ROOT}/user/starred?per_page={per_page}&page={page}"
            "&sort=created&direction=desc",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": STAR_ACCEPT_HEADER,
                "User-Agent": "star-atlas",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response = opener(request)
        if response.status == 404:
            raise GitHubAPIError(404, "user not found or token lacks access")
        if response.status >= 300:
            raise GitHubAPIError(response.status, "unexpected response")

        body = json.loads(response.read().decode("utf-8"))
        if not body:
            break

        page_had_new = False
        for entry in body:
            starred_at = entry["starred_at"]
            if since is not None and starred_at <= since:
                continue
            page_had_new = True
            results.append(_parse_repo(entry))

        if since is not None and not page_had_new:
            break
        if len(body) < per_page:
            break
        page += 1

    return results
