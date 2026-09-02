"""Free-text reference-line structuring: deterministic regex first, optional
Claude Haiku fallback second.

The deterministic pre-pass runs unconditionally and makes zero network
calls. The AI fallback only fires when explicitly requested (`use_ai=True`)
**and** `ANTHROPIC_API_KEY` is set **and** the regex pass could not
confidently fill the required fields. A line neither pass can structure is
returned flagged `needs_review=True` rather than guessed.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Callable

from .models import Author, Reference

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

_YEAR_RE = re.compile(r"\((\d{4})\)|\b(\d{4})\b")
_DOI_RE = re.compile(r"10\.\d{4,9}/\S+")
_QUOTED_TITLE_RE = re.compile(r'"([^"]{5,300})"')

Transport = Callable[[str, dict], bytes]

_SYSTEM_PROMPT = (
    "Extract this academic reference's fields as compact JSON with keys "
    "family_names (list of strings), given_names (list of strings, same order "
    "and length as family_names), year (string), title (string), "
    "container_title (string, journal or publisher or site name), "
    "volume (string), issue (string), pages (string), doi (string). "
    "Use an empty string or empty list for any field you cannot determine. "
    "Return only the JSON object — no prose, no markdown code fences."
)


def regex_extract(line: str) -> Reference | None:
    """Best-effort deterministic extraction. None if input is empty."""
    line = line.strip()
    if not line:
        return None
    year_match = _YEAR_RE.search(line)
    year = ""
    if year_match:
        year = year_match.group(1) or year_match.group(2) or ""
    doi_match = _DOI_RE.search(line)
    doi = doi_match.group(0).rstrip(".,;") if doi_match else ""
    title_match = _QUOTED_TITLE_RE.search(line)
    title = title_match.group(1) if title_match else ""

    confident = bool(year and title)
    author_source = line[: year_match.start()] if year_match else line
    authors = _parse_author_prefix(author_source.strip().rstrip(".,"))

    if not confident:
        return Reference(
            ref_type="other", authors=authors, year=year, title=title or line,
            doi=doi, source="text-regex", needs_review=True,
        )
    return Reference(
        ref_type="other", authors=authors, year=year, title=title, doi=doi,
        source="text-regex", needs_review=not authors,
    )


def _parse_author_prefix(text: str) -> list[Author]:
    if not text:
        return []
    parts = [p for p in re.split(r",\s*(?:&|and)\s*|,\s*|\s+&\s+|\s+and\s+", text) if p.strip()]
    authors = []
    for part in parts:
        tokens = part.strip().split()
        if not tokens:
            continue
        if len(tokens) == 1:
            authors.append(Author(family=tokens[0]))
        else:
            authors.append(Author(family=tokens[0], given=" ".join(tokens[1:])))
    return authors


def default_transport(url: str, payload: dict) -> bytes:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "x-api-key": os.environ.get("ANTHROPIC_API_KEY", ""),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 (fixed https host)
        return response.read()


def ai_extract_reference(
    line: str, api_key: str, transport: Transport = default_transport
) -> Reference | None:
    if not api_key:
        return None
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 400,
        "system": _SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": line}],
    }
    try:
        raw = transport(ANTHROPIC_URL, payload)
    except (urllib.error.HTTPError, urllib.error.URLError):
        return None
    try:
        response = json.loads(raw)
        text = response["content"][0]["text"]
        fields = json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None
    families = fields.get("family_names") or []
    givens = fields.get("given_names") or []
    authors = [
        Author(family=family, given=(givens[i] if i < len(givens) else ""))
        for i, family in enumerate(families)
        if family
    ]
    title = fields.get("title", "")
    if not title:
        return None
    return Reference(
        ref_type="other",
        authors=authors,
        year=fields.get("year", ""),
        title=title,
        container_title=fields.get("container_title", ""),
        volume=fields.get("volume", ""),
        issue=fields.get("issue", ""),
        pages=fields.get("pages", ""),
        doi=fields.get("doi", ""),
        source="ai-extract",
        needs_review=False,
    )


def extract_reference(
    line: str, use_ai: bool, api_key: str, ai_transport: Transport = default_transport
) -> Reference:
    deterministic = regex_extract(line)
    if deterministic and not deterministic.needs_review:
        return deterministic
    if use_ai and api_key:
        ai_result = ai_extract_reference(line, api_key, transport=ai_transport)
        if ai_result:
            return ai_result
    if deterministic:
        return deterministic
    return Reference(
        ref_type="other", authors=[], year="", title=line.strip(),
        source="text-unparsed", needs_review=True,
    )
