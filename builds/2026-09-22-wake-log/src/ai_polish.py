"""Optional Claude Haiku prose polish for a deterministic narrative draft.

Design contract:
  - Called only when ANTHROPIC_API_KEY is set; otherwise this module makes
    zero network calls (checked by the caller before invoking `polish`).
  - The model may only restyle the draft -- every fact string extracted from
    the real forecast (wind speed, gust speed, temperature, precipitation
    probability, Beaufort name) must still appear verbatim in its output.
  - Any missing key, network error, malformed response, or a response that
    drops a required fact silently falls back to the deterministic draft.
    The tool must never look broken just because the AI path failed.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Dict, Optional

from .narrative import verify_facts_present

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = (
    "You are polishing a boating trip-log entry. Rewrite the draft to read more "
    "vividly, in a personal log-entry voice. You MUST preserve every number and "
    "named fact in the draft exactly as given (wind speed, gust speed, temperature, "
    "precipitation percentage, Beaufort force name) -- do not round, convert units, "
    "or invent any new numbers or facts. Do not add facts not present in the draft. "
    "Keep it to 2-4 sentences. Return only the rewritten entry text, nothing else."
)


def polish(
    draft: str,
    facts: Dict[str, str],
    api_key: Optional[str] = None,
    timeout: int = 20,
) -> str:
    """Attempt an AI polish of `draft`. Returns the polished text on success,
    or `draft` unchanged on any failure or fact-dropping response."""
    key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return draft

    body = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 300,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": draft}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.URLError:
        return draft

    try:
        payload = json.loads(raw)
        content_blocks = payload["content"]
        polished_text = "".join(block.get("text", "") for block in content_blocks).strip()
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return draft

    if not polished_text or not verify_facts_present(polished_text, facts):
        return draft

    return polished_text
