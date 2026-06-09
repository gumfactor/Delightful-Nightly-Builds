"""Fetch commits from the GitHub API using only stdlib."""

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Optional


BASE = "https://api.github.com"
_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _get(url: str, token: str) -> list | dict:
    headers = dict(_HEADERS)
    headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_user_repos(username: str, token: str, exclude: list[str] | None = None) -> list[str]:
    """Return all non-archived repo names for the given user."""
    exclude = exclude or []
    repos: list[str] = []
    page = 1
    while True:
        url = f"{BASE}/users/{username}/repos?per_page=100&page={page}&type=all"
        try:
            data = _get(url, token)
        except Exception:
            break
        if not isinstance(data, list) or not data:
            break
        for repo in data:
            name = repo.get("name", "")
            if name and name not in exclude and not repo.get("archived", False):
                repos.append(name)
        if len(data) < 100:
            break
        page += 1
    return repos


def get_commits_since(
    username: str,
    repo: str,
    token: str,
    hours: int,
    author: Optional[str] = None,
) -> list[dict]:
    """Return commits pushed to the repo in the last N hours."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    url = f"{BASE}/repos/{username}/{repo}/commits?since={since}&per_page=100"
    try:
        data = _get(url, token)
    except urllib.error.HTTPError as e:
        if e.code in (404, 409):  # 409 = empty repo
            return []
        raise
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    commits: list[dict] = []
    for item in data:
        sha = item.get("sha", "")
        commit = item.get("commit", {})
        message = commit.get("message", "").split("\n")[0]
        author_name = commit.get("author", {}).get("name", "")
        timestamp = commit.get("author", {}).get("date", "")
        if author and author.lower() not in author_name.lower():
            continue
        commits.append(
            {
                "hash": sha[:8],
                "sha": sha,
                "message": message,
                "author": author_name,
                "timestamp": timestamp,
                "repo": repo,
                "source": "github",
            }
        )
    return commits
