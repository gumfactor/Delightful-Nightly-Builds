"""Piece types, tones, occasions, and the compatibility/eligibility rule engine."""

from __future__ import annotations

PIECE_TYPES = ["spotlight", "gift_guide", "swap_it", "local_spotlight"]
TONES = ["consumer", "editorial", "social"]
OCCASIONS = ["general", "holiday", "canada-day", "back-to-school"]

# Only these piece types are short-form enough for a 'social' tone.
SHORT_FORM_PIECE_TYPES = {"spotlight", "gift_guide"}

MIN_BUSINESSES = {
    "spotlight": 1,
    "gift_guide": 3,
    "swap_it": 2,
    "local_spotlight": 2,
}

GROUPING_LABEL = {
    "spotlight": "selected business",
    "gift_guide": "category",
    "swap_it": "category",
    "local_spotlight": "province",
}


def check_eligibility(piece_type: str, businesses: list[dict]) -> None:
    """Raise ValueError with a clear, specific message if the business set
    doesn't meet the piece type's minimum requirements."""
    if piece_type not in PIECE_TYPES:
        raise ValueError(f"Unknown piece type: {piece_type!r}")

    minimum = MIN_BUSINESSES[piece_type]
    found = len(businesses)
    if found < minimum:
        label = GROUPING_LABEL[piece_type]
        raise ValueError(
            f"'{piece_type}' requires at least {minimum} business(es) in the same "
            f"{label}; found {found}."
        )
    if piece_type == "spotlight" and found > 1:
        raise ValueError(
            f"'spotlight' expects exactly 1 business; found {found}. "
            "Narrow the selection with --business."
        )


def check_tone_compatibility(piece_type: str, tone: str) -> None:
    """Raise ValueError if the piece type / tone combination is not allowed."""
    if piece_type not in PIECE_TYPES:
        raise ValueError(f"Unknown piece type: {piece_type!r}")
    if tone not in TONES:
        raise ValueError(f"Unknown tone: {tone!r}")
    if tone == "social" and piece_type not in SHORT_FORM_PIECE_TYPES:
        raise ValueError(
            f"'social' tone is not valid for '{piece_type}' — social pieces must "
            "stay short-form (spotlight or gift_guide). Use 'consumer' or 'editorial' "
            f"for '{piece_type}'."
        )


def check_occasion(occasion: str) -> None:
    if occasion not in OCCASIONS:
        raise ValueError(
            f"Unknown occasion: {occasion!r}. Choose from: {', '.join(OCCASIONS)}"
        )
