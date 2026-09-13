"""Client for arXiv's public Atom API (export.arxiv.org/api/query).

Free, public, no authentication required. See https://info.arxiv.org/help/api/
for the documented terms of use, including the courtesy rate limit this
client honors (a short delay between paginated requests).
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional
from xml.etree import ElementTree as ET

ARXIV_API_BASE = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
PAGE_SIZE = 50
COURTESY_DELAY_SECONDS = 3.0


class ArxivClientError(Exception):
    """Raised when the arXiv API cannot be reached or returns unusable data."""


@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published: date
    categories: list[str]
    pdf_url: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["published"] = self.published.isoformat()
        return d

    @staticmethod
    def from_dict(d: dict) -> "Paper":
        d = dict(d)
        d["published"] = date.fromisoformat(d["published"])
        return Paper(**d)


def _build_query(topic: str, categories: Optional[list[str]]) -> str:
    """Build the arXiv `search_query` value for a topic + optional category filter."""
    # arXiv's search syntax: quote multi-word phrases, AND category filters together.
    terms = [f'all:"{topic}"'] if " " in topic.strip() else [f"all:{topic.strip()}"]
    if categories:
        cat_clause = " OR ".join(f"cat:{c}" for c in categories)
        terms.append(f"({cat_clause})")
    return " AND ".join(terms)


def _build_url(search_query: str, start: int, max_results: int) -> str:
    params = {
        "search_query": search_query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    return f"{ARXIV_API_BASE}?{urllib.parse.urlencode(params)}"


def _parse_entry(entry: ET.Element) -> Optional[Paper]:
    id_el = entry.find("atom:id", ATOM_NS)
    title_el = entry.find("atom:title", ATOM_NS)
    summary_el = entry.find("atom:summary", ATOM_NS)
    published_el = entry.find("atom:published", ATOM_NS)
    if id_el is None or title_el is None or published_el is None:
        return None

    raw_id = id_el.text.strip() if id_el.text else ""
    arxiv_id = raw_id.rsplit("/", 1)[-1] if raw_id else ""
    if not arxiv_id:
        return None

    title = " ".join((title_el.text or "").split())
    abstract = " ".join((summary_el.text or "").split()) if summary_el is not None else ""

    try:
        published = datetime.fromisoformat(
            published_el.text.strip().replace("Z", "+00:00")
        ).date()
    except (ValueError, AttributeError):
        return None

    authors = []
    for author_el in entry.findall("atom:author", ATOM_NS):
        name_el = author_el.find("atom:name", ATOM_NS)
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())

    categories = []
    for cat_el in entry.findall("atom:category", ATOM_NS):
        term = cat_el.get("term")
        if term:
            categories.append(term)

    pdf_url = ""
    for link_el in entry.findall("atom:link", ATOM_NS):
        if link_el.get("title") == "pdf" or link_el.get("type") == "application/pdf":
            pdf_url = link_el.get("href", "")
            break
    if not pdf_url and raw_id:
        pdf_url = raw_id.replace("/abs/", "/pdf/")

    return Paper(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        abstract=abstract,
        published=published,
        categories=categories,
        pdf_url=pdf_url,
    )


def parse_atom_response(xml_text: str) -> list[Paper]:
    """Parse a raw Atom XML response body into a list of Paper records."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ArxivClientError(f"Could not parse arXiv response: {exc}") from exc

    papers = []
    for entry in root.findall("atom:entry", ATOM_NS):
        paper = _parse_entry(entry)
        if paper is not None:
            papers.append(paper)
    return papers


def _query_hash(topic: str, categories: Optional[list[str]], months: int) -> str:
    key = json.dumps(
        {"topic": topic, "categories": sorted(categories or []), "months": months},
        sort_keys=True,
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def _load_cache(cache_path: Path, ttl_hours: int, now: datetime) -> Optional[list[Paper]]:
    if not cache_path.exists():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    fetched_at = payload.get("fetched_at")
    if not fetched_at:
        return None
    try:
        fetched_dt = datetime.fromisoformat(fetched_at)
    except ValueError:
        return None
    if now - fetched_dt > timedelta(hours=ttl_hours):
        return None
    try:
        return [Paper.from_dict(p) for p in payload.get("papers", [])]
    except (KeyError, ValueError):
        return None


def _write_cache(cache_path: Path, papers: list[Paper], now: datetime) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": now.isoformat(),
        "papers": [p.to_dict() for p in papers],
    }
    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def fetch_papers(
    topic: str,
    categories: Optional[list[str]] = None,
    months: int = 18,
    max_results: int = 150,
    cache_dir: Optional[Path] = None,
    cache_ttl_hours: int = 24,
    use_cache: bool = True,
    urlopen: Callable = urllib.request.urlopen,
    sleep: Callable[[float], None] = time.sleep,
    now: Optional[datetime] = None,
) -> list[Paper]:
    """Fetch papers matching `topic` published within the trailing `months`.

    `urlopen`, `sleep`, and `now` are injectable for testing; production
    callers should leave them at their defaults.
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now.date() - timedelta(days=30 * months)

    cache_path = None
    if cache_dir is not None:
        cache_path = Path(cache_dir) / f"{_query_hash(topic, categories, months)}.json"
        if use_cache:
            cached = _load_cache(cache_path, cache_ttl_hours, now)
            if cached is not None:
                return [p for p in cached if p.published >= cutoff]

    search_query = _build_query(topic, categories)
    all_papers: list[Paper] = []
    seen_ids: set[str] = set()
    start = 0

    while len(all_papers) < max_results:
        page_size = min(PAGE_SIZE, max_results - len(all_papers))
        url = _build_url(search_query, start, page_size)
        try:
            with urlopen(url, timeout=30) as response:
                xml_text = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise ArxivClientError(f"Could not reach arXiv API: {exc}") from exc
        except TimeoutError as exc:
            raise ArxivClientError(f"arXiv API request timed out: {exc}") from exc

        page_papers = parse_atom_response(xml_text)
        if not page_papers:
            break

        new_this_page = 0
        stop_early = False
        for paper in page_papers:
            if paper.arxiv_id in seen_ids:
                continue
            seen_ids.add(paper.arxiv_id)
            if paper.published < cutoff:
                # Results are sorted by submittedDate descending, so once we
                # fall below the cutoff every remaining page is also too old.
                stop_early = True
                continue
            all_papers.append(paper)
            new_this_page += 1

        start += page_size
        if stop_early or new_this_page == 0 or len(page_papers) < page_size:
            break
        sleep(COURTESY_DELAY_SECONDS)

    if cache_path is not None:
        _write_cache(cache_path, all_papers, now)

    return all_papers
