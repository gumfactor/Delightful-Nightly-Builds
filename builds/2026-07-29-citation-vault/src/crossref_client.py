"""Crossref REST API client — DOI lookup and free-text search.

Crossref (api.crossref.org) is free and requires no authentication. Every
network call goes through an injectable `request_fn(url) -> bytes` so tests
never touch the network.
"""

import json
import urllib.request
import urllib.parse
from typing import Callable, Optional

CROSSREF_BASE = "https://api.crossref.org"
USER_AGENT = "CitationVault/1.0 (personal research tool; mailto:user@example.com)"


class CrossrefError(Exception):
    pass


def default_request_fn(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read()


def _extract_authors(message: dict) -> list:
    authors = []
    for a in message.get("author", []):
        if "given" in a and "family" in a:
            authors.append(f"{a['given']} {a['family']}")
        elif "family" in a:
            authors.append(a["family"])
        elif "name" in a:
            authors.append(a["name"])
    return authors


def _extract_year(message: dict) -> Optional[int]:
    for key in ("published-print", "published-online", "published", "issued"):
        block = message.get(key)
        if block and block.get("date-parts"):
            parts = block["date-parts"][0]
            if parts and parts[0]:
                return int(parts[0])
    return None


def _message_to_paper(message: dict) -> dict:
    title_list = message.get("title") or [""]
    container = message.get("container-title") or [""]
    return {
        "doi": message.get("DOI"),
        "title": title_list[0] if title_list else "",
        "authors": _extract_authors(message),
        "year": _extract_year(message),
        "journal": container[0] if container else None,
        "abstract": message.get("abstract"),
    }


def lookup_doi(doi: str, request_fn: Callable[[str], bytes] = default_request_fn) -> dict:
    doi_clean = doi.strip().lower().removeprefix("https://doi.org/").removeprefix("doi:")
    url = f"{CROSSREF_BASE}/works/{urllib.parse.quote(doi_clean, safe='')}"
    try:
        raw = request_fn(url)
    except Exception as exc:
        raise CrossrefError(f"Crossref lookup failed for DOI {doi_clean}: {exc}") from exc
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise CrossrefError(f"Crossref returned malformed JSON for DOI {doi_clean}: {exc}") from exc
    message = data.get("message")
    if not message:
        raise CrossrefError(f"Crossref response for DOI {doi_clean} had no 'message' field")
    return _message_to_paper(message)


def search(query: str, limit: int = 5, request_fn: Callable[[str], bytes] = default_request_fn) -> list:
    params = urllib.parse.urlencode({"query": query, "rows": limit})
    url = f"{CROSSREF_BASE}/works?{params}"
    try:
        raw = request_fn(url)
    except Exception as exc:
        raise CrossrefError(f"Crossref search failed for query '{query}': {exc}") from exc
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise CrossrefError(f"Crossref returned malformed JSON for query '{query}': {exc}") from exc
    items = (data.get("message") or {}).get("items") or []
    return [_message_to_paper(item) for item in items]
