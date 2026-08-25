"""Deterministic reusability scoring for grant text chunks.

The score answers one question: "how safely can this paragraph be dropped
into a *different* future grant with little or no editing?" It rewards a
usable length and generic/transferable language, and penalizes language
anchored to one specific proposal (dollar figures, calendar years, and
named-entity-like phrases such as a collaborator or institution name).
"""

import re

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_DOLLAR_RE = re.compile(r"\$\s?[\d,]+(?:\.\d+)?")
_NAME_LIKE_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b")

_GENERIC_KEYWORDS = [
    "framework", "broadly applicable", "generalizable", "across settings",
    "translational", "community", "widely applicable",
]

HIGH_TIER = "High"
MEDIUM_TIER = "Medium"
LOW_TIER = "Low"


def _length_adjustment(word_count: int) -> int:
    if 40 <= word_count <= 250:
        return 2
    if word_count < 15:
        return -2
    if word_count > 400:
        return -1
    return 0


def _specificity_adjustment(chunk: str) -> int:
    categories_present = sum(
        1
        for pattern in (_YEAR_RE, _DOLLAR_RE, _NAME_LIKE_RE)
        if pattern.search(chunk)
    )
    if categories_present >= 3:
        return -4
    if categories_present == 2:
        return -3
    if categories_present == 1:
        return -1
    return 0


def _generic_bonus(chunk: str) -> int:
    lowered = chunk.lower()
    return 1 if any(keyword in lowered for keyword in _GENERIC_KEYWORDS) else 0


def score_reusability(chunk: str) -> tuple[int, str]:
    """Return (score 0-10, tier) for a text chunk."""
    if not chunk or not chunk.strip():
        return 0, LOW_TIER

    word_count = len(chunk.split())
    raw_score = (
        5
        + _length_adjustment(word_count)
        + _specificity_adjustment(chunk)
        + _generic_bonus(chunk)
    )
    score = max(0, min(10, raw_score))

    if score >= 7:
        tier = HIGH_TIER
    elif score >= 4:
        tier = MEDIUM_TIER
    else:
        tier = LOW_TIER
    return score, tier
