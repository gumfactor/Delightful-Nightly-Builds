"""Weighted aggregation of heuristics.analyze_text() output into a single
0-100 Human Voice Score.

Every weight below is a named constant, not a tuned/opaque model — the goal
is an explainable score, not a black box. Higher score = reads more human;
lower score = more of the counted AI-tell / mechanical-rhythm patterns.
"""

from __future__ import annotations

AI_TELL_PENALTY_PER_HIT = 2.5
AI_TELL_PENALTY_CAP = 40.0

EM_DASH_DENSITY_THRESHOLD = 8.0  # per 1000 words
EM_DASH_PENALTY_CAP = 10.0

SEMICOLON_DENSITY_THRESHOLD = 5.0  # per 1000 words
SEMICOLON_PENALTY_CAP = 6.0

HEDGE_DENSITY_THRESHOLD = 10.0  # per 1000 words
HEDGE_PENALTY_SCALE = 0.5
HEDGE_PENALTY_CAP = 8.0

PASSIVE_RATIO_THRESHOLD = 0.15  # fraction of sentences
PASSIVE_PENALTY_SCALE = 40.0
PASSIVE_PENALTY_CAP = 10.0

RULE_OF_THREE_PENALTY_PER_HIT = 2.0
RULE_OF_THREE_PENALTY_CAP = 8.0

BURSTINESS_CV_THRESHOLD = 0.30  # coefficient of variation
BURSTINESS_MIN_SENTENCES = 5
BURSTINESS_PENALTY_SCALE = 40.0
BURSTINESS_PENALTY_CAP = 15.0

TTR_THRESHOLD = 0.40
TTR_MIN_WORDS = 200
TTR_PENALTY_SCALE = 50.0
TTR_PENALTY_CAP = 15.0

REPEATED_OPENER_PENALTY_PER_EXTRA = 2.0
REPEATED_OPENER_PENALTY_CAP = 8.0


def _density_per_1000(count: int, word_count: int) -> float:
    if word_count <= 0:
        return 0.0
    return count / word_count * 1000.0


def compute_score(analysis: dict) -> dict:
    """Return {"score": float, "flag_count": int, "breakdown": {...}}."""
    word_count = analysis["word_count"]
    breakdown: dict[str, float] = {}

    ai_tell_hits = analysis["ai_tell_hits"]
    breakdown["ai_tell_phrases"] = min(
        AI_TELL_PENALTY_CAP, len(ai_tell_hits) * AI_TELL_PENALTY_PER_HIT
    )

    em_dash_density = _density_per_1000(analysis["em_dash_count"], word_count)
    breakdown["em_dash_density"] = min(
        EM_DASH_PENALTY_CAP, max(0.0, em_dash_density - EM_DASH_DENSITY_THRESHOLD)
    )

    semicolon_density = _density_per_1000(analysis["semicolon_count"], word_count)
    breakdown["semicolon_density"] = min(
        SEMICOLON_PENALTY_CAP,
        max(0.0, semicolon_density - SEMICOLON_DENSITY_THRESHOLD),
    )

    hedge_density = _density_per_1000(len(analysis["hedge_hits"]), word_count)
    breakdown["hedge_density"] = min(
        HEDGE_PENALTY_CAP,
        max(0.0, hedge_density - HEDGE_DENSITY_THRESHOLD) * HEDGE_PENALTY_SCALE,
    )

    sentence_count = analysis["sentence_count"]
    passive_ratio = (
        len(analysis["passive_matches"]) / sentence_count if sentence_count > 0 else 0.0
    )
    breakdown["passive_voice"] = min(
        PASSIVE_PENALTY_CAP,
        max(0.0, passive_ratio - PASSIVE_RATIO_THRESHOLD) * PASSIVE_PENALTY_SCALE,
    )

    breakdown["rule_of_three"] = min(
        RULE_OF_THREE_PENALTY_CAP,
        len(analysis["rule_of_three_matches"]) * RULE_OF_THREE_PENALTY_PER_HIT,
    )

    cv = analysis["burstiness"]["cv"]
    if sentence_count >= BURSTINESS_MIN_SENTENCES and cv < BURSTINESS_CV_THRESHOLD:
        breakdown["low_burstiness"] = min(
            BURSTINESS_PENALTY_CAP,
            (BURSTINESS_CV_THRESHOLD - cv) * BURSTINESS_PENALTY_SCALE,
        )
    else:
        breakdown["low_burstiness"] = 0.0

    ttr = analysis["type_token_ratio"]
    if word_count >= TTR_MIN_WORDS and ttr < TTR_THRESHOLD:
        breakdown["low_vocabulary_diversity"] = min(
            TTR_PENALTY_CAP, (TTR_THRESHOLD - ttr) * TTR_PENALTY_SCALE
        )
    else:
        breakdown["low_vocabulary_diversity"] = 0.0

    repeated_extra = sum(
        max(0, item["count"] - 2) for item in analysis["repeated_openers"]
    )
    breakdown["repeated_paragraph_openers"] = min(
        REPEATED_OPENER_PENALTY_CAP, repeated_extra * REPEATED_OPENER_PENALTY_PER_EXTRA
    )

    total_penalty = sum(breakdown.values())
    score = max(0.0, min(100.0, 100.0 - total_penalty))

    flag_count = (
        len(ai_tell_hits)
        + len(analysis["rule_of_three_matches"])
        + len(analysis["repeated_openers"])
        + (1 if breakdown["em_dash_density"] > 0 else 0)
        + (1 if breakdown["semicolon_density"] > 0 else 0)
        + (1 if breakdown["hedge_density"] > 0 else 0)
        + (1 if breakdown["passive_voice"] > 0 else 0)
        + (1 if breakdown["low_burstiness"] > 0 else 0)
        + (1 if breakdown["low_vocabulary_diversity"] > 0 else 0)
    )

    return {"score": round(score, 1), "flag_count": flag_count, "breakdown": breakdown}
