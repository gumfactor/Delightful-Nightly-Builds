"""NCBI E-utilities client — free, no-auth PubMed access.

Uses esearch.fcgi to resolve a search query into PMIDs and efetch.fcgi to
fetch each article's title/abstract/journal/year as XML. Every network
call goes through urllib.request.urlopen so it can be monkeypatched in
tests; no test in this build ever hits the real network.

This build container's egress proxy is expected to block
eutils.ncbi.nlm.nih.gov — that is a build-environment constraint, not a
reason to redesign around mock data. The tool is designed for the user's
local runtime, where PubMed's public API is freely reachable.
"""
import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_TIMEOUT_SECONDS = 20


class PubMedError(Exception):
    """Raised when PubMed cannot be reached or returns an unusable response."""


@dataclass
class PubMedArticle:
    pmid: str
    title: str
    abstract: str
    journal: Optional[str]
    pub_year: Optional[int]


def search_pmids(query: str, retmax: int = 10) -> List[str]:
    """Resolve a free-text PubMed search query into a list of PMIDs."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(retmax),
        "retmode": "json",
        "sort": "relevance",
    }
    url = f"{_ESEARCH_URL}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError) as exc:
        raise PubMedError(f"esearch failed: {exc}") from exc

    try:
        return list(body["esearchresult"]["idlist"])
    except (KeyError, TypeError) as exc:
        raise PubMedError("esearch returned an unexpected response shape") from exc


def fetch_articles(pmids: List[str]) -> List[PubMedArticle]:
    """Fetch title/abstract/journal/year for a list of PMIDs.

    Articles with no PMID, no title, or no abstract text are skipped —
    there is nothing usable to build a teaching case from."""
    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "abstract",
        "retmode": "xml",
    }
    url = f"{_EFETCH_URL}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT_SECONDS) as response:
            raw_xml = response.read()
    except urllib.error.URLError as exc:
        raise PubMedError(f"efetch failed: {exc}") from exc

    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as exc:
        raise PubMedError(f"efetch returned unparseable XML: {exc}") from exc

    articles = []
    for article_elem in root.findall(".//PubmedArticle"):
        parsed = _parse_article(article_elem)
        if parsed is not None:
            articles.append(parsed)
    return articles


def _parse_article(article_elem) -> Optional[PubMedArticle]:
    pmid_elem = article_elem.find(".//PMID")
    if pmid_elem is None or not (pmid_elem.text or "").strip():
        return None
    pmid = pmid_elem.text.strip()

    title_elem = article_elem.find(".//ArticleTitle")
    title = "".join(title_elem.itertext()).strip() if title_elem is not None else ""
    if not title:
        return None

    abstract_parts = [
        "".join(node.itertext()).strip()
        for node in article_elem.findall(".//Abstract/AbstractText")
    ]
    abstract = " ".join(part for part in abstract_parts if part).strip()
    if not abstract:
        return None

    journal_elem = article_elem.find(".//Journal/Title")
    journal = (
        journal_elem.text.strip()
        if journal_elem is not None and journal_elem.text
        else None
    )

    pub_year = _extract_pub_year(article_elem)

    return PubMedArticle(
        pmid=pmid, title=title, abstract=abstract, journal=journal, pub_year=pub_year
    )


def _extract_pub_year(article_elem) -> Optional[int]:
    year_elem = article_elem.find(".//JournalIssue/PubDate/Year")
    if year_elem is not None and year_elem.text and year_elem.text.strip().isdigit():
        return int(year_elem.text.strip())

    medline_date_elem = article_elem.find(".//JournalIssue/PubDate/MedlineDate")
    if medline_date_elem is not None and medline_date_elem.text:
        digits = "".join(ch for ch in medline_date_elem.text[:4] if ch.isdigit())
        if len(digits) == 4:
            return int(digits)

    return None
