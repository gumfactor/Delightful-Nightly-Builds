"""Optional Claude Haiku enrichment: confirms ambiguous near-duplicate
clusters and suggests canonical ownership_status mappings.

Fully optional. When ANTHROPIC_API_KEY is not set, every function here
returns a deterministic fallback and no network call is made. Tests must
mock urllib.request.urlopen — never make a live API call in a test.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"
REQUEST_TIMEOUT_SECONDS = 20


def is_ai_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _call_claude(prompt: str, max_tokens: int = 300) -> str | None:
    """Send one message to Claude Haiku. Returns the text response, or None
    on any failure (missing key, network error, malformed response) — the
    caller is always responsible for falling back deterministically.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    payload = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": max_tokens,
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
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None

    try:
        return body["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None


def confirm_duplicate_cluster(business_names: list) -> tuple:
    """Ask Claude whether a set of near-duplicate business names likely
    refer to the same real-world business. Returns (confirmed, reasoning).

    Deterministic fallback (no key, or any API failure): confirmed=None
    (meaning "unconfirmed by AI, treat the similarity score alone"),
    reasoning explains the fallback was used.
    """
    if not is_ai_available():
        return None, "AI enrichment not configured (no ANTHROPIC_API_KEY); relying on name-similarity score alone."

    names_list = "\n".join(f"- {name}" for name in business_names)
    prompt = (
        "These business names were flagged as possible duplicate entries in a "
        "Canadian business directory:\n"
        f"{names_list}\n\n"
        "Reply with exactly one line in the format:\n"
        "CONFIRMED: yes|no | REASON: <one short sentence>"
    )
    response_text = _call_claude(prompt)
    if response_text is None:
        return None, "AI call failed; relying on name-similarity score alone."

    return _parse_confirmation_response(response_text)


def _parse_confirmation_response(text: str) -> tuple:
    lowered = text.lower()
    reason = text.split("REASON:", 1)[1].strip() if "REASON:" in text else text.strip()
    if "confirmed: yes" in lowered:
        return True, reason
    if "confirmed: no" in lowered:
        return False, reason
    return None, f"Could not parse AI response; relying on name-similarity score alone. (raw: {text[:120]})"


def suggest_ownership_status_mapping(value: str, canonical_values: list) -> tuple:
    """Ask Claude which canonical ownership_status value an unrecognized
    value most likely means. Returns (suggestion_or_None, reasoning).

    Deterministic fallback: no suggestion, value stays "unmapped".
    """
    if not is_ai_available():
        return None, "AI enrichment not configured (no ANTHROPIC_API_KEY); value left unmapped."

    options = ", ".join(canonical_values)
    prompt = (
        f"A Canadian business directory uses these canonical ownership_status values: {options}.\n"
        f"An entry has the non-canonical value '{value}'. "
        "Reply with exactly one line in the format:\n"
        "SUGGESTION: <one of the canonical values, or 'none'> | REASON: <one short sentence>"
    )
    response_text = _call_claude(prompt)
    if response_text is None:
        return None, "AI call failed; value left unmapped."

    return _parse_suggestion_response(response_text, canonical_values)


def _parse_suggestion_response(text: str, canonical_values: list) -> tuple:
    reason = text.split("REASON:", 1)[1].strip() if "REASON:" in text else text.strip()
    if "SUGGESTION:" not in text:
        return None, f"Could not parse AI response; value left unmapped. (raw: {text[:120]})"
    suggestion_raw = text.split("SUGGESTION:", 1)[1].split("|")[0].strip().lower()
    for canonical in canonical_values:
        if canonical.lower() == suggestion_raw:
            return canonical, reason
    return None, reason
