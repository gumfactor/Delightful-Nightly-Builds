"""Minimal Anthropic Messages API client (stdlib urllib only).

Makes zero network calls unless ANTHROPIC_API_KEY is set in the runtime
environment. Never raises to signal "no key" or "call failed" — callers
treat a None return as "AI unavailable" and fall back to deterministic
output, per this repo's established runtime-credentials convention.
"""
import json
import os
import urllib.error
import urllib.request
from typing import Optional

_API_URL = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-haiku-4-5-20251001"
_ANTHROPIC_VERSION = "2023-06-01"
_TIMEOUT_SECONDS = 30


def call_claude(prompt: str, max_tokens: int = 400) -> Optional[str]:
    """Send a single-turn prompt to Claude Haiku and return the text
    response, or None if no API key is configured or the call fails."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    payload = json.dumps(
        {
            "model": _MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        _API_URL,
        data=payload,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError):
        return None

    try:
        blocks = body["content"]
        text = "".join(block["text"] for block in blocks if block.get("type") == "text")
    except (KeyError, TypeError):
        return None

    text = text.strip()
    return text or None
