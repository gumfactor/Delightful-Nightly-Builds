"""Novelty scoring: how much a candidate analogy repeats a triple that has
already been generated, and how much its text overlaps with everything
already stored in the library.
"""

from __future__ import annotations

import re
from typing import Iterable

_WORD_RE = re.compile(r"[a-z0-9']+")


def tokenize(text: str) -> set:
    return set(_WORD_RE.findall(text.lower()))


def jaccard_similarity(text_a: str, text_b: str) -> float:
    """1.0 for identical token sets, 0.0 for disjoint sets, 0.0 if both empty."""
    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def max_overlap(text: str, existing_texts: Iterable[str]) -> float:
    """The highest Jaccard similarity between `text` and any text in `existing_texts`.
    Returns 0.0 if `existing_texts` is empty."""
    best = 0.0
    for existing in existing_texts:
        score = jaccard_similarity(text, existing)
        if score > best:
            best = score
    return best


def novelty_score(usage_count: int, overlap: float) -> float:
    """Combines how many times this exact (concept, domain, audience) triple
    has already been generated with how much the new text overlaps existing
    library text. 1.0 is maximally novel; scores fall toward 0.0 as either
    the triple repeats or the phrasing echoes prior entries."""
    if usage_count < 0:
        raise ValueError("usage_count must be >= 0")
    if not 0.0 <= overlap <= 1.0:
        raise ValueError("overlap must be between 0.0 and 1.0")
    repeat_penalty = 1.0 / (1 + usage_count)
    return round(repeat_penalty * (1.0 - overlap), 4)


def rank_triples_by_usage(triples: list, usage_counts: dict) -> list:
    """Sort (concept, domain, audience) triples ascending by how many times
    they have already been generated, so under-explored triples surface first.
    Stable sort preserves the incoming order among ties."""

    def usage_key(triple):
        concept, domain, audience = triple
        return usage_counts.get((concept.id, domain.id, audience), 0)

    return sorted(triples, key=usage_key)
