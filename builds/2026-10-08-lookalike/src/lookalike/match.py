"""Blocking, explainable pair scoring and labelling.

score = 1 - prod(1 - w_i) over positive evidence, minus conflict penalties, clamped to [0, 1].
Labels: duplicate (>= DUPLICATE_MIN), review (>= REVIEW_MIN), branch (same brand, different place), distinct.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations

from .schema import Record
from .similarity import name_similarity

DUPLICATE_MIN = 0.85
REVIEW_MIN = 0.55
MAX_BLOCK = 150

W_EMAIL = 0.55
W_DOMAIN = 0.50
W_PHONE = 0.45
W_ADDRESS = 0.40
W_POSTAL_STREET_NUM = 0.10


@dataclass
class PairResult:
    a: str
    b: str
    score: float
    label: str
    reasons: list[tuple[str, float]] = field(default_factory=list)
    name_sim: float = 0.0

    def explain(self) -> str:
        return "; ".join(f"{name} ({weight:+.2f})" for name, weight in self.reasons)


def block_keys(rec: Record) -> set[str]:
    keys: set[str] = set()
    if rec.domain:
        keys.add(f"dom:{rec.domain}")
    if rec.phone:
        keys.add(f"tel:{rec.phone}")
    if rec.email:
        keys.add(f"eml:{rec.email}")
    if rec.postal and rec.street:
        keys.add(f"adr:{rec.postal}:{rec.street.split(' ')[0]}")
    flat = rec.name_key.replace(" ", "")
    if len(flat) >= 4:
        keys.add(f"nam:{rec.province}:{flat[:5]}")
    if rec.name_tokens:
        keys.add(f"tok:{rec.province}:{sorted(rec.name_tokens)[0]}:{rec.city_key}")
    return keys


def candidate_pairs(records: list[Record]) -> set[tuple[int, int]]:
    blocks: dict[str, list[int]] = defaultdict(list)
    for index, rec in enumerate(records):
        for key in block_keys(rec):
            blocks[key].append(index)
    pairs: set[tuple[int, int]] = set()
    for members in blocks.values():
        if 1 < len(members) <= MAX_BLOCK:
            pairs.update(combinations(members, 2))
    return pairs


def _same_place(a: Record, b: Record) -> bool | None:
    """True/False when both have a street line; None when unknown."""
    if not a.street or not b.street:
        return None
    if a.street != b.street:
        return False
    return True


def score_pair(a: Record, b: Record) -> PairResult:
    reasons: list[tuple[str, float]] = []
    positives: list[float] = []
    sim = name_similarity(a.name_tokens, b.name_tokens)
    if sim >= 0.97:
        positives.append(0.60)
        reasons.append((f"names match ({sim:.2f})", 0.60))
    elif sim >= 0.90:
        positives.append(0.45)
        reasons.append((f"names very similar ({sim:.2f})", 0.45))
    elif sim >= 0.82:
        positives.append(0.25)
        reasons.append((f"names similar ({sim:.2f})", 0.25))
    elif sim >= 0.72:
        positives.append(0.10)
        reasons.append((f"names loosely similar ({sim:.2f})", 0.10))
    if a.email and a.email == b.email:
        positives.append(W_EMAIL)
        reasons.append(("same email", W_EMAIL))
    if a.domain and a.domain == b.domain:
        positives.append(W_DOMAIN)
        reasons.append((f"same website domain {a.domain}", W_DOMAIN))
    if a.phone and a.phone == b.phone:
        positives.append(W_PHONE)
        reasons.append(("same phone", W_PHONE))
    place = _same_place(a, b)
    if place and (not a.postal or not b.postal or a.postal == b.postal or a.city_key == b.city_key):
        positives.append(W_ADDRESS)
        reasons.append(("same street address", W_ADDRESS))
    elif a.postal and a.postal == b.postal and a.street and b.street and a.street.split(" ")[0] == b.street.split(" ")[0]:
        positives.append(W_POSTAL_STREET_NUM)
        reasons.append(("same postal code and street number", W_POSTAL_STREET_NUM))
    raw = 1.0
    for weight in positives:
        raw *= 1 - weight
    score = 1 - raw
    penalty = 0.0
    if a.province and b.province and a.province != b.province:
        penalty += 0.30
        reasons.append((f"different provinces {a.province}/{b.province}", -0.30))
    if a.phone and b.phone and a.phone != b.phone:
        penalty += 0.10
        reasons.append(("different phone numbers", -0.10))
    if a.domain and b.domain and a.domain != b.domain:
        penalty += 0.20
        reasons.append(("different website domains", -0.20))
    if place is False and a.postal and b.postal and a.postal != b.postal:
        penalty += 0.15
        reasons.append(("different addresses", -0.15))
    if a.unit and b.unit and a.unit != b.unit and place:
        penalty += 0.20
        reasons.append((f"different units {a.unit}/{b.unit}", -0.20))
    score = max(0.0, min(1.0, score - penalty))
    label = _label(a, b, score, sim, place)
    return PairResult(a.id, b.id, round(score, 4), label, reasons, round(sim, 4))


def _label(a: Record, b: Record, score: float, sim: float, place: bool | None) -> str:
    # same brand + clearly different physical location => a branch, never a merge candidate
    different_location = (place is False and (not a.postal or not b.postal or a.postal != b.postal)) or (
        a.phone and b.phone and a.phone != b.phone and place is False)
    if sim >= 0.9 and different_location and not (a.email and a.email == b.email and place is None):
        conflicting_sites = a.domain and b.domain and a.domain != b.domain
        shared = (a.domain and a.domain == b.domain) or (sim >= 0.97 and not conflicting_sites)
        if shared:
            return "branch"
    if score >= DUPLICATE_MIN:
        return "duplicate"
    if score >= REVIEW_MIN:
        return "review"
    return "distinct"


def find_pairs(records: list[Record]) -> list[PairResult]:
    results = []
    for i, j in sorted(candidate_pairs(records)):
        result = score_pair(records[i], records[j])
        if result.label != "distinct":
            results.append(result)
    results.sort(key=lambda r: (-r.score, r.a, r.b))
    return results
