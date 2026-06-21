import json
import urllib.error
import urllib.request
from typing import Callable, Optional


def _default_fetch(url: str, token: str) -> list | dict:
    """Make an authenticated GET request to the GitHub API and return parsed JSON."""
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def list_repos(token: str, fetch: Optional[Callable] = None) -> list[dict]:
    """Fetch all repos for the authenticated user (paginated, all types)."""
    _fetch = fetch or (lambda url: _default_fetch(url, token))
    all_repos: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/user/repos"
            f"?per_page=100&sort=pushed&direction=desc&type=all&page={page}"
        )
        data = _fetch(url)
        if not isinstance(data, list) or not data:
            break
        all_repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return all_repos


def get_latest_ci_run(
    owner: str,
    repo_name: str,
    token: str,
    fetch: Optional[Callable] = None,
) -> Optional[dict]:
    """Return the most recent completed workflow run for the repo, or None."""
    _fetch = fetch or (lambda url: _default_fetch(url, token))
    url = (
        f"https://api.github.com/repos/{owner}/{repo_name}/actions/runs"
        f"?per_page=1"
    )
    try:
        data = _fetch(url)
        runs = data.get("workflow_runs", []) if isinstance(data, dict) else []
        return runs[0] if runs else None
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, IndexError):
        return None
