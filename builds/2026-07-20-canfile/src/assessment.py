"""Ownership-verdict rule engine, with optional Claude enrichment.

The deterministic engine is always correct and always available with zero
API keys. Claude enrichment only improves the wording of the write-up; it
never changes the verdict or confidence, and any failure (missing key,
network error, malformed response) falls back to the deterministic text.
"""
from __future__ import annotations

import os
from typing import Any

VERDICT_CANADIAN = "canadian"
VERDICT_FOREIGN = "foreign"
VERDICT_UNCERTAIN = "uncertain"
VERDICT_INSUFFICIENT = "insufficient-data"

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"

CLAUDE_MODEL = "claude-haiku-4-5-20251001"


def _is_canada(labels: list[str]) -> bool:
    return any(label.strip().lower() == "canada" for label in labels)


def deterministic_assessment(company_name: str, facts: dict[str, Any]) -> dict[str, str]:
    """Apply the transparent ownership rule engine to a facts dict.

    `facts` keys (all lists of human-readable labels, may be empty):
      country_labels, headquarters_labels, parent_organization_labels,
      owned_by_labels, parent_country_labels
    """
    country_labels = facts.get("country_labels", [])
    parent_labels = facts.get("parent_organization_labels", []) + facts.get("owned_by_labels", [])
    parent_country_labels = facts.get("parent_country_labels", [])
    headquarters_labels = facts.get("headquarters_labels", [])

    has_parent = bool(parent_labels)
    hq_note = f" (headquartered in {', '.join(headquarters_labels)})" if headquarters_labels else ""

    if has_parent:
        parent_desc = ", ".join(parent_labels)
        if parent_country_labels:
            if _is_canada(parent_country_labels):
                return {
                    "verdict": VERDICT_CANADIAN,
                    "confidence": CONFIDENCE_HIGH,
                    "text": (
                        f"{company_name} is likely Canadian-owned{hq_note}: its parent/owner "
                        f"({parent_desc}) is based in Canada."
                    ),
                }
            return {
                "verdict": VERDICT_FOREIGN,
                "confidence": CONFIDENCE_HIGH,
                "text": (
                    f"{company_name} is likely foreign-owned{hq_note}: its parent/owner "
                    f"({parent_desc}) is based in {', '.join(parent_country_labels)}, not Canada."
                ),
            }
        return {
            "verdict": VERDICT_UNCERTAIN,
            "confidence": CONFIDENCE_MEDIUM,
            "text": (
                f"{company_name} has a parent/owner ({parent_desc}){hq_note}, but that "
                "entity's country of registration could not be determined from Wikidata. "
                "Manual verification recommended."
            ),
        }

    if country_labels:
        if _is_canada(country_labels):
            return {
                "verdict": VERDICT_CANADIAN,
                "confidence": CONFIDENCE_HIGH,
                "text": f"{company_name} is likely Canadian-owned{hq_note} with no parent/owner on record.",
            }
        return {
            "verdict": VERDICT_FOREIGN,
            "confidence": CONFIDENCE_HIGH,
            "text": (
                f"{company_name} is likely foreign-owned{hq_note}: its country of registration "
                f"is {', '.join(country_labels)}, not Canada."
            ),
        }

    return {
        "verdict": VERDICT_INSUFFICIENT,
        "confidence": CONFIDENCE_LOW,
        "text": (
            f"No country or ownership data was found for {company_name} on Wikidata. "
            "Manual research required."
        ),
    }


def enrich_with_claude(
    company_name: str,
    facts: dict[str, Any],
    deterministic_result: dict[str, str],
    api_key: str | None = None,
) -> str:
    """Ask Claude Haiku for a plain-English write-up of the same facts.

    Returns the deterministic text unchanged if no API key is configured,
    or if the call fails for any reason.
    """
    resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not resolved_key:
        return deterministic_result["text"]

    try:
        import anthropic  # imported lazily so the tool has zero hard dependencies

        client = anthropic.Anthropic(api_key=resolved_key)
        prompt = (
            "You are assisting a Canadian consumer-advocacy research project "
            "(The Canada List) that identifies Canadian-owned businesses. "
            f"Company: {company_name}\n"
            f"Country of registration: {facts.get('country_labels') or 'unknown'}\n"
            f"Headquarters: {facts.get('headquarters_labels') or 'unknown'}\n"
            f"Parent organization: {facts.get('parent_organization_labels') or 'none on record'}\n"
            f"Owned by: {facts.get('owned_by_labels') or 'none on record'}\n"
            f"Parent/owner's country: {facts.get('parent_country_labels') or 'unknown'}\n"
            f"Rule-based verdict: {deterministic_result['verdict']} "
            f"(confidence: {deterministic_result['confidence']})\n\n"
            "Write a 2-3 sentence plain-English assessment of whether this company is "
            "Canadian-owned, citing the specific facts above. Do not change the verdict "
            "or confidence level, only explain it clearly."
        )
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()
        return text if text else deterministic_result["text"]
    except Exception:
        return deterministic_result["text"]
