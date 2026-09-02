"""Core reference data model shared by every input source and output style."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

VALID_REF_TYPES = {"journal-article", "book", "webpage", "other"}


@dataclass
class Author:
    family: str
    given: str = ""

    def to_dict(self) -> dict:
        return {"family": self.family, "given": self.given}

    @staticmethod
    def from_dict(data: dict) -> "Author":
        return Author(family=data.get("family", ""), given=data.get("given", ""))


@dataclass
class Reference:
    ref_type: str
    authors: list[Author]
    year: str
    title: str
    container_title: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    url: str = ""
    source: str = "manual"
    needs_review: bool = False
    ref_id: int | None = field(default=None)

    def __post_init__(self) -> None:
        if self.ref_type not in VALID_REF_TYPES:
            self.ref_type = "other"

    def dedupe_key(self) -> str:
        if self.doi:
            return f"doi:{normalize_doi(self.doi)}"
        first_family = self.authors[0].family if self.authors else ""
        return "fyt:" + "|".join(
            _normalize_key_part(part) for part in (first_family, self.year, self.title)
        )


def _normalize_key_part(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def normalize_doi(doi: str) -> str:
    doi = doi.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    return doi.strip().lower()
