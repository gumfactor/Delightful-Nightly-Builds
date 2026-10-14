"""Minimal GitHub REST client: auth, pagination, rate-limit handling.

The network layer is a ``transport`` callable so tests never touch the network.
A transport takes (url, headers) and returns (status, headers, body_bytes).
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any, Callable, Iterator

API_ROOT = "https://api.github.com"
Transport = Callable[[str, dict[str, str]], tuple[int, dict[str, str], bytes]]


class GitHubError(Exception):
    """Any non-recoverable API failure."""


class RateLimitError(GitHubError):
    """Raised when the primary rate limit is exhausted."""


class NotFoundError(GitHubError):
    """404 / 403 / 410: resource missing or Actions disabled for the repo."""


def urllib_transport(url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - https only
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()
    except urllib.error.HTTPError as error:
        return error.code, {k.lower(): v for k, v in error.headers.items()}, error.read()
    except urllib.error.URLError as error:
        raise GitHubError(f"network error: {error.reason}") from error


class GitHubClient:
    def __init__(self, token: str | None, transport: Transport = urllib_transport) -> None:
        self._transport = transport
        self._headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "gha-perf",
        }
        if token:
            self._headers["Authorization"] = f"Bearer {token}"
        self.requests_made = 0

    def _get_with_headers(self, path_or_url: str) -> tuple[Any, dict[str, str]]:
        url = path_or_url if path_or_url.startswith("https://") else API_ROOT + path_or_url
        self.requests_made += 1
        status, headers, body = self._transport(url, self._headers)
        if status == 200:
            return json.loads(body.decode("utf-8")), headers
        if status in (403, 429) and headers.get("x-ratelimit-remaining") == "0":
            raise RateLimitError(f"rate limit exhausted; resets at epoch {headers.get('x-ratelimit-reset', '?')}")
        if status in (403, 404, 410):
            raise NotFoundError(f"HTTP {status} for {url}")
        if status == 401:
            raise GitHubError("HTTP 401 unauthorized: check GITHUB_TOKEN")
        raise GitHubError(f"HTTP {status} for {url}")

    def get(self, path_or_url: str) -> Any:
        return self._get_with_headers(path_or_url)[0]

    def paginate(self, path: str, list_key: str | None = None, max_items: int = 1000) -> Iterator[Any]:
        """Yield items across pages, following Link rel=next, up to ``max_items``."""
        url: str | None = path
        yielded = 0
        while url:
            data, headers = self._get_with_headers(url)
            for item in (data.get(list_key, []) if list_key else data):
                yield item
                yielded += 1
                if yielded >= max_items:
                    return
            match = re.search(r'<([^>]+)>;\s*rel="next"', headers.get("link", ""))
            url = match.group(1) if match else None
