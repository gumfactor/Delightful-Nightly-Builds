"""Headline formula bank and novelty-driven headline selection."""

from __future__ import annotations

import novelty

FORMULA_BANK = {
    "spotlight": {
        "general": [
            "Meet {name}: {category} Done the Canadian Way",
            "{name} Is the {category} Brand You Should Know",
            "Why {name} Belongs on Your Radar",
        ],
        "holiday": [
            "{name}: Your Canadian {category} Gift Idea This Season",
            "Give Canadian This Year — Start With {name}",
        ],
        "canada-day": [
            "{name}: A Canada Day Spotlight on {category}",
            "This Canada Day, Meet {name}",
        ],
        "back-to-school": [
            "{name}: A Canadian {category} Pick for Back-to-School",
        ],
    },
    "gift_guide": {
        "general": [
            "{count} Canadian-Made {category} Worth Adding to Your Cart",
            "Skip the Import: {count} Canadian {category} Brands to Know",
            "Your Canadian {category} Shortlist",
        ],
        "holiday": [
            "{count} Canadian {category} Gifts for Everyone on Your List",
            "A Canadian-Made {category} Gift Guide for the Holidays",
        ],
        "canada-day": [
            "{count} Canadian {category} Picks to Celebrate Canada Day",
        ],
        "back-to-school": [
            "{count} Canadian {category} Essentials for Back-to-School",
        ],
    },
    "swap_it": {
        "general": [
            "Next Time You Reach for {category}, Try Canadian Instead",
            "{count} Canadian Swaps for Your Usual {category}",
        ],
        "holiday": [
            "Swap It Canadian: {count} {category} Alternatives for the Holidays",
        ],
        "canada-day": [
            "Your Canada Day {category} Swap List",
        ],
        "back-to-school": [
            "Back-to-School {category}? Make the Canadian Swap",
        ],
    },
    "local_spotlight": {
        "general": [
            "{count} Canadian Businesses to Know in {province}",
            "{province}'s Canadian-Owned Small Business Scene",
        ],
        "holiday": [
            "{count} {province} Businesses for Local Holiday Shopping",
        ],
        "canada-day": [
            "Celebrate Canada Day Local: {count} {province} Businesses",
        ],
        "back-to-school": [
            "{count} {province} Businesses for Back-to-School Shopping",
        ],
    },
}


def select_headline(
    piece_type: str,
    occasion: str,
    context: dict,
    body_text: str,
    history_full_texts: list[str],
) -> tuple[str, float]:
    """Pick the least-overlapping headline formula against generation history.

    Renders every formula for this (piece_type, occasion), scores each
    candidate's full text (headline + body) against every previously
    generated piece of the same piece_type, and returns the formula with the
    lowest max overlap. Ties (including the no-history case, where every
    candidate scores 0.0) resolve to the first formula in bank order, so a
    single generation with no history is fully deterministic.
    """
    piece_formulas = FORMULA_BANK.get(piece_type)
    if piece_formulas is None:
        raise ValueError(f"Unknown piece type: {piece_type!r}")
    formulas = piece_formulas.get(occasion)
    if not formulas:
        raise ValueError(f"No headline formulas for occasion {occasion!r}")

    best_headline = None
    best_overlap = None
    for formula in formulas:
        headline = formula.format(**context)
        full_text = f"{headline}\n\n{body_text}"
        overlap = novelty.max_overlap_against_history(full_text, history_full_texts)
        if best_overlap is None or overlap < best_overlap:
            best_overlap = overlap
            best_headline = headline

    return best_headline, best_overlap
