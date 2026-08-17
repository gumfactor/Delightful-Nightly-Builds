"""Jaccard token-overlap novelty scoring for generated editorial pieces."""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    """Lowercase word-token set for a piece of text."""
    return set(_TOKEN_RE.findall(text.lower()))


def jaccard_overlap(text_a: str, text_b: str) -> float:
    """Jaccard overlap of the token sets of two texts, in [0.0, 1.0].

    Two texts with no tokens in common (including two empty texts) score 0.0.
    """
    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)
    if not tokens_a and not tokens_b:
        return 0.0
    union = tokens_a | tokens_b
    if not union:
        return 0.0
    intersection = tokens_a & tokens_b
    return len(intersection) / len(union)


def max_overlap_against_history(candidate_text: str, history_texts: list[str]) -> float:
    """Highest Jaccard overlap between candidate_text and any text in history_texts.

    Returns 0.0 when history_texts is empty (nothing to overlap with yet).
    """
    if not history_texts:
        return 0.0
    return max(jaccard_overlap(candidate_text, past) for past in history_texts)
