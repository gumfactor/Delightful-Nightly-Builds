"""Pure, deterministic analysis functions: overlap, gap scoring, term diff.

None of these touch the network or the database directly — they operate on
plain dicts/objects so they can be unit tested with hand-built fixtures.
"""

from __future__ import annotations

import re
from collections import defaultdict

DEFAULT_GAP_THRESHOLD = 0.15

_STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "on", "at", "by", "for", "with",
    "and", "or", "but", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as", "from", "into",
    "over", "under", "after", "before", "between", "during", "without",
    "within", "about",
}


def tokenize(text: str) -> set:
    """Lowercase, strip punctuation, drop stopwords and 1-char tokens."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = text.split()
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def find_gaps(objectives, concepts, threshold: float = DEFAULT_GAP_THRESHOLD) -> list:
    """For each objective, find its best-matching concept by Jaccard overlap.

    ``objectives`` and ``concepts`` are iterables of objects/dicts exposing
    ``.text``/["text"] and ``.display_name``/["display_name"] respectively.
    Returns a list of dicts, one per objective, in input order.
    """
    concept_tokens = []
    for c in concepts:
        name = c["display_name"] if isinstance(c, dict) else c.display_name
        concept_tokens.append((name, tokenize(name)))

    results = []
    for obj in objectives:
        text = obj["text"] if isinstance(obj, dict) else obj.text
        obj_tokens = tokenize(text)
        best_name = None
        best_score = 0.0
        for name, tokens in concept_tokens:
            score = jaccard(obj_tokens, tokens)
            if score > best_score:
                best_score = score
                best_name = name
        results.append({
            "objective_text": text,
            "best_concept": best_name,
            "best_score": round(best_score, 4),
            "flagged": best_score < threshold,
        })
    return results


def find_overlap(concept_rows: list) -> list:
    """Group concept rows (as returned by store.list_concepts) by normalized
    name and return those present in more than one distinct course."""
    groups = defaultdict(list)
    for row in concept_rows:
        groups[row["normalized_name"]].append(row)

    results = []
    for norm, rows in groups.items():
        course_ids = {r["course_id"] for r in rows}
        if len(course_ids) <= 1:
            continue
        display_name = rows[0]["display_name"]
        locations = sorted({
            (r["course_name"], r["term"], r["source_path"]) for r in rows
        })
        results.append({
            "normalized_name": norm,
            "display_name": display_name,
            "course_count": len(course_ids),
            "locations": [
                {"course_name": c, "term": t, "source_path": p}
                for c, t, p in locations
            ],
        })
    results.sort(key=lambda r: (-r["course_count"], r["normalized_name"]))
    return results


def diff_terms(concepts_a: list, concepts_b: list) -> dict:
    """Compare two concept sets (e.g. same course, two different terms)."""
    names_a = {c["normalized_name"]: c["display_name"] for c in concepts_a}
    names_b = {c["normalized_name"]: c["display_name"] for c in concepts_b}
    set_a, set_b = set(names_a), set(names_b)

    added = sorted(names_b[n] for n in (set_b - set_a))
    removed = sorted(names_a[n] for n in (set_a - set_b))
    kept = sorted(names_a[n] for n in (set_a & set_b))
    return {"added": added, "removed": removed, "kept": kept}
