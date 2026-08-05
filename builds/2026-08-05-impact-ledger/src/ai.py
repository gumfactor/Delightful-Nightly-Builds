"""Optional Claude Haiku commentary for rising papers, with an unconditional
deterministic fallback. Zero network calls are made when ANTHROPIC_API_KEY is unset.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"
REQUEST_TIMEOUT_SECONDS = 20


def fallback_note(title: str, previous_count: int, latest_count: int, latest_date: str) -> str:
    return (
        f"Cited {latest_count} times as of {latest_date}, "
        f"up from {previous_count} at the previous sync."
    )


def generate_note(
    title: str,
    abstract: str,
    previous_count: int,
    latest_count: int,
    latest_date: str,
    api_key: str | None = None,
) -> str:
    """Return a one-sentence note on why a paper may be gaining citations.

    Falls back to a deterministic template when no API key is configured, or when
    the Anthropic call fails for any reason (network, HTTP, or malformed response).
    """
    key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    template = fallback_note(title, previous_count, latest_count, latest_date)

    if not key:
        return template

    prompt = (
        "In one concise sentence, suggest why a research paper's citation count "
        "might be increasing, based only on its title and abstract below. "
        "Do not invent facts not supported by the text; if unsure, describe the "
        "paper's likely relevance instead of guessing a specific cause.\n\n"
        f"Title: {title}\n"
        f"Abstract: {abstract or '(no abstract available)'}\n"
        f"Citations went from {previous_count} to {latest_count} since the last check."
    )

    payload = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 120,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=payload,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
        data = json.loads(raw)
        content = data.get("content", [])
        text = "".join(block.get("text", "") for block in content if block.get("type") == "text").strip()
        return text if text else template
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
        return template
