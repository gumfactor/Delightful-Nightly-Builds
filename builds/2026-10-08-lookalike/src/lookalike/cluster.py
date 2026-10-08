"""Clustering, human decisions, weak-chain guard and field-level survivorship merge."""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

from .match import PairResult, REVIEW_MIN, find_pairs, score_pair
from .schema import CANONICAL, Record

MAX_CLUSTER_AUDIT = 30
UNION_FIELDS = {"category"}


class DecisionsError(ValueError):
    pass


@dataclass
class Decisions:
    same: set[frozenset[str]] = field(default_factory=set)
    different: set[frozenset[str]] = field(default_factory=set)

    def to_json(self) -> dict[str, list[list[str]]]:
        return {"same": sorted(sorted(p) for p in self.same), "different": sorted(sorted(p) for p in self.different)}


def load_decisions(path: Path | None) -> Decisions:
    if path is None:
        return Decisions()
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DecisionsError(f"cannot read decisions file {path}: {exc}") from exc
    return parse_decisions(raw)


def parse_decisions(raw: object) -> Decisions:
    if not isinstance(raw, dict):
        raise DecisionsError("decisions must be an object with 'same' and 'different' lists")
    result = Decisions()
    for key, bucket in (("same", result.same), ("different", result.different)):
        for pair in raw.get(key, []) or []:
            if not (isinstance(pair, list) and len(pair) == 2 and all(isinstance(x, (str, int)) for x in pair)):
                raise DecisionsError(f"each '{key}' entry must be a [id, id] pair")
            first, second = str(pair[0]), str(pair[1])
            if first == second:
                raise DecisionsError(f"'{key}' pair {first!r} repeats the same id")
            bucket.add(frozenset((first, second)))
    clash = result.same & result.different
    if clash:
        raise DecisionsError("pair marked both same and different: " + ", ".join(sorted("/".join(sorted(p)) for p in clash)))
    return result


class UnionFind:
    def __init__(self, items: list[str]) -> None:
        self.parent = {item: item for item in items}

    def find(self, item: str) -> str:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self.parent[max(root_a, root_b)] = min(root_a, root_b)


@dataclass
class Cluster:
    id: str
    members: list[str]
    status: str                       # merged | needs_review
    flags: list[str] = field(default_factory=list)
    merged: dict[str, str] = field(default_factory=dict)
    provenance: dict[str, str] = field(default_factory=dict)
    representative: str = ""
    pair_ids: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Analysis:
    records: list[Record]
    pairs: list[PairResult]           # all non-distinct pairs after decisions
    clusters: list[Cluster]
    review_pairs: list[PairResult]
    branch_pairs: list[PairResult]
    decisions: Decisions

    @property
    def by_id(self) -> dict[str, Record]:
        return {r.id: r for r in self.records}


def analyze(records: list[Record], decisions: Decisions | None = None) -> Analysis:
    decisions = decisions or Decisions()
    by_id = {r.id: r for r in records}
    pairs = []
    for pair in find_pairs(records):
        key = frozenset((pair.a, pair.b))
        if key in decisions.different:
            continue
        if key in decisions.same:
            pair = PairResult(pair.a, pair.b, 1.0, "duplicate", [("human decision: same", 1.0)] + pair.reasons, pair.name_sim)
        pairs.append(pair)
    known = {frozenset((p.a, p.b)) for p in pairs}
    for key in sorted(decisions.same - known, key=sorted):
        first, second = sorted(key)
        if first in by_id and second in by_id:
            pairs.append(PairResult(first, second, 1.0, "duplicate", [("human decision: same", 1.0)]))
    union = UnionFind([r.id for r in records])
    for pair in pairs:
        if pair.label == "duplicate":
            union.union(pair.a, pair.b)
    groups: dict[str, list[str]] = {}
    for rec in records:
        groups.setdefault(union.find(rec.id), []).append(rec.id)
    clusters: list[Cluster] = []
    for root, members in sorted(groups.items()):
        if len(members) < 2:
            continue
        flags = _audit(members, by_id, decisions)
        cluster = Cluster(id=f"c{len(clusters) + 1:03d}", members=members,
                          status="needs_review" if flags else "merged", flags=flags,
                          pair_ids=[(p.a, p.b) for p in pairs if p.label == "duplicate" and p.a in members])
        if not flags:
            cluster.merged, cluster.provenance, cluster.representative = merge_records([by_id[m] for m in members])
        clusters.append(cluster)
    in_cluster = {m for c in clusters for m in c.members}
    review = [p for p in pairs if p.label == "review" and not (p.a in in_cluster and p.b in in_cluster
                                                                 and union.find(p.a) == union.find(p.b))]
    branches = [p for p in pairs if p.label == "branch"]
    return Analysis(records, pairs, clusters, review, branches, decisions)


def _audit(members: list[str], by_id: dict[str, Record], decisions: Decisions) -> list[str]:
    """Flags that stop an automatic merge: transitive chains and contradicted human decisions."""
    flags: list[str] = []
    for pair in combinations(sorted(members), 2):
        key = frozenset(pair)
        if key in decisions.different:
            flags.append(f"decision_conflict: {pair[0]} and {pair[1]} were marked different but link through other rows")
    if len(members) > MAX_CLUSTER_AUDIT:
        flags.append(f"large_cluster: {len(members)} rows")
        return flags
    for first, second in combinations(sorted(members), 2):
        key = frozenset((first, second))
        if key in decisions.same:
            continue
        result = score_pair(by_id[first], by_id[second])
        if result.label == "branch" or result.score < REVIEW_MIN:
            flags.append(f"weak_chain: {first} and {second} are linked only through other rows "
                         f"(direct score {result.score:.2f}, {result.label})")
    return flags


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _split_values(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[;|,]", value) if part.strip()]


def merge_records(rows: list[Record]) -> tuple[dict[str, str], dict[str, str], str]:
    """Field-level survivorship. Returns (merged fields, provenance field->row id, representative id)."""
    merged: dict[str, str] = {}
    provenance: dict[str, str] = {}
    ordered = sorted(rows, key=lambda r: (-sum(1 for v in r.fields.values() if v), r.id))
    for name in CANONICAL:
        candidates = [(r.fields.get(name, ""), r) for r in ordered if r.fields.get(name, "")]
        if not candidates:
            continue
        if name in UNION_FIELDS:
            seen: dict[str, str] = {}
            for value, row in candidates:
                for part in _split_values(value):
                    seen.setdefault(_norm(part), part)
            merged[name] = "; ".join(seen.values())
            provenance[name] = "union"
            continue
        counts = Counter(_norm(value) for value, _ in candidates)
        if name == "updated_at":
            best = max(candidates, key=lambda c: c[0])
        else:
            best = max(enumerate(candidates), key=lambda ic: (counts[_norm(ic[1][0])], len(ic[1][0]), -ic[0]))[1]
        merged[name] = best[0]
        provenance[name] = best[1].id
    return merged, provenance, ordered[0].id
