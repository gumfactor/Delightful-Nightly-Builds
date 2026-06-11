"""GitHub REST API client using stdlib urllib. No external dependencies."""
import json
import urllib.error
import urllib.request
from typing import Optional

BASE_URL = "https://api.github.com"


def _get(url: str, token: str) -> list | dict:
    """
    Make an authenticated GET request to the GitHub API.
    Raises RuntimeError with a descriptive message on HTTP errors.
    """
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {err.code}: {body}") from err
    except urllib.error.URLError as err:
        raise RuntimeError(f"Network error: {err.reason}") from err


def fetch_repos(
    token: str,
    limit: int = 30,
    org: Optional[str] = None,
) -> list[dict]:
    """
    Fetch up to `limit` repositories sorted by most-recently-pushed.
    Uses the authenticated user's repos unless `org` is specified.
    Paginates automatically until `limit` is reached or all repos are fetched.
    """
    all_repos: list[dict] = []
    page = 1
    per_page = min(100, max(1, limit))

    while len(all_repos) < limit:
        if org:
            url = (
                f"{BASE_URL}/orgs/{org}/repos"
                f"?sort=pushed&direction=desc&per_page={per_page}&page={page}&type=all"
            )
        else:
            url = (
                f"{BASE_URL}/user/repos"
                f"?sort=pushed&direction=desc&per_page={per_page}&page={page}"
            )

        batch = _get(url, token)
        if not isinstance(batch, list) or not batch:
            break
        all_repos.extend(batch)
        if len(batch) < per_page:
            break
        page += 1

    return all_repos[:limit]
