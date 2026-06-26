"""
GitHub API client for fetching commit history.
Uses GITHUB_TOKEN via urllib (no external HTTP library required).
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _gh_request(path: str, token: str, params: dict | None = None) -> list | dict:
    """Make an authenticated GET request to the GitHub REST API."""
    base = "https://api.github.com"
    url = f"{base}{path}"
    if params:
        url += "?" + urlencode(params)

    req = Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "github-activity-explorer/1.0")

    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_authenticated_user(token: str) -> dict:
    """Return the authenticated user's profile dict."""
    return _gh_request("/user", token)


def get_user_repos(token: str) -> list[dict]:
    """Return all repos visible to the token, sorted by most recently pushed."""
    repos: list[dict] = []
    page = 1
    while True:
        batch = _gh_request("/user/repos", token, {
            "per_page": 100,
            "page": page,
            "sort": "pushed",
            "direction": "desc",
            "affiliation": "owner,collaborator",
        })
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        page += 1
        if len(batch) < 100:
            break
    return repos


def get_repo_commits(
    token: str,
    owner: str,
    repo: str,
    author: str,
    since_iso: str,
    max_pages: int = 3,
) -> list[dict]:
    """
    Fetch commits in `owner/repo` authored by `author` since `since_iso`.
    Caps at max_pages × 100 commits per repo to stay within rate limits.
    """
    commits: list[dict] = []
    page = 1
    while page <= max_pages:
        try:
            batch = _gh_request(
                f"/repos/{owner}/{repo}/commits",
                token,
                {
                    "author": author,
                    "since": since_iso,
                    "per_page": 100,
                    "page": page,
                },
            )
        except HTTPError as exc:
            if exc.code in (403, 409, 422):
                break
            raise
        except URLError:
            break

        if not isinstance(batch, list) or not batch:
            break

        for item in batch:
            commit_data = item.get("commit", {})
            author_data = commit_data.get("author", {})
            commits.append({
                "repo": f"{owner}/{repo}",
                "sha": (item.get("sha") or "")[:7],
                "timestamp": author_data.get("date", ""),
                "message": (commit_data.get("message") or "").split("\n")[0][:100],
            })

        page += 1
        if len(batch) < 100:
            break

    return commits


def fetch_all_commits(
    token: str,
    months: int = 12,
    max_repos: int = 50,
    verbose: bool = False,
) -> tuple[str, list[dict]]:
    """
    Fetch all commits by the authenticated user across their repos
    for the past `months` months.

    Returns (username, commits_list).
    """
    since_dt = datetime.now(timezone.utc) - timedelta(days=months * 30)
    since_iso = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    user = get_authenticated_user(token)
    username: str = user["login"]

    repos = get_user_repos(token)
    if verbose:
        print(f"Found {len(repos)} repos for {username}")

    all_commits: list[dict] = []
    checked = 0
    for repo in repos[:max_repos]:
        pushed_at = repo.get("pushed_at") or ""
        if pushed_at and pushed_at < since_iso:
            continue  # no activity in our window

        owner = repo["owner"]["login"]
        name = repo["name"]
        if verbose:
            print(f"  Fetching {owner}/{name}...")

        try:
            commits = get_repo_commits(token, owner, name, username, since_iso)
            all_commits.extend(commits)
            checked += 1
        except Exception as exc:
            if verbose:
                print(f"    Skipped ({exc})")

        # Polite rate limiting: 1 request per 0.1s average
        time.sleep(0.05)

    if verbose:
        print(f"Checked {checked} repos, fetched {len(all_commits)} commits")

    # Deduplicate (same SHA can appear in forks)
    seen: set[str] = set()
    unique: list[dict] = []
    for c in all_commits:
        key = c["sha"] + c["timestamp"]
        if key not in seen:
            seen.add(key)
            unique.append(c)

    unique.sort(key=lambda c: c["timestamp"], reverse=True)
    return username, unique
