"""Three fixed reviewer personas that critique a parsed proposal draft.

Every persona always has a deterministic score and rationale, derived
purely from the checklist result — this path requires no network access
and is the tool's real floor of usefulness. When ANTHROPIC_API_KEY is set,
an optional Claude Haiku call per persona is attempted; any missing key,
network error, timeout, or malformed response falls back to the
deterministic result with zero retries, following the same
deterministic-first/AI-preferred/unconditional-fallback shape used in
2026-08-06-manuscript-pipeline/src/parsing.py.

NIH scoring convention: 1 = exceptional, 9 = poor. Only Significance,
Innovation, Approach, and overall Impact are scored here — Investigator and
Environment are deliberately never scored, since they require CV/facilities
information this tool is never given.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from . import checklist as checklist_module

SECTION_LABELS = {
    "aims": "Specific Aims",
    "significance": "Significance",
    "innovation": "Innovation",
    "approach": "Approach",
    "rigor": "Rigor and Reproducibility",
}

PERSONAS: list[dict[str, Any]] = [
    {
        "key": "rigor_hawk",
        "name": "The Rigor Hawk",
        "tone": "a methodologist obsessed with statistical power, pre-registration, and reproducibility; skeptical of any claim not backed by a stated analysis plan",
        "weight_sections": {"approach": 0.5, "rigor": 0.3, "aims": 0.1, "significance": 0.05, "innovation": 0.05},
    },
    {
        "key": "vision_advocate",
        "name": "The Vision Advocate",
        "tone": "a big-picture thinker who cares about paradigm-shifting potential and field-level impact; impatient with incremental, safe proposals",
        "weight_sections": {"significance": 0.4, "innovation": 0.4, "aims": 0.15, "approach": 0.05},
    },
    {
        "key": "generalist",
        "name": "The Generalist",
        "tone": "a balanced reviewer weighing feasibility, clarity, and overall coherence across the whole proposal",
        "weight_sections": {"aims": 0.25, "significance": 0.2, "innovation": 0.2, "approach": 0.25, "rigor": 0.1},
    },
]


def _weighted_pass_rate(checklist_result: dict, weight_sections: dict[str, float]) -> float:
    sections = checklist_result["sections"]
    total_weight = sum(weight_sections.values())
    if total_weight == 0:
        return 0.0
    weighted = sum(weight * sections.get(key, {}).get("pass_rate", 0.0) for key, weight in weight_sections.items())
    return weighted / total_weight


def deterministic_score(checklist_result: dict, persona: dict) -> int:
    """1 (exceptional) to 9 (poor), derived from this persona's
    weighted checklist pass-rate. A fully-passing checklist always scores
    a 1; a fully-failing one always scores a 9."""
    pass_rate = _weighted_pass_rate(checklist_result, persona["weight_sections"])
    score = round(1 + (1 - pass_rate) * 8)
    return max(1, min(9, score))


def _focus_sections(persona: dict, limit: int = 2) -> list[str]:
    ranked = sorted(persona["weight_sections"].items(), key=lambda pair: -pair[1])
    return [key for key, _weight in ranked[:limit]]


def deterministic_rationale(checklist_result: dict, persona: dict) -> list[str]:
    focus = _focus_sections(persona)
    failed = checklist_module.failed_items(checklist_result, section_keys=focus)
    if not failed:
        labels = ", ".join(SECTION_LABELS[key] for key in focus)
        return [f"All checklist items this reviewer weighs most heavily ({labels}) are present in the draft."]
    bullets = [f"{SECTION_LABELS[item['section']]}: {item['description']}" for item in failed[:4]]
    return bullets


def ai_persona_critique(persona: dict, sections: dict[str, str], checklist_result: dict, api_key: str | None = None) -> dict | None:
    """Attempt a Claude Haiku critique in this persona's voice. Returns
    None on any failure (missing key, network error, malformed response)
    so the caller falls back to the deterministic result."""
    api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    section_blocks = "\n\n".join(
        f"### {SECTION_LABELS[key]}\n{text}" for key, text in sections.items() if text.strip()
    )
    missing = ", ".join(SECTION_LABELS[key] for key in checklist_result["missing_sections"]) or "none"

    prompt = (
        "You are a mock NIH study section reviewer with this persona: "
        f"{persona['tone']}\n\n"
        "Read the grant proposal draft excerpt below and produce a critical review "
        "in your persona's voice. Reply with ONLY a JSON object with keys: "
        "\"score\" (integer 1-9, where 1 = exceptional and 9 = poor, NIH impact-score "
        "convention), and \"rationale\" (a list of 2-5 short critique bullets, each a "
        "single sentence, specific to this draft).\n\n"
        f"Sections missing entirely from the draft: {missing}\n\n"
        f"DRAFT EXCERPT:\n{section_blocks}"
    )
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["content"][0]["text"]
        parsed = json.loads(content)
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, TimeoutError, ValueError):
        return None

    score = parsed.get("score")
    rationale = parsed.get("rationale")
    if not isinstance(score, int) or not (1 <= score <= 9):
        return None
    if not isinstance(rationale, list) or not rationale or not all(isinstance(item, str) and item.strip() for item in rationale):
        return None

    return {"score": score, "rationale": [item.strip() for item in rationale][:5]}


def build_resume(personas_out: list[dict], checklist_result: dict) -> str:
    scores = [p["score"] for p in personas_out]
    variance = max(scores) - min(scores)
    best = min(personas_out, key=lambda p: p["score"])
    worst = max(personas_out, key=lambda p: p["score"])

    if variance <= 1:
        alignment = f"The panel was closely aligned (scores {min(scores)}-{max(scores)})."
    else:
        alignment = (
            f"The panel diverged: {best['name']} was most positive (score {best['score']}), "
            f"while {worst['name']} was most critical (score {worst['score']})."
        )

    top_failed = checklist_module.failed_items(checklist_result)[:3]
    if top_failed:
        concerns = "; ".join(f"{SECTION_LABELS[item['section']]} — {item['description']}" for item in top_failed)
        concerns_sentence = f" Shared concerns to address before submission: {concerns}."
    else:
        concerns_sentence = " No checklist items were flagged — the draft covers the core completeness and rigor elements this tool checks for."

    return alignment + concerns_sentence


def build_review(sections: dict[str, str], checklist_result: dict, api_key: str | None = None) -> dict:
    personas_out = []
    ai_used = False

    for persona in PERSONAS:
        ai_result = ai_persona_critique(persona, sections, checklist_result, api_key=api_key)
        if ai_result is not None:
            score = ai_result["score"]
            rationale = ai_result["rationale"]
            source = "ai"
            ai_used = True
        else:
            score = deterministic_score(checklist_result, persona)
            rationale = deterministic_rationale(checklist_result, persona)
            source = "deterministic"

        personas_out.append({
            "key": persona["key"],
            "name": persona["name"],
            "score": score,
            "rationale": rationale,
            "source": source,
        })

    overall_impact = round(sum(p["score"] for p in personas_out) / len(personas_out), 1)
    resume = build_resume(personas_out, checklist_result)

    return {
        "personas": personas_out,
        "overall_impact": overall_impact,
        "resume": resume,
        "ai_used": ai_used,
    }
