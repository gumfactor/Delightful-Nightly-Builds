"""Deterministic per-submission checks: word count, section detection,
citation counting, keyword-coverage scoring, and an informational
Flesch Reading Ease estimate. Every function is pure and independently
testable — no network, no filesystem access.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rubric import Rubric

_WORD_RE = re.compile(r"[A-Za-z']+")
_SENTENCE_END_RE = re.compile(r"[.!?]+")
_VOWEL_GROUP_RE = re.compile(r"[aeiouyAEIOUY]+")

_HEADING_RE_TEMPLATE = r"^\s{{0,3}}#{{0,6}}\s*{name}\s*:?\s*$"

_AUTHOR_YEAR_CITATION_RE = re.compile(
    r"\([A-Z][A-Za-z\-']+(?:,?\s*(?:&|and)\s*[A-Z][A-Za-z\-']+|\set al\.)?,?\s*\d{4}[a-z]?\)"
)
_NUMBERED_CITATION_RE = re.compile(r"\[\d+(?:[,\-]\s*\d+)*\]")


def count_words(text: str) -> int:
    return len(_WORD_RE.findall(text))


def find_sections(text: str, required_sections: list[str]) -> dict[str, bool]:
    """Case-insensitive detection of a section heading on its own line,
    optionally prefixed with 1-6 Markdown '#' characters and optionally
    suffixed with a colon (e.g. 'Introduction', '## Discussion', 'CONCLUSION:').
    """
    lines = text.splitlines()
    result: dict[str, bool] = {}
    for section in required_sections:
        pattern = re.compile(_HEADING_RE_TEMPLATE.format(name=re.escape(section)), re.IGNORECASE)
        result[section] = any(pattern.match(line) for line in lines)
    return result


def count_citations(text: str) -> int:
    author_year = _AUTHOR_YEAR_CITATION_RE.findall(text)
    numbered = _NUMBERED_CITATION_RE.findall(text)
    return len(author_year) + len(numbered)


def keyword_hits(text: str, keywords: list[str]) -> dict[str, int]:
    lower_words = _WORD_RE.findall(text.lower())
    counts: dict[str, int] = {}
    for kw in keywords:
        kw_lower = kw.lower()
        counts[kw] = sum(1 for w in lower_words if w == kw_lower)
    return counts


def keyword_coverage_score(
    text: str, keywords: list[str], min_hits: int, max_points: float
) -> tuple[float, int]:
    """Deterministic partial-credit scoring: total keyword hits scaled linearly
    against min_hits, capped at max_points. Returns (score, total_hits)."""
    if min_hits <= 0:
        raise ValueError("min_hits must be positive for a scored criterion")
    hits = keyword_hits(text, keywords)
    total_hits = sum(hits.values())
    fraction = min(total_hits / min_hits, 1.0)
    score = round(max_points * fraction, 2)
    return score, total_hits


def _count_syllables(word: str) -> int:
    groups = _VOWEL_GROUP_RE.findall(word.lower())
    count = len(groups)
    if word.lower().endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def flesch_reading_ease(text: str) -> float | None:
    words = _WORD_RE.findall(text)
    sentences = [s for s in _SENTENCE_END_RE.split(text) if s.strip()]
    if not words or not sentences:
        return None
    syllables = sum(_count_syllables(w) for w in words)
    words_per_sentence = len(words) / len(sentences)
    syllables_per_word = syllables / len(words)
    score = 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word
    return round(score, 1)


@dataclass
class ComplianceResult:
    word_count: int
    word_count_ok: bool
    sections_found: dict[str, bool]
    sections_ok: bool
    citation_count: int
    citations_ok: bool
    flesch_score: float | None


def check_compliance(text: str, rubric: "Rubric") -> ComplianceResult:
    word_count = count_words(text)
    word_count_ok = True
    if rubric.min_words is not None and word_count < rubric.min_words:
        word_count_ok = False
    if rubric.max_words is not None and word_count > rubric.max_words:
        word_count_ok = False

    sections_found = find_sections(text, rubric.required_sections)
    sections_ok = all(sections_found.values())

    citation_count = count_citations(text)
    citations_ok = citation_count >= rubric.min_citations

    return ComplianceResult(
        word_count=word_count,
        word_count_ok=word_count_ok,
        sections_found=sections_found,
        sections_ok=sections_ok,
        citation_count=citation_count,
        citations_ok=citations_ok,
        flesch_score=flesch_reading_ease(text),
    )
