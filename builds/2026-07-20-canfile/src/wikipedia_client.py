"""Thin client for the public, no-auth Wikipedia REST summary API."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

WIKIPEDIA_SUMMARY_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
USER_AGENT = "CanFile/1.0 (personal knowledge tool; contact via GitHub)"


class WikipediaError(RuntimeError):
    """Raised when the Wikipedia API is unreachable or returns malformed data."""


def _api_get(title: str, timeout: float = 10.0) -> dict[str, Any] | None:
    encoded_title = urllib.parse.quote(title.replace(" ", "_"))
    url = f"{WIKIPEDIA_SUMMARY_API}{encoded_title}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise WikipediaError(f"Wikipedia request failed: {exc}") from exc
    except Exception as exc:
        raise WikipediaError(f"Wikipedia request failed: {exc}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise WikipediaError(f"Wikipedia returned invalid JSON: {exc}") from exc


def get_summary(title: str) -> dict[str, str] | None:
    """Fetch a plain-English summary for a Wikipedia page title.

    Returns None if the page does not exist (404), rather than raising,
    since a missing Wikipedia page is a normal outcome, not an error.
    """
    data = _api_get(title)
    if data is None:
        return None
    extract = data.get("extract", "")
    page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
    if not page_url:
        page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
    return {"title": data.get("title", title), "extract": extract, "url": page_url}
