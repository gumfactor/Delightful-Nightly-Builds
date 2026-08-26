"""Three fixed critic personas, each weighting a subset of the 5 rule categories.

Score = (sum of weights for categories that fired True) / (sum of weights for
categories the persona can evaluate at all, i.e. fired is not None) * 100.
A category the persona doesn't weight (weight 0) never affects its score.
If every weighted category is unavailable (None), the score is None rather
than a misleading 0 -- an honest "cannot assess" beats a false clean bill.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .rules import RuleResult

PERSONAS = {
    "value_skeptic": {
        "name": "Value Skeptic",
        "weights": {
            "valuation_stretch": 3,
            "narrative_fragility": 2,
            "growth_deceleration": 1,
            "margin_debt_risk": 0,
            "insider_selling": 0,
        },
    },
    "macro_bear": {
        "name": "Macro Bear",
        "weights": {
            "growth_deceleration": 3,
            "margin_debt_risk": 3,
            "valuation_stretch": 1,
            "narrative_fragility": 1,
            "insider_selling": 0,
        },
    },
    "governance_hawk": {
        "name": "Governance Hawk",
        "weights": {
            "insider_selling": 3,
            "narrative_fragility": 3,
            "margin_debt_risk": 1,
            "valuation_stretch": 0,
            "growth_deceleration": 0,
        },
    },
}


@dataclass
class PersonaScore:
    key: str
    name: str
    score: Optional[int]
    fired: list[RuleResult]
    not_fired: list[RuleResult]
    unavailable: list[RuleResult]


def score_persona(persona_key: str, results: list[RuleResult]) -> PersonaScore:
    persona = PERSONAS[persona_key]
    weights = persona["weights"]
    by_key = {r.key: r for r in results}

    weighted_total = 0
    weighted_fired = 0
    fired, not_fired, unavailable = [], [], []

    for rule_key, weight in weights.items():
        if weight == 0:
            continue
        result = by_key.get(rule_key)
        if result is None or result.fired is None:
            if result is not None:
                unavailable.append(result)
            continue
        weighted_total += weight
        if result.fired:
            weighted_fired += weight
            fired.append(result)
        else:
            not_fired.append(result)

    score = round(100 * weighted_fired / weighted_total) if weighted_total > 0 else None
    return PersonaScore(persona_key, persona["name"], score, fired, not_fired, unavailable)


def score_all_personas(results: list[RuleResult]) -> list[PersonaScore]:
    return [score_persona(key, results) for key in PERSONAS]


def overall_score(persona_scores: list[PersonaScore]) -> Optional[int]:
    valid = [p.score for p in persona_scores if p.score is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid))
