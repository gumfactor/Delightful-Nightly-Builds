"""APA 7th Edition reference-list and in-text citation formatting."""

from __future__ import annotations

from ..models import Reference, normalize_doi
from ..names import format_authors_apa
from ..pages import format_pages_full
from ..text_case import to_sentence_case, to_title_case


def format_reference(ref: Reference) -> str:
    year = ref.year or "n.d."
    authors = format_authors_apa(ref.authors)
    author_year = f"{authors} ({year})." if authors else f"({year})."
    title = to_sentence_case(ref.title)

    if ref.ref_type == "journal-article":
        journal = to_title_case(ref.container_title)
        vol_issue = f"*{ref.volume}*" if ref.volume else ""
        if ref.volume and ref.issue:
            vol_issue += f"({ref.issue})"
        pages = format_pages_full(ref.pages)
        tail = f"*{journal}*" if journal else ""
        if vol_issue:
            tail += f", {vol_issue}" if tail else vol_issue
        if pages:
            tail += f", {pages}" if tail else pages
        body = f"{title}. {tail}.".strip() if tail else f"{title}."
    elif ref.ref_type == "book":
        body = f"*{title}*."
        if ref.container_title:
            body += f" {ref.container_title}."
    elif ref.ref_type == "webpage":
        body = f"{title}."
        if ref.container_title:
            body += f" *{ref.container_title}*."
    else:
        body = f"{title}."
        if ref.container_title:
            body += f" {ref.container_title}."

    citation = f"{author_year} {body}".strip()
    if ref.doi:
        citation += f" https://doi.org/{normalize_doi(ref.doi)}"
    elif ref.url:
        citation += f" {ref.url}"
    return citation


def format_in_text(ref: Reference, index: int) -> str:
    year = ref.year or "n.d."
    n = len(ref.authors)
    if n == 0:
        return f"(Unknown, {year})"
    if n == 1:
        return f"({ref.authors[0].family}, {year})"
    if n == 2:
        return f"({ref.authors[0].family} & {ref.authors[1].family}, {year})"
    return f"({ref.authors[0].family} et al., {year})"
