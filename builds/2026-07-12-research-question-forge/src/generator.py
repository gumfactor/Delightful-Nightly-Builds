"""Combinatorial research-question generator with compatibility rules and novelty scoring."""
from __future__ import annotations

import itertools
import json
import re
from pathlib import Path
from typing import Any

TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"

_STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "of", "to", "does", "is", "with",
    "on", "for", "does", "predict", "relationship", "between",
}

_FORENSIC_TESTING_CAUTION_POPULATIONS = {"p_forensic_offenders", "p_adolescent_cd"}
_RESOURCE_HEAVY_METHODS = {"m_fmri", "m_eeg", "m_rct"}
_METHOD_BASE_TESTABILITY = {
    "m_fmri": "needs-resources",
    "m_eeg": "needs-resources",
    "m_salivary_cortisol": "feasible-now",
    "m_behavioral_task": "feasible-now",
    "m_survey_longitudinal": "feasible-now",
    "m_ema": "feasible-now",
    "m_rct": "needs-resources",
}


def load_taxonomy(path: Path = TAXONOMY_PATH) -> dict[str, list[dict[str, Any]]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _tags(entry: dict[str, Any]) -> set[str]:
    return set(entry.get("tags", []))


def is_compatible(
    population: dict[str, Any],
    construct: dict[str, Any],
    outcome: dict[str, Any],
    method: dict[str, Any],
    frame: dict[str, Any],
) -> bool:
    """Rule-based compatibility check across the five taxonomy dimensions."""
    if not (_tags(population) & _tags(construct)):
        return False

    combined = _tags(construct) | _tags(outcome)
    requires = set(method.get("requires_tags", []))
    excludes = set(method.get("excludes_tags", []))
    if requires and not (requires & combined):
        return False
    if excludes & combined:
        return False

    if not (_tags(frame) & (_tags(population) | _tags(construct))):
        return False

    return True


def testability_tag(population: dict[str, Any], method: dict[str, Any]) -> str:
    base = _METHOD_BASE_TESTABILITY.get(method["id"], "needs-resources")
    if population["id"] in _FORENSIC_TESTING_CAUTION_POPULATIONS and method["id"] in _RESOURCE_HEAVY_METHODS:
        return "speculative"
    return base


def render_skeleton(
    population: dict[str, Any],
    construct: dict[str, Any],
    outcome: dict[str, Any],
    method: dict[str, Any],
    frame: dict[str, Any],
) -> str:
    return (
        f"Does {construct['label']} predict {outcome['label']} in "
        f"{population['label']}, and is this relationship explained by "
        f"{frame['label']}?"
    )


def render_rationale(
    population: dict[str, Any],
    construct: dict[str, Any],
    outcome: dict[str, Any],
    method: dict[str, Any],
    frame: dict[str, Any],
    testability: str,
) -> str:
    testability_note = {
        "feasible-now": "This design is achievable with standard lab resources.",
        "needs-resources": "This design requires imaging or trial infrastructure beyond a standard behavioral study.",
        "speculative": "Access to this population for this method is a real constraint and should be scoped carefully before committing.",
    }[testability]
    return (
        f"Measured via {method['label']}, framed through {frame['label']}. "
        f"{testability_note}"
    )


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def novelty_score(skeleton: str, existing_skeletons: list[str]) -> float:
    """1.0 = fully novel vs. the library; lower means it overlaps heavily with a past entry."""
    if not existing_skeletons:
        return 1.0
    new_tokens = _tokenize(skeleton)
    max_sim = max(jaccard(new_tokens, _tokenize(existing)) for existing in existing_skeletons)
    return round(1.0 - max_sim, 4)


def all_valid_combinations(taxonomy: dict[str, list[dict[str, Any]]]):
    """Yield every taxonomy combination that passes the compatibility rules."""
    for population, construct, outcome, method, frame in itertools.product(
        taxonomy["populations"],
        taxonomy["constructs"],
        taxonomy["outcomes"],
        taxonomy["methods"],
        taxonomy["frames"],
    ):
        if is_compatible(population, construct, outcome, method, frame):
            yield population, construct, outcome, method, frame


def generate_batch(
    count: int,
    existing_skeletons: list[str],
    taxonomy: dict[str, list[dict[str, Any]]] | None = None,
    rng_seed: int | None = None,
) -> list[dict[str, Any]]:
    """Generate up to `count` compatibility-valid, deduplicated question dicts.

    Deterministic when `rng_seed` is set; otherwise uses Python's default random
    state seeded by nothing extra (caller may pre-seed `random` if determinism
    across runs is required).
    """
    import random

    taxonomy = taxonomy or load_taxonomy()
    candidates = list(all_valid_combinations(taxonomy))
    rnd = random.Random(rng_seed) if rng_seed is not None else random.Random()
    rnd.shuffle(candidates)

    results: list[dict[str, Any]] = []
    seen_skeletons = list(existing_skeletons)
    seen_ids: set[tuple] = set()

    for population, construct, outcome, method, frame in candidates:
        if len(results) >= count:
            break
        combo_id = (population["id"], construct["id"], outcome["id"], method["id"], frame["id"])
        if combo_id in seen_ids:
            continue
        seen_ids.add(combo_id)

        skeleton = render_skeleton(population, construct, outcome, method, frame)
        testability = testability_tag(population, method)
        rationale = render_rationale(population, construct, outcome, method, frame, testability)
        score = novelty_score(skeleton, seen_skeletons)
        seen_skeletons.append(skeleton)

        results.append(
            {
                "population": population["id"],
                "construct": construct["id"],
                "outcome": outcome["id"],
                "method": method["id"],
                "frame": frame["id"],
                "skeleton": skeleton,
                "rationale": rationale,
                "testability": testability,
                "novelty_score": score,
            }
        )

    return results
