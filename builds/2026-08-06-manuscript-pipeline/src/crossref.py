"""Crossref-based auto-detection of manuscript publication.

Crossref (api.crossref.org) is a free, no-auth API. Every call in this module
is mocked in tests -- no live network access is exercised by the test suite.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from typing import Any

MATCH_THRESHOLD = 0.72
CROSSREF_BASE_URL = "https://api.crossref.org/works"

_WORD_RE = re.compile(r"[a-z0-9]+")


def _normalize_title(title: str) -> list[str]:
    return _WORD_RE.findall(title.lower())


def title_similarity(a: str, b: str) -> float:
    tokens_a = _normalize_title(a)
    tokens_b = _normalize_title(b)
    if not tokens_a or not tokens_b:
        return 0.0
    return SequenceMatcher(None, tokens_a, tokens_b).ratio()


def _surname(author_entry: str) -> str:
    """Best-effort surname extraction from a free-text author string like
    'Jane Doe' or 'Doe, Jane' -- takes the last whitespace-separated token,
    or the part before a comma."""
    entry = author_entry.strip()
    if "," in entry:
        return entry.split(",")[0].strip().lower()
    parts = entry.split()
    return parts[-1].lower() if parts else ""


def authors_overlap(local_authors: str, crossref_authors: list[dict[str, Any]]) -> bool:
    local_surnames = {_surname(a) for a in local_authors.split(",") if a.strip()}
    crossref_surnames = {
        (entry.get("family") or "").strip().lower()
        for entry in crossref_authors
        if entry.get("family")
    }
    return bool(local_surnames & crossref_surnames)


def search_works(title: str, author_surname: str, http_get=None) -> list[dict[str, Any]]:
    """Query Crossref for works matching a bibliographic title + author.
    `http_get` is an injectable callable (url -> bytes) used by tests to
    avoid any live network access; defaults to a real urllib GET."""
    query = urllib.parse.urlencode({
        "query.bibliographic": title,
        "query.author": author_surname,
        "rows": 5,
    })
    url = f"{CROSSREF_BASE_URL}?{query}"

    if http_get is not None:
        raw = http_get(url)
    else:
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                raw = response.read()
        except (urllib.error.URLError, TimeoutError):
            return []

    try:
        data = json.loads(raw)
        return data.get("message", {}).get("items", [])
    except (json.JSONDecodeError, AttributeError):
        return []


def find_publication_match(
    title: str,
    authors: str,
    http_get=None,
) -> dict[str, Any] | None:
    """Returns a dict with doi/container_title/published_date if a confident
    match is found among Crossref search results, else None."""
    first_author_surname = _surname(authors.split(",")[0]) if authors else ""
    items = search_works(title, first_author_surname, http_get=http_get)

    for item in items:
        candidate_title = (item.get("title") or [""])[0]
        if not candidate_title:
            continue
        similarity = title_similarity(title, candidate_title)
        if similarity < MATCH_THRESHOLD:
            continue
        if not authors_overlap(authors, item.get("author", [])):
            continue

        return {
            "doi": item.get("DOI"),
            "container_title": (item.get("container-title") or [""])[0],
            "published_date": _extract_published_date(item),
            "similarity": similarity,
        }
    return None


def _extract_published_date(item: dict[str, Any]) -> str | None:
    for key in ("published", "published-print", "published-online"):
        date_parts = item.get(key, {}).get("date-parts")
        if date_parts and date_parts[0]:
            parts = date_parts[0]
            year = parts[0]
            month = parts[1] if len(parts) > 1 else 1
            day = parts[2] if len(parts) > 2 else 1
            return f"{year:04d}-{month:02d}-{day:02d}"
    return None
