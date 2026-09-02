"""Shared reference-list construction for AMA and Vancouver/ICMJE.

Both styles share the same overall shape (numbered in-text citations,
inverted "Family II" author names, sentence-case titles, unabbreviated
journal names as a documented simplification) and differ only in their
author-list et-al threshold, which is injected via `authors_fn`.
"""

from __future__ import annotations

from collections.abc import Callable

from ..models import Author, Reference, normalize_doi
from ..pages import format_pages_ama_vancouver
from ..text_case import to_sentence_case


def build_reference(ref: Reference, authors_fn: Callable[[list[Author]], str]) -> str:
    authors = authors_fn(ref.authors)
    title = to_sentence_case(ref.title)
    if not authors:
        author_segment = ""
    else:
        author_segment = authors if authors.endswith(".") else f"{authors}."

    if ref.ref_type == "journal-article":
        vol_issue = ref.volume
        if ref.volume and ref.issue:
            vol_issue += f"({ref.issue})"
        pages = format_pages_ama_vancouver(ref.pages)
        tail = f"{ref.year}"
        if vol_issue:
            tail += f";{vol_issue}"
        if pages:
            tail += f":{pages}"
        body = f"{ref.container_title}. {tail}." if ref.container_title else f"{tail}."
    elif ref.ref_type == "book":
        body = f"{ref.container_title}; {ref.year}." if ref.container_title else f"{ref.year}."
    elif ref.ref_type == "webpage":
        body = f"{ref.container_title}. {ref.year}." if ref.container_title else f"{ref.year}."
    else:
        body = f"{ref.container_title}. {ref.year}." if ref.container_title else f"{ref.year}."

    citation = " ".join(part for part in (author_segment, f"{title}.", body) if part)
    if ref.doi:
        citation += f" doi:{normalize_doi(ref.doi)}"
    elif ref.url:
        citation += f" {ref.url}"
    return citation


def format_in_text(index: int) -> str:
    return f"[{index}]"
