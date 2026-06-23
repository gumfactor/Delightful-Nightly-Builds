"""arXiv API client — fetches paper metadata from the Atom feed."""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_BASE_URL = "https://export.arxiv.org/api/query"

# Topics tailored to user's research areas (PROFILE.md)
TOPICS = [
    {
        "name": "Affective Neuroscience",
        "query": "cat:q-bio.NC",
        "max_results": 15,
    },
    {
        "name": "Psychopathy & Empathy",
        "query": "ti:psychopathy OR ti:empathy",
        "max_results": 10,
    },
    {
        "name": "Stress & HPA",
        "query": "ti:stress AND ti:neuroscience",
        "max_results": 8,
    },
    {
        "name": "AI Agents & LLMs",
        "query": 'cat:cs.AI AND (ti:agent OR ti:autonomous)',
        "max_results": 12,
    },
]


def build_query_url(query: str, max_results: int, start: int = 0) -> str:
    params = {
        "search_query": query,
        "start": str(start),
        "max_results": str(max_results),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    return ARXIV_BASE_URL + "?" + urllib.parse.urlencode(params)


def fetch_arxiv_papers(query: str, max_results: int) -> list:
    """Fetch papers from arXiv for a given query. Returns empty list on any error."""
    url = build_query_url(query, max_results)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PaperLens/1.0 (nightly research tool)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_data = resp.read()
        return parse_atom_feed(xml_data)
    except Exception:
        return []


def fetch_all_topics() -> list:
    """Fetch papers for all configured topics, deduplicating by arxiv_id."""
    seen_ids: set = set()
    all_papers = []
    for topic in TOPICS:
        papers = fetch_arxiv_papers(topic["query"], topic["max_results"])
        for paper in papers:
            if paper["arxiv_id"] not in seen_ids:
                seen_ids.add(paper["arxiv_id"])
                all_papers.append(paper)
    return all_papers


def parse_atom_feed(xml_data: bytes) -> list:
    """Parse arXiv Atom XML and return a list of paper dicts."""
    root = ET.fromstring(xml_data)
    papers = []
    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        paper = _parse_entry(entry)
        if paper:
            papers.append(paper)
    return papers


def _parse_entry(entry: ET.Element) -> dict:
    id_elem = entry.find(f"{{{ATOM_NS}}}id")
    title_elem = entry.find(f"{{{ATOM_NS}}}title")
    summary_elem = entry.find(f"{{{ATOM_NS}}}summary")
    published_elem = entry.find(f"{{{ATOM_NS}}}published")
    author_elems = entry.findall(f"{{{ATOM_NS}}}author")

    if id_elem is None or title_elem is None:
        return {}

    raw_id = (id_elem.text or "").strip()
    arxiv_id = _extract_arxiv_id(raw_id)
    if not arxiv_id:
        return {}

    authors = []
    for a in author_elems:
        name_elem = a.find(f"{{{ATOM_NS}}}name")
        if name_elem is not None and name_elem.text:
            authors.append(name_elem.text.strip())

    title = (title_elem.text or "").strip()
    abstract = (summary_elem.text or "").strip() if summary_elem is not None else ""
    published = (published_elem.text or "").strip()[:10] if published_elem is not None else ""

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": ", ".join(authors),
        "abstract": abstract,
        "published_date": published,
    }


def _extract_arxiv_id(raw_id: str) -> str:
    """Extract bare arxiv ID from a URL like http://arxiv.org/abs/2410.00001v2."""
    if "/abs/" in raw_id:
        arxiv_id = raw_id.split("/abs/")[-1]
        # Strip version suffix (v1, v2, …)
        parts = arxiv_id.rsplit("v", 1)
        if len(parts) == 2 and parts[1].isdigit():
            arxiv_id = parts[0]
        return arxiv_id
    return raw_id
