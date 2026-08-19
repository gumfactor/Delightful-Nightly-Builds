"""Optional Claude Haiku narrative briefing. Input is aggregate counts only —
never a name, dollar figure, or grant identifier — so there is nothing
personal or financial to leak even when the AI path is used."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections import Counter

from src.models import Flag, GrantBudgetSummary, OvercommitmentWindow

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"


def build_aggregate_summary(
    flags: list[Flag],
    summaries: list[GrantBudgetSummary],
    windows: list[OvercommitmentWindow],
) -> dict:
    severity_counts = Counter(f.severity.value for f in flags)
    code_counts = Counter(f.code for f in flags)

    return {
        "total_grants": len(summaries),
        "total_flags": len(flags),
        "errors": severity_counts.get("error", 0),
        "warnings": severity_counts.get("warning", 0),
        "info": severity_counts.get("info", 0),
        "people_overcommitted": len({w.person_name for w in windows}),
        "flag_types": dict(sorted(code_counts.items())),
    }


def deterministic_template(aggregate: dict) -> str:
    if aggregate["total_flags"] == 0:
        return (
            f"Audited {aggregate['total_grants']} grant/fiscal-year budget group(s) with zero flags. "
            "No indirect-cost mismatches or effort overcommitments found."
        )

    parts = [
        f"Audited {aggregate['total_grants']} grant/fiscal-year budget group(s) and found "
        f"{aggregate['total_flags']} flag(s): {aggregate['errors']} error(s), "
        f"{aggregate['warnings']} warning(s), {aggregate['info']} informational."
    ]
    if aggregate["people_overcommitted"] > 0:
        parts.append(
            f"{aggregate['people_overcommitted']} person/people have overlapping effort commitments "
            "above the configured cap — review the Effort Timeline panel before certifying effort."
        )
    if aggregate["errors"] > 0:
        parts.append("Errors should be resolved before this budget or effort report is submitted.")
    return " ".join(parts)


def _call_anthropic(aggregate: dict, api_key: str) -> str:
    prompt = (
        "You audit research grant budgets and effort commitments. Given only this aggregate "
        "summary (no names, dollar amounts, or grant identifiers were provided), write a 2-3 "
        "sentence plain-English briefing for the researcher. Summary: " + json.dumps(aggregate)
    )
    payload = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.loads(response.read().decode("utf-8"))
    return "".join(block.get("text", "") for block in body.get("content", [])).strip()


def generate_ai_briefing(aggregate: dict, api_key: str | None) -> str:
    if not api_key:
        return deterministic_template(aggregate)

    try:
        text = _call_anthropic(aggregate, api_key)
        return text if text else deterministic_template(aggregate)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, KeyError):
        return deterministic_template(aggregate)
