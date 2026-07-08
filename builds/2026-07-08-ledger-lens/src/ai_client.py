"""Minimal Anthropic API client (stdlib-only, via urllib) with a deterministic fallback path.

No third-party SDK dependency, matching the pattern used across this repo's recent builds.
Never sends more than a redacted merchant description and a rounded amount magnitude —
no account numbers, no dates, no other personal data.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
import urllib.error

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"
TIMEOUT_SECONDS = 20

_DIGIT_RUN_RE = re.compile(r"\d{5,}")


def redact_reference_numbers(text: str) -> str:
    """Strip long digit runs (account/reference/confirmation numbers) from a description."""
    return _DIGIT_RUN_RE.sub("[ref]", text)


def is_configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def classify_batch(descriptions: list, categories: list) -> dict | None:
    """Ask Claude to classify a batch of (redacted) merchant descriptions.

    Returns {description: category} on success, or None if the API is unavailable,
    unconfigured, or the call fails for any reason (caller must fall back).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not descriptions:
        return None

    redacted = [redact_reference_numbers(d) for d in descriptions]
    prompt = (
        "Classify each merchant/transaction description below into exactly one of "
        f"these categories: {', '.join(categories)}.\n"
        "Respond ONLY with a JSON object mapping each description (verbatim) to its category, "
        "no other text.\n\nDescriptions:\n" + "\n".join(f"- {d}" for d in redacted)
    )

    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=payload,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None

    try:
        text = body["content"][0]["text"]
        mapping = json.loads(text)
    except (KeyError, IndexError, ValueError):
        return None

    if not isinstance(mapping, dict):
        return None

    # Map back from redacted description to the caller's original description.
    result = {}
    for original, redacted_desc in zip(descriptions, redacted):
        category = mapping.get(redacted_desc)
        if category in categories:
            result[original] = category
    return result or None


def generate_insights(summary: dict) -> str | None:
    """Ask Claude for a short plain-English spending insights paragraph.

    Only aggregate numbers (category totals, month-over-month deltas) are sent —
    never individual transaction descriptions. Returns None on any failure.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    prompt = (
        "Here is a summary of a person's monthly spending (aggregate numbers only, "
        "no transaction-level detail):\n"
        f"{json.dumps(summary)}\n\n"
        "Write a single short paragraph (3-4 sentences, plain English, no markdown) "
        "highlighting the most useful, specific observation for the person reviewing this."
    )

    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=payload,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["content"][0]["text"].strip()
    except (urllib.error.URLError, TimeoutError, ValueError, OSError, KeyError, IndexError):
        return None
