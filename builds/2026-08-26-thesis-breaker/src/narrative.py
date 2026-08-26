"""Deterministic per-persona narrative text, with an optional Claude Haiku
polish layer. The deterministic template is always computed first and is
the only thing ever passed to the model -- Haiku is only allowed to
rephrase it, never to introduce a new fact or number. On any missing key,
network error, or malformed response, the deterministic text is returned
unchanged.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional

from .personas import PersonaScore

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"


def deterministic_text(persona: PersonaScore) -> str:
    if persona.score is None:
        return (
            f"{persona.name}: insufficient data was available to score this thesis "
            f"from this persona's perspective."
        )
    lines = [f"{persona.name} (severity {persona.score}/100):"]
    if persona.fired:
        lines.append("Triggered concerns:")
        lines.extend(f"  - {r.detail}" for r in persona.fired)
    if persona.not_fired:
        lines.append("Checked and did NOT trigger:")
        lines.extend(f"  - {r.detail}" for r in persona.not_fired)
    if persona.unavailable:
        lines.append("Could not evaluate:")
        lines.extend(f"  - {r.detail}" for r in persona.unavailable)
    return "\n".join(lines)


def _extract_text(response_json: dict) -> Optional[str]:
    try:
        content = response_json["content"]
        return content[0]["text"]
    except (KeyError, IndexError, TypeError):
        return None


def polish(persona: PersonaScore, api_key: Optional[str], base_text: Optional[str] = None,
           http_post=None) -> tuple[str, bool]:
    """Return (text, was_polished). Falls back to the deterministic text on
    any failure. `http_post(url, data_bytes, headers) -> (status, body_bytes)`
    is injectable for tests; defaults to a real urllib call.
    """
    fallback = base_text if base_text is not None else deterministic_text(persona)
    if not api_key:
        return fallback, False

    prompt = (
        f"Rewrite the following analyst note in {persona.name}'s voice, as tight "
        f"persona-appropriate prose. Do NOT invent any new number, fact, or claim "
        f"beyond what is stated below -- only rephrase.\n\n{fallback}"
    )
    payload = json.dumps({
        "model": ANTHROPIC_MODEL,
        "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    try:
        if http_post is not None:
            status, body = http_post(ANTHROPIC_URL, payload, headers)
        else:
            request = urllib.request.Request(ANTHROPIC_URL, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=15) as response:
                status, body = response.status, response.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return fallback, False

    if status != 200:
        return fallback, False
    try:
        response_json = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return fallback, False

    text = _extract_text(response_json)
    if not text:
        return fallback, False
    return text, True
