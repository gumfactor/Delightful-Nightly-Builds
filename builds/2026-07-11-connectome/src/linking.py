"""Note-to-note link scoring by rarity-weighted shared concepts."""

from __future__ import annotations

from itertools import combinations
from typing import NamedTuple


class Link(NamedTuple):
    note_a: int
    note_b: int
    score: float
    shared_concepts: list[str]


def score_pair(
    concepts_a: dict[str, float],
    concepts_b: dict[str, float],
    doc_freq: dict[str, int],
    total_notes: int,
) -> tuple[float, list[str]]:
    """Score how related two notes are by their shared concepts.

    Each shared concept contributes 1 / doc_freq (rarer concepts score more
    than common ones shared by nearly every note). Returns (score, shared
    concept terms sorted by contribution descending).
    """
    shared = set(concepts_a) & set(concepts_b)
    if not shared:
        return 0.0, []

    contributions = []
    for term in shared:
        df = max(doc_freq.get(term, total_notes), 1)
        contributions.append((term, 1.0 / df))
    contributions.sort(key=lambda pair: pair[1], reverse=True)
    score = sum(weight for _, weight in contributions)
    return score, [term for term, _ in contributions]


def compute_links(
    note_concepts: dict[int, dict[str, float]],
    doc_freq: dict[str, int],
    total_notes: int,
    min_score: float = 1e-9,
) -> list[Link]:
    """Compute all pairwise links above min_score, canonically ordered (a < b)."""
    links = []
    note_ids = sorted(note_concepts.keys())
    for note_a, note_b in combinations(note_ids, 2):
        score, shared = score_pair(
            note_concepts[note_a], note_concepts[note_b], doc_freq, total_notes
        )
        if score > min_score:
            links.append(Link(note_a, note_b, score, shared))
    links.sort(key=lambda link: link.score, reverse=True)
    return links


def related_to(note_id: int, links: list[Link], top_n: int = 5) -> list[Link]:
    """Return the top links touching note_id, oriented so note_a == note_id."""
    touching = []
    for link in links:
        if link.note_a == note_id:
            touching.append(link)
        elif link.note_b == note_id:
            touching.append(Link(link.note_b, link.note_a, link.score, link.shared_concepts))
    touching.sort(key=lambda link: link.score, reverse=True)
    return touching[:top_n]
