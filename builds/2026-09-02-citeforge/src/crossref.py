"""DOI resolution via the free, no-auth Crossref REST API.

The HTTP transport is injectable so tests never make a real network call —
every test passes a fake transport function and asserts on call counts.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable

from .models import Author, Reference, normalize_doi

CROSSREF_BASE = "https://api.crossref.org/works/"
USER_AGENT = "CiteForge/1.0 (personal citation formatting tool; mailto:contact@example.com)"

Transport = Callable[[str], bytes]

_TYPE_MAP = {
    "journal-article": "journal-article",
    "proceedings-article": "journal-article",
    "book": "book",
    "monograph": "book",
    "book-chapter": "book",
    "posted-content": "webpage",
}


class CrossrefError(Exception):
    pass


def default_transport(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 (fixed https host)
        return response.read()


def fetch_doi_metadata(doi: str, transport: Transport = default_transport) -> dict:
    clean_doi = normalize_doi(doi)
    if not clean_doi:
        raise CrossrefError("Empty DOI")
    url = CROSSREF_BASE + clean_doi
    try:
        raw = transport(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise CrossrefError(f"DOI not found on Crossref: {doi}") from exc
        raise CrossrefError(f"Crossref request failed ({exc.code}) for {doi}") from exc
    except urllib.error.URLError as exc:
        raise CrossrefError(f"Network error resolving {doi}: {exc.reason}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CrossrefError(f"Crossref returned malformed JSON for {doi}") from exc
    message = payload.get("message")
    if not message:
        raise CrossrefError(f"Crossref response for {doi} had no 'message' field")
    return message


def _crossref_authors(message: dict) -> list[Author]:
    authors = []
    for item in message.get("author", []):
        family = item.get("family", "")
        given = item.get("given", "")
        if family:
            authors.append(Author(family=family, given=given))
    return authors


def _crossref_year(message: dict) -> str:
    for key in ("published-print", "published-online", "issued", "created"):
        date_parts = message.get(key, {}).get("date-parts")
        if date_parts and date_parts[0]:
            return str(date_parts[0][0])
    return ""


def message_to_reference(message: dict) -> Reference:
    crossref_type = message.get("type", "")
    ref_type = _TYPE_MAP.get(crossref_type, "other")
    titles = message.get("title") or []
    title = titles[0] if titles else ""
    container_titles = message.get("container-title") or []
    container = container_titles[0] if container_titles else ""
    return Reference(
        ref_type=ref_type,
        authors=_crossref_authors(message),
        year=_crossref_year(message),
        title=title,
        container_title=container,
        volume=message.get("volume", ""),
        issue=message.get("issue", ""),
        pages=message.get("page", ""),
        doi=message.get("DOI", ""),
        url=message.get("URL", ""),
        source="crossref",
    )


def resolve_doi(doi: str, transport: Transport = default_transport) -> Reference:
    message = fetch_doi_metadata(doi, transport=transport)
    return message_to_reference(message)
