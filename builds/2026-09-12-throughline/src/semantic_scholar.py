"""Thin client for the free, no-auth Semantic Scholar Graph API.

Every network call goes through a single injectable `transport` callable so
tests never touch the real network. At runtime the default transport is a
plain `urllib.request.urlopen` call.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Optional

API_BASE = "https://api.semanticscholar.org/graph/v1"
USER_AGENT = "Throughline/1.0 (personal research knowledge base)"

Transport = Callable[[str, dict], bytes]


class SemanticScholarError(Exception):
    """Raised when the Semantic Scholar API cannot be reached or returns an error."""


@dataclass
class AuthorCandidate:
    author_id: str
    name: str
    affiliations: list
    paper_count: int
    citation_count: int
    sample_titles: list = field(default_factory=list)


@dataclass
class Paper:
    paper_id: str
    title: str
    abstract: Optional[str]
    year: Optional[int]
    venue: Optional[str]
    citation_count: int
    external_url: Optional[str]


def _default_transport(url: str, headers: dict) -> bytes:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read()


def _headers() -> dict:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    return headers


def _get(url: str, transport: Transport) -> dict:
    try:
        raw = transport(url, _headers())
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise SemanticScholarError(
                "Semantic Scholar rate limit hit (HTTP 429). Wait a few minutes "
                "and retry, or set SEMANTIC_SCHOLAR_API_KEY for a higher limit."
            ) from exc
        raise SemanticScholarError(f"Semantic Scholar API returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise SemanticScholarError(f"Could not reach Semantic Scholar API: {exc.reason}") from exc

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise SemanticScholarError("Semantic Scholar API returned malformed JSON") from exc


def search_authors(name: str, transport: Transport = _default_transport) -> list:
    """Search for candidate authors by name. Returns a disambiguation list."""
    if not name or not name.strip():
        raise ValueError("author name must not be empty")

    query = urllib.parse.quote(name.strip())
    url = (
        f"{API_BASE}/author/search?query={query}"
        "&fields=name,affiliations,paperCount,citationCount,papers.title"
    )
    data = _get(url, transport)

    candidates = []
    for entry in data.get("data", []):
        papers = entry.get("papers") or []
        candidates.append(
            AuthorCandidate(
                author_id=entry.get("authorId", ""),
                name=entry.get("name", "Unknown"),
                affiliations=entry.get("affiliations") or [],
                paper_count=entry.get("paperCount") or 0,
                citation_count=entry.get("citationCount") or 0,
                sample_titles=[p.get("title", "") for p in papers[:3] if p.get("title")],
            )
        )
    return candidates


def fetch_author_papers(author_id: str, transport: Transport = _default_transport) -> list:
    """Fetch the full paper list for a confirmed Semantic Scholar author id."""
    if not author_id or not author_id.strip():
        raise ValueError("author_id must not be empty")

    fields = (
        "name,papers.paperId,papers.title,papers.abstract,papers.year,"
        "papers.venue,papers.citationCount,papers.externalIds"
    )
    url = f"{API_BASE}/author/{urllib.parse.quote(author_id)}?fields={fields}"
    data = _get(url, transport)

    papers = []
    for entry in data.get("papers") or []:
        paper_id = entry.get("paperId")
        if not paper_id:
            continue
        external_ids = entry.get("externalIds") or {}
        doi = external_ids.get("DOI")
        papers.append(
            Paper(
                paper_id=paper_id,
                title=entry.get("title") or "(untitled)",
                abstract=entry.get("abstract"),
                year=entry.get("year"),
                venue=entry.get("venue") or None,
                citation_count=entry.get("citationCount") or 0,
                external_url=f"https://doi.org/{doi}" if doi else entry.get("url"),
            )
        )
    return papers
