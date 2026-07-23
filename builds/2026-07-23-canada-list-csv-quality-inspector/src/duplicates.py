"""Exact and near-duplicate detection for Canada List directory rows."""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from urllib.parse import urlparse

from src.schema import normalize_business_name

NEAR_DUPLICATE_THRESHOLD = 0.85


@dataclass
class DuplicateCluster:
    cluster_id: int
    row_indices: list
    match_basis: str  # "exact_row" | "name+province" | "name+domain"
    similarity_score: float
    ai_confirmed: object = None  # True | False | None (None = not checked by AI)
    ai_reasoning: str = ""

    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "row_indices": self.row_indices,
            "match_basis": self.match_basis,
            "similarity_score": round(self.similarity_score, 3),
            "ai_confirmed": self.ai_confirmed,
            "ai_reasoning": self.ai_reasoning,
        }


def _find_column(header: list, target: str) -> str | None:
    target_lower = target.strip().lower()
    for col in header:
        if col.strip().lower() == target_lower:
            return col
    return None


def _domain_of(url: str) -> str:
    if not url:
        return ""
    candidate = url if "://" in url else f"https://{url}"
    netloc = urlparse(candidate).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


class _UnionFind:
    def __init__(self, items):
        self.parent = {item: item for item in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def find_exact_duplicate_clusters(row_records: list, header: list) -> list:
    """Group rows whose full field content is byte-for-byte identical."""
    seen: dict[tuple, list] = {}
    for record in row_records:
        key = tuple(record.raw_fields.get(col, "") for col in header)
        seen.setdefault(key, []).append(record.row_index)

    clusters: list[DuplicateCluster] = []
    cluster_id = 0
    for indices in seen.values():
        if len(indices) > 1:
            cluster_id += 1
            clusters.append(
                DuplicateCluster(
                    cluster_id=cluster_id,
                    row_indices=indices,
                    match_basis="exact_row",
                    similarity_score=1.0,
                )
            )
    return clusters


def find_near_duplicate_clusters(
    row_records: list,
    header: list,
    threshold: float = NEAR_DUPLICATE_THRESHOLD,
    already_clustered: set | None = None,
) -> list:
    """Cluster rows with similar business names corroborated by matching
    province or matching website domain. `already_clustered` row indices
    (e.g. already flagged as exact duplicates) are skipped to avoid
    double-reporting the same pair.
    """
    name_col = _find_column(header, "business_name")
    province_col = _find_column(header, "province")
    website_col = _find_column(header, "website")
    if name_col is None:
        return []

    already_clustered = already_clustered or set()
    candidates = [r for r in row_records if r.row_index not in already_clustered]

    normalized = {
        r.row_index: normalize_business_name(r.raw_fields.get(name_col, "") or "")
        for r in candidates
    }
    provinces = {
        r.row_index: (r.raw_fields.get(province_col, "") or "").strip().lower()
        for r in candidates
    } if province_col else {}
    domains = {
        r.row_index: _domain_of(r.raw_fields.get(website_col, "") or "")
        for r in candidates
    } if website_col else {}

    uf = _UnionFind([r.row_index for r in candidates])
    pair_scores: dict[tuple, float] = {}

    for i, r1 in enumerate(candidates):
        n1 = normalized[r1.row_index]
        if not n1:
            continue
        for r2 in candidates[i + 1:]:
            n2 = normalized[r2.row_index]
            if not n2:
                continue
            score = difflib.SequenceMatcher(None, n1, n2).ratio()
            if score < threshold:
                continue
            corroborated = False
            if province_col and provinces.get(r1.row_index) and provinces.get(r1.row_index) == provinces.get(r2.row_index):
                corroborated = True
                basis = "name+province"
            if website_col and domains.get(r1.row_index) and domains.get(r1.row_index) == domains.get(r2.row_index):
                corroborated = True
                basis = "name+domain"
            if not corroborated:
                continue
            uf.union(r1.row_index, r2.row_index)
            pair_scores[(r1.row_index, r2.row_index)] = score

    groups: dict[int, list] = {}
    for r in candidates:
        root = uf.find(r.row_index)
        groups.setdefault(root, []).append(r.row_index)

    clusters: list[DuplicateCluster] = []
    cluster_id = 1000  # offset so IDs never collide with exact-duplicate clusters
    for indices in groups.values():
        if len(indices) < 2:
            continue
        relevant_scores = [
            score
            for (a, b), score in pair_scores.items()
            if a in indices and b in indices
        ]
        avg_score = sum(relevant_scores) / len(relevant_scores) if relevant_scores else threshold
        cluster_id += 1
        clusters.append(
            DuplicateCluster(
                cluster_id=cluster_id,
                row_indices=sorted(indices),
                match_basis="name+province/domain",
                similarity_score=avg_score,
            )
        )
    return clusters


def find_all_duplicate_clusters(row_records: list, header: list) -> list:
    exact = find_exact_duplicate_clusters(row_records, header)
    exact_indices = {i for cluster in exact for i in cluster.row_indices}
    near = find_near_duplicate_clusters(row_records, header, already_clustered=exact_indices)
    return exact + near
