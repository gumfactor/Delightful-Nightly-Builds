"""Minimal client for the free, no-auth OpenAlex API (https://api.openalex.org).

Only the endpoints Impact Ledger needs are implemented: author search,
a single author lookup, and a cursor-paginated walk of an author's works.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterator

BASE_URL = "https://api.openalex.org"
USER_AGENT = "ImpactLedger/1.0 (nightly-build; personal research-impact tracker)"
REQUEST_TIMEOUT_SECONDS = 15


class OpenAlexError(Exception):
    """Raised when an OpenAlex request fails or returns unexpected data."""


def _get_json(path: str, params: dict[str, Any], mailto: str | None = None) -> dict[str, Any]:
    query = dict(params)
    if mailto:
        query["mailto"] = mailto
    url = f"{BASE_URL}{path}?{urllib.parse.urlencode(query)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise OpenAlexError(f"OpenAlex returned HTTP {exc.code} for {path}") from exc
    except urllib.error.URLError as exc:
        raise OpenAlexError(f"Could not reach OpenAlex ({exc.reason}) for {path}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OpenAlexError(f"OpenAlex returned malformed JSON for {path}") from exc


def search_authors(query: str, mailto: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    """Return up to `limit` candidate authors matching `query`, for disambiguation."""
    if not query.strip():
        raise OpenAlexError("Author search query must not be empty")

    data = _get_json("/authors", {"search": query, "per-page": limit}, mailto=mailto)
    candidates = []
    for entry in data.get("results", []):
        institution = ""
        last_inst = entry.get("last_known_institutions") or entry.get("last_known_institution")
        if isinstance(last_inst, list) and last_inst:
            institution = last_inst[0].get("display_name", "")
        elif isinstance(last_inst, dict):
            institution = last_inst.get("display_name", "")
        candidates.append(
            {
                "author_id": _short_id(entry.get("id", "")),
                "display_name": entry.get("display_name", "Unknown"),
                "institution": institution,
                "works_count": entry.get("works_count", 0),
                "cited_by_count": entry.get("cited_by_count", 0),
            }
        )
    return candidates


def get_author(author_id: str, mailto: str | None = None) -> dict[str, Any]:
    """Fetch an author's summary profile by OpenAlex ID."""
    data = _get_json(f"/authors/{author_id}", {}, mailto=mailto)
    summary_stats = data.get("summary_stats", {}) or {}
    return {
        "author_id": _short_id(data.get("id", author_id)),
        "display_name": data.get("display_name", "Unknown"),
        "works_count": data.get("works_count", 0),
        "cited_by_count": data.get("cited_by_count", 0),
        "h_index": summary_stats.get("h_index"),
        "i10_index": summary_stats.get("i10_index"),
    }


def iter_author_works(author_id: str, mailto: str | None = None, per_page: int = 200) -> Iterator[dict[str, Any]]:
    """Cursor-paginate through every work for an author, yielding normalized records."""
    cursor = "*"
    while cursor:
        data = _get_json(
            "/works",
            {"filter": f"author.id:{author_id}", "per-page": per_page, "cursor": cursor},
            mailto=mailto,
        )
        for work in data.get("results", []):
            yield _normalize_work(work)

        meta = data.get("meta", {}) or {}
        cursor = meta.get("next_cursor")
        if not data.get("results"):
            break


def _normalize_work(work: dict[str, Any]) -> dict[str, Any]:
    host_venue = ""
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    if source:
        host_venue = source.get("display_name", "") or ""

    concepts = [c.get("display_name", "") for c in work.get("concepts", []) if c.get("display_name")]

    return {
        "work_id": _short_id(work.get("id", "")),
        "title": work.get("title") or work.get("display_name") or "Untitled",
        "publication_year": work.get("publication_year"),
        "doi": work.get("doi"),
        "host_venue": host_venue,
        "cited_by_count": work.get("cited_by_count", 0),
        "concepts": concepts,
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
    }


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """Rebuild plain-text abstract from OpenAlex's word-position inverted index."""
    if not inverted_index:
        return ""

    max_position = max(pos for positions in inverted_index.values() for pos in positions)
    words: list[str] = [""] * (max_position + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(w for w in words if w)


def _short_id(full_id: str) -> str:
    """OpenAlex IDs are full URLs like 'https://openalex.org/A5023888391'; keep just the ID."""
    return full_id.rsplit("/", 1)[-1] if full_id else ""
