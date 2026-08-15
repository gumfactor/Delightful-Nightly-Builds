"""Optional Claude Haiku enrichment for uncertain verdicts.

Only ever called for the ``uncertain`` bucket — the deterministic rule
engine's verdict is never overridden by this. This function's only job is
to turn the rule engine's already-computed evidence string into a clearer
plain-English sentence. With no ``ANTHROPIC_API_KEY`` set (the default in
this build's own container), it makes zero network calls and returns None,
matching every other optional-AI build in this catalog.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from src.rules import VERDICT_UNCERTAIN

MODEL = "claude-haiku-4-5-20251001"
API_URL = "https://api.anthropic.com/v1/messages"
TIMEOUT_SECONDS = 15


def enrich(business_name: str, evidence: str, verdict: str, api_key: str | None = None) -> str | None:
    """Return a one-sentence plain-English note, or None if unavailable/failed."""
    if verdict != VERDICT_UNCERTAIN:
        return None

    api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    prompt = (
        "A Canadian-ownership research tool found this evidence for a business "
        f'named "{business_name}": {evidence}\n\n'
        "Write exactly one plain-English sentence (no preamble, no quotes) "
        "explaining to a non-technical reader why this business's Canadian-"
        "ownership status is uncertain, based only on the evidence given. "
        "Do not invent facts not present in the evidence."
    )
    payload = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 150,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        note = body["content"][0]["text"].strip()
    except (urllib.error.URLError, OSError, KeyError, IndexError, json.JSONDecodeError, TimeoutError, ValueError):
        return None

    return note or None
