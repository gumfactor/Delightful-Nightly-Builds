"""Thin GitHub REST API client using only the stdlib.

Every function here is a pure HTTP boundary — tests mock `_request`
directly and never make a live call. The build container's egress proxy
blocks most external hosts anyway, so this is designed for the user's own
runtime, per CLAUDE.md's API-access guidance.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

GITHUB_API = "https://api.github.com"


class GitHubAPIError(Exception):
    pass


def _request(url, token, params=None):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "bugtrace",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise GitHubAPIError(f"GitHub API HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise GitHubAPIError(f"GitHub API unreachable: {exc.reason}") from exc


def list_user_repos(token, include_forks=False, max_repos=200, request_fn=None):
    request_fn = request_fn or _request
    repos = []
    page = 1
    while len(repos) < max_repos:
        data = request_fn(
            f"{GITHUB_API}/user/repos", token, params={"per_page": 100, "page": page, "affiliation": "owner"}
        )
        if not data:
            break
        for repo in data:
            if not include_forks and repo.get("fork"):
                continue
            repos.append(repo["full_name"])
        if len(data) < 100:
            break
        page += 1
    return repos[:max_repos]


def list_fix_candidate_commits(token, owner_repo, since_iso=None, limit=500, request_fn=None):
    request_fn = request_fn or _request
    commits = []
    page = 1
    while len(commits) < limit:
        params = {"per_page": 100, "page": page}
        if since_iso:
            params["since"] = since_iso
        data = request_fn(f"{GITHUB_API}/repos/{owner_repo}/commits", token, params=params)
        if not data:
            break
        commits.extend(data)
        if len(data) < 100:
            break
        page += 1
    return commits[:limit]


def get_commit_detail(token, owner_repo, sha, request_fn=None):
    request_fn = request_fn or _request
    return request_fn(f"{GITHUB_API}/repos/{owner_repo}/commits/{sha}", token)
