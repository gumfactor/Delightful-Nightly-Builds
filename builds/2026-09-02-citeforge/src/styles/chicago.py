"""Chicago Author-Date 17th Edition reference-list and in-text formatting.

Known simplification (documented in Manual.md): place-of-publication and
month-of-publication are not tracked in the reference model, so both are
omitted rather than fabricated.
"""

from __future__ import annotations

from ..models import Reference, normalize_doi
from ..names import format_authors_chicago
from ..pages import format_pages_full
from ..text_case import to_title_case


def format_reference(ref: Reference) -> str:
    authors = format_authors_chicago(ref.authors)
    year = ref.year or "n.d."
    author_year = f"{authors}. {year}." if authors else f"{year}."
    title = to_title_case(ref.title)

    if ref.ref_type == "journal-article":
        journal = to_title_case(ref.container_title)
        vol_part = ref.volume
        if ref.volume and ref.issue:
            vol_part += f", no. {ref.issue}"
        pages = format_pages_full(ref.pages)
        tail = f"*{journal}*" if journal else ""
        if vol_part:
            tail += f" {vol_part}" if tail else vol_part
        if pages:
            tail += f": {pages}" if tail else pages
        body = f'"{title}." {tail}.'.strip() if tail else f'"{title}."'
    elif ref.ref_type == "book":
        body = f"*{title}*."
        if ref.container_title:
            body += f" {ref.container_title}."
    elif ref.ref_type == "webpage":
        body = f'"{title}."'
        if ref.container_title:
            body += f" *{ref.container_title}*."
    else:
        body = f'"{title}."'
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
        return f"(Unknown {year})"
    if n <= 3:
        names = " and ".join(a.family for a in ref.authors)
        return f"({names} {year})"
    return f"({ref.authors[0].family} et al. {year})"
