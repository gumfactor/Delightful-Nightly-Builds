"""Deterministic subcategory clustering, with an optional AI naming pass.

Subcategories are a second, cross-cutting axis on top of category (Notes /
Academic Papers / News Articles / ...): a group of notes that talk about the
same thing regardless of which category they belong to. Clustering is
connected components over the note-to-note links already computed by
linking.py — no separate concept graph is built, this just reuses what's
already there. Naming is always deterministic first (from each cluster's
own top aggregate concepts); an optional Claude pass can relabel names to
read better, and falls back to the deterministic name per-cluster on any
failure, never all-or-nothing.
"""

from __future__ import annotations

import json
import statistics
import urllib.error
import urllib.request
from typing import Optional

MAX_NAME_CONCEPTS = 3
UNCATEGORIZED = "Uncategorized"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"


def _cluster_threshold(links: list) -> float:
    """Median link score across the corpus. A rough heuristic (like this
    build's other top_n tuning) — notes linked at or above the corpus's
    typical strength cluster together, not a statistically principled cut."""
    scores = [link.score for link in links]
    if not scores:
        return 0.0
    return statistics.median(scores)


def compute_clusters(notes: list, links: list, threshold: Optional[float] = None) -> dict[int, int]:
    """Union-find over links scoring >= threshold. Returns note_id -> cluster root id.

    Every note gets an entry, including ones with no qualifying links — those
    end up as their own singleton cluster (root == their own id).
    """
    note_ids = [note["id"] for note in notes]
    if not note_ids:
        return {}
    if threshold is None:
        threshold = _cluster_threshold(links)

    parent = {note_id: note_id for note_id in note_ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for link in links:
        if link.score >= threshold and link.note_a in parent and link.note_b in parent:
            union(link.note_a, link.note_b)

    return {note_id: find(note_id) for note_id in note_ids}


def cluster_members(clusters: dict[int, int]) -> dict[int, list[int]]:
    """root id -> list of note ids in that cluster."""
    members: dict[int, list[int]] = {}
    for note_id, root in clusters.items():
        members.setdefault(root, []).append(note_id)
    return members


def cluster_top_terms(members: list[int], note_concepts: dict[int, dict[str, float]]) -> list[str]:
    """A cluster's most distinctive concepts: per-note weights summed across members."""
    totals: dict[str, float] = {}
    for note_id in members:
        for term, weight in note_concepts.get(note_id, {}).items():
            totals[term] = totals.get(term, 0.0) + weight
    ranked = sorted(totals.items(), key=lambda pair: pair[1], reverse=True)
    return [term for term, _ in ranked[:MAX_NAME_CONCEPTS]]


def name_clusters_deterministic(
    clusters: dict[int, int],
    note_concepts: dict[int, dict[str, float]],
) -> dict[int, str]:
    """root id -> deterministic name, built from the cluster's own top concepts."""
    names = {}
    for root, members in cluster_members(clusters).items():
        top_terms = cluster_top_terms(members, note_concepts)
        names[root] = " / ".join(term.title() for term in top_terms) if top_terms else UNCATEGORIZED
    return names


def relabel_with_claude(
    deterministic_names: dict[int, str],
    cluster_terms: dict[int, list[str]],
    api_key: Optional[str],
) -> dict[int, str]:
    """Ask Claude for a cleaner human-readable name per cluster in one batched call.

    Falls back to the deterministic name for any cluster whose id is missing
    from the response or whose returned name is empty; falls back for every
    cluster on total failure (no key, network error, bad status, malformed
    response) — never raises.
    """
    if not api_key or not cluster_terms:
        return dict(deterministic_names)

    payload_clusters = {str(root): terms for root, terms in cluster_terms.items() if terms}
    if not payload_clusters:
        return dict(deterministic_names)

    prompt = (
        "Here are concept clusters from a personal knowledge graph, each identified "
        "by an id, with their most representative keywords. For each cluster, respond "
        "with a short (2-4 word) human-readable category name that captures the theme. "
        "Respond with ONLY a JSON object mapping each id (as a string) to its name "
        "string, no prose, no markdown fences.\n\nClusters:\n" + json.dumps(payload_clusters)
    )
    body = json.dumps({
        "model": ANTHROPIC_MODEL,
        "max_tokens": 512,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            ANTHROPIC_API_URL,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status != 200:
                return dict(deterministic_names)
            raw = json.loads(response.read().decode("utf-8"))
            text = raw["content"][0]["text"].strip()
            relabeled = json.loads(text)
            if not isinstance(relabeled, dict):
                return dict(deterministic_names)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            KeyError, IndexError, ValueError, json.JSONDecodeError):
        return dict(deterministic_names)

    result = dict(deterministic_names)
    for root in deterministic_names:
        candidate = relabeled.get(str(root))
        if isinstance(candidate, str) and candidate.strip():
            result[root] = candidate.strip()
    return result


def assign_subcategories(
    notes: list,
    links: list,
    note_concepts: dict[int, dict[str, float]],
    api_key: Optional[str] = None,
) -> dict[int, str]:
    """Top-level orchestration: note_id -> final subcategory name.

    Always computes the deterministic clustering first; only calls out to
    Claude (and only ever improves, never degrades, a name) when api_key is set.
    """
    clusters = compute_clusters(notes, links)
    if not clusters:
        return {}
    names = name_clusters_deterministic(clusters, note_concepts)
    if api_key:
        terms_by_root = {
            root: cluster_top_terms(members, note_concepts)
            for root, members in cluster_members(clusters).items()
        }
        names = relabel_with_claude(names, terms_by_root, api_key)
    return {note_id: names[root] for note_id, root in clusters.items()}
