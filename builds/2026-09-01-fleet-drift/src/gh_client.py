"""GitHub REST API client — list owned repos, fetch manifest file contents.

Uses only ``GITHUB_TOKEN`` (already available at the user's runtime per
PROFILE.md's Data Sources) and the real GitHub REST API shapes. Every call
accepts an injectable ``transport`` so tests never touch the network.
"""
from __future__ import annotations

import base64
import json
from typing import List, Optional

from .http import Transport, default_transport

_API_ROOT = "https://api.github.com"
_PER_PAGE = 100


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "fleet-drift/1.0 (nightly-build tool)",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def list_owned_repos(token: str, transport: Transport = default_transport) -> List[str]:
    """Return every repo the token's owner owns, as 'owner/repo' full names."""
    repos: List[str] = []
    page = 1
    while True:
        url = f"{_API_ROOT}/user/repos?type=owner&per_page={_PER_PAGE}&page={page}"
        status, body = transport(url, _headers(token))
        if status != 200:
            break
        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            break
        if not isinstance(data, list) or not data:
            break
        for repo in data:
            full_name = repo.get("full_name") if isinstance(repo, dict) else None
            if full_name:
                repos.append(full_name)
        if len(data) < _PER_PAGE:
            break
        page += 1
    return repos


def fetch_file_content(
    token: str, repo_full_name: str, path: str, transport: Transport = default_transport
) -> Optional[str]:
    """Return a repo file's decoded text content on its default branch, or
    None if the file doesn't exist (404) or can't be decoded."""
    url = f"{_API_ROOT}/repos/{repo_full_name}/contents/{path}"
    status, body = transport(url, _headers(token))
    if status != 200:
        return None
    try:
        data = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict) or data.get("encoding") != "base64":
        return None
    try:
        return base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    except (ValueError, TypeError):
        return None
