"""PubMed E-utilities client: search + fetch + parse.

Uses the free, no-auth NCBI E-utilities REST API (esearch + efetch).
https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import requests

from src.config import PUBMED_EFETCH_URL, PUBMED_ESEARCH_URL

REQUEST_TIMEOUT_SECONDS = 20


class PubMedError(Exception):
    """Raised when PubMed returns an unusable response."""


def search_pmids(query: str, days: int, retmax: int) -> list[str]:
    """Return a list of PMIDs matching `query` published in the last `days` days."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": str(retmax),
        "datetype": "pdat",
        "reldate": str(days),
        "sort": "most+recent",
    }
    try:
        response = requests.get(PUBMED_ESEARCH_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise PubMedError(f"esearch request failed: {exc}") from exc
    payload = response.json()
    try:
        return list(payload["esearchresult"]["idlist"])
    except (KeyError, TypeError) as exc:
        raise PubMedError(f"Unexpected esearch response shape: {payload!r}") from exc


def fetch_articles(pmids: list[str]) -> list[dict[str, Any]]:
    """Fetch full article metadata (title/authors/journal/date/abstract) for the given PMIDs."""
    if not pmids:
        return []
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "abstract",
        "retmode": "xml",
    }
    try:
        response = requests.get(PUBMED_EFETCH_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise PubMedError(f"efetch request failed: {exc}") from exc
    return parse_efetch_xml(response.text)


def parse_efetch_xml(xml_text: str) -> list[dict[str, Any]]:
    """Parse a PubMed efetch XML payload into a list of article dicts."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise PubMedError(f"Malformed efetch XML: {exc}") from exc

    articles: list[dict[str, Any]] = []
    for article_el in root.findall(".//PubmedArticle"):
        pmid_el = article_el.find(".//MedlineCitation/PMID")
        if pmid_el is None or not (pmid_el.text or "").strip():
            continue
        pmid = pmid_el.text.strip()

        title_el = article_el.find(".//Article/ArticleTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else "(untitled)"

        abstract_parts = [
            "".join(node.itertext()).strip()
            for node in article_el.findall(".//Article/Abstract/AbstractText")
        ]
        abstract = " ".join(part for part in abstract_parts if part)

        authors = _parse_authors(article_el)
        journal = _parse_journal(article_el)
        pub_date = _parse_pub_date(article_el)

        articles.append(
            {
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "journal": journal,
                "pub_date": pub_date,
                "abstract": abstract,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
        )
    return articles


def _parse_authors(article_el: ET.Element) -> str:
    names = []
    for author_el in article_el.findall(".//Article/AuthorList/Author"):
        last_name = author_el.findtext("LastName")
        initials = author_el.findtext("Initials")
        collective = author_el.findtext("CollectiveName")
        if last_name and initials:
            names.append(f"{last_name} {initials}")
        elif last_name:
            names.append(last_name)
        elif collective:
            names.append(collective)
    if not names:
        return "Unknown"
    if len(names) > 3:
        return ", ".join(names[:3]) + " et al."
    return ", ".join(names)


def _parse_journal(article_el: ET.Element) -> str:
    return (
        article_el.findtext(".//Article/Journal/ISOAbbreviation")
        or article_el.findtext(".//Article/Journal/Title")
        or "Unknown journal"
    )


def _parse_pub_date(article_el: ET.Element) -> str:
    pub_date_el = article_el.find(".//Article/Journal/JournalIssue/PubDate")
    if pub_date_el is None:
        return "Unknown date"
    medline_date = pub_date_el.findtext("MedlineDate")
    if medline_date:
        return medline_date
    year = pub_date_el.findtext("Year") or ""
    month = pub_date_el.findtext("Month") or ""
    day = pub_date_el.findtext("Day") or ""
    parts = [p for p in (year, month, day) if p]
    return " ".join(parts) if parts else "Unknown date"
