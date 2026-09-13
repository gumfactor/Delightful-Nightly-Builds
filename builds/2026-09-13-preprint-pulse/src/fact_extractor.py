"""Regex-based extraction of concrete reported statistics from abstracts.

Deliberately conservative: only matches the small set of conventional
notations researchers actually use in abstracts, each tagged with the
source paper and a short surrounding context snippet so every fact traces
back to something a reader could verify.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from arxiv_client import Paper

CONTEXT_RADIUS = 40  # characters of context on each side of a match

_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("sample_size", re.compile(r"\b[Nn]\s*=\s*\d{1,6}\b")),
    ("p_value", re.compile(r"\bp\s*[<>=]\s*\.?0?\.\d+\b")),
    ("correlation", re.compile(r"\br\s*=\s*-?0?\.\d+\b")),
    ("effect_size", re.compile(r"\b[dD]\s*=\s*-?\d?\.\d+\b")),
]


@dataclass
class Fact:
    arxiv_id: str
    paper_title: str
    fact_type: str
    raw_text: str
    context: str


def _context_snippet(text: str, start: int, end: int) -> str:
    lo = max(0, start - CONTEXT_RADIUS)
    hi = min(len(text), end + CONTEXT_RADIUS)
    snippet = text[lo:hi].strip()
    prefix = "…" if lo > 0 else ""
    suffix = "…" if hi < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


def extract_facts_from_text(text: str) -> list[tuple[str, str, str]]:
    """Return (fact_type, raw_text, context) tuples found in `text`."""
    results = []
    for fact_type, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(0)
            context = _context_snippet(text, match.start(), match.end())
            results.append((fact_type, raw, context))
    return results


def extract_facts(papers: list[Paper]) -> list[Fact]:
    """Extract facts from every paper's abstract, in paper order."""
    facts: list[Fact] = []
    for paper in papers:
        for fact_type, raw_text, context in extract_facts_from_text(paper.abstract):
            facts.append(
                Fact(
                    arxiv_id=paper.arxiv_id,
                    paper_title=paper.title,
                    fact_type=fact_type,
                    raw_text=raw_text,
                    context=context,
                )
            )
    return facts
