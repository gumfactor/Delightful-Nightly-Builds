"""Reconciles Teamwork tasks against Coda rows by title similarity.

Pure logic, no I/O: takes normalized item dicts in, returns bucketed
match results out. Kept dependency-free so it can be hand-verified and
unit tested in isolation from either HTTP client.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

Bucket = Literal["matched_ok", "status_conflict", "teamwork_only", "coda_only"]

_TOKEN_RE = re.compile(r"[a-z0-9]+")

DEFAULT_THRESHOLD = 0.5


def normalize_title(title: str) -> frozenset[str]:
    """Casefold, strip punctuation, and tokenize a title into a word set."""
    return frozenset(_TOKEN_RE.findall(title.casefold()))


def jaccard_similarity(a: frozenset[str], b: frozenset[str]) -> float:
    """Jaccard index of two token sets. Two empty sets are defined as 0.0 similarity."""
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union


@dataclass
class MatchResult:
    bucket: Bucket
    teamwork_item: dict | None = None
    coda_item: dict | None = None
    similarity: float | None = None
    detail: str = ""


def _status_conflict_detail(teamwork_item: dict, coda_item: dict) -> str | None:
    tw_done = bool(teamwork_item["completed"])
    coda_done = bool(coda_item["is_done"])
    if tw_done == coda_done:
        return None
    if tw_done and not coda_done:
        return "done in Teamwork, still open in Coda"
    return "done in Coda, still open in Teamwork"


def reconcile(
    teamwork_items: list[dict],
    coda_items: list[dict],
    threshold: float = DEFAULT_THRESHOLD,
) -> list[MatchResult]:
    """Greedily match Teamwork/Coda items by title similarity and bucket every item.

    Each Teamwork item and each Coda item is used in at most one match. Candidate
    pairs are considered in descending similarity order so the strongest matches
    are claimed first; anything left over at or below `threshold` never matches.
    """
    tw_tokens = [normalize_title(item["title"]) for item in teamwork_items]
    coda_tokens = [normalize_title(item["title"]) for item in coda_items]

    candidates: list[tuple[float, int, int]] = []
    for i, tw_tok in enumerate(tw_tokens):
        for j, coda_tok in enumerate(coda_tokens):
            sim = jaccard_similarity(tw_tok, coda_tok)
            if sim > threshold:
                candidates.append((sim, i, j))

    candidates.sort(key=lambda c: c[0], reverse=True)

    matched_tw: set[int] = set()
    matched_coda: set[int] = set()
    results: list[MatchResult] = []

    for sim, i, j in candidates:
        if i in matched_tw or j in matched_coda:
            continue
        matched_tw.add(i)
        matched_coda.add(j)
        tw_item = teamwork_items[i]
        coda_item = coda_items[j]
        conflict_detail = _status_conflict_detail(tw_item, coda_item)
        if conflict_detail is None:
            results.append(MatchResult("matched_ok", tw_item, coda_item, sim))
        else:
            results.append(MatchResult("status_conflict", tw_item, coda_item, sim, conflict_detail))

    for i, tw_item in enumerate(teamwork_items):
        if i not in matched_tw:
            results.append(MatchResult("teamwork_only", teamwork_item=tw_item))

    for j, coda_item in enumerate(coda_items):
        if j not in matched_coda:
            results.append(MatchResult("coda_only", coda_item=coda_item))

    return results


def summarize(results: list[MatchResult]) -> dict[str, int]:
    """Count results per bucket, always including all four buckets (zero if absent)."""
    counts = {"matched_ok": 0, "status_conflict": 0, "teamwork_only": 0, "coda_only": 0}
    for r in results:
        counts[r.bucket] += 1
    return counts
