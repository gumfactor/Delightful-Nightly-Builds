"""Extract structured decision-email fields from pasted, unstructured text.

Always runs a deterministic regex/keyword parser first. If ANTHROPIC_API_KEY
is set, an optional Claude Haiku pass is attempted and preferred when it
returns well-formed data; any missing key, network error, or malformed
response falls back to the deterministic result. Zero network calls are
ever made without an API key.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import date
from typing import Any

# Order matters: more specific/exclusive phrases are checked first so that a
# rejection phrase like "unable to accept" is never mis-caught by a looser
# acceptance keyword.
DECISION_KEYWORDS = {
    "rejected": ["reject", "regret to inform", "unable to accept", "decline to publish", "not suitable"],
    "revise_resubmit": ["revise and resubmit", "major revision", "minor revision", "revise & resubmit"],
    "accepted": ["pleased to accept", "delighted to accept", "happy to accept", "accepted for publication"],
}

DATE_PATTERNS = [
    re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"),  # ISO
    re.compile(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b", re.IGNORECASE),
]

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

JOURNAL_PATTERN = re.compile(r"(?:manuscript submitted to|submission to|for)\s+([A-Z][A-Za-z0-9&:,.' -]{2,60}?)(?:\.|,|\n|$)")


def deterministic_parse(text: str) -> dict[str, Any]:
    """Regex/keyword-based extraction. Never raises; degrades to None fields."""
    text = text or ""
    lower = text.lower()

    decision = None
    for label, keywords in DECISION_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            decision = label
            break

    journal_match = JOURNAL_PATTERN.search(text)
    journal = journal_match.group(1).strip() if journal_match else None

    deadline = _extract_deadline(text) if decision == "revise_resubmit" else None

    return {
        "decision": decision,
        "journal": journal,
        "revision_deadline": deadline,
        "source": "capture-fallback",
    }


def _extract_deadline(text: str) -> str | None:
    iso_match = DATE_PATTERNS[0].search(text)
    if iso_match:
        y, m, d = iso_match.groups()
        try:
            return date(int(y), int(m), int(d)).isoformat()
        except ValueError:
            return None

    month_match = DATE_PATTERNS[1].search(text)
    if month_match:
        month_name, day_str, year_str = month_match.groups()
        month_num = MONTHS.get(month_name.lower())
        if month_num:
            try:
                return date(int(year_str), month_num, int(day_str)).isoformat()
            except ValueError:
                return None
    return None


def ai_parse(text: str, api_key: str | None = None) -> dict[str, Any] | None:
    """Attempt Claude Haiku extraction. Returns None on any failure (missing key,
    network error, malformed response) so the caller can fall back."""
    api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    prompt = (
        "Extract fields from this academic journal decision/confirmation email. "
        "Reply with ONLY a JSON object with keys: decision "
        "(one of: accepted, rejected, revise_resubmit, or null), "
        "journal (string or null), revision_deadline (ISO YYYY-MM-DD string or null).\n\n"
        f"EMAIL TEXT:\n{text}"
    )
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 300,
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
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["content"][0]["text"]
        parsed = json.loads(content)
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, TimeoutError, ValueError):
        return None

    if "decision" not in parsed:
        return None
    if parsed.get("decision") not in (None, "accepted", "rejected", "revise_resubmit"):
        return None

    parsed["source"] = "capture-ai"
    parsed.setdefault("journal", None)
    parsed.setdefault("revision_deadline", None)
    return parsed


def extract(text: str, api_key: str | None = None) -> dict[str, Any]:
    """Public entry point: deterministic parse always computed; AI result
    preferred when available and well-formed."""
    fallback = deterministic_parse(text)
    ai_result = ai_parse(text, api_key=api_key)
    if ai_result is not None:
        return ai_result
    return fallback
