"""Optional Claude Haiku "why this worked" note for a top-scoring prompt.

Sends only the prompt text and already-computed aggregate features (score, task type, tool
names) — never raw tool output, file contents, or the rest of the transcript. When
``ANTHROPIC_API_KEY`` is unset, ``enrich_note`` returns a deterministic templated sentence
built from the same features and makes zero network calls.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Callable

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

Transport = Callable[[str, bytes, dict[str, str]], bytes]


def _default_transport(url: str, data: bytes, headers: dict[str, str]) -> bytes:
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 (fixed https URL)
        return response.read()


def _deterministic_fallback(prompt_text: str, task_type: str, score: int, tools_used: list[str]) -> str:
    outcome = "led to a strong outcome" if score >= 7 else "had a mixed outcome" if score >= 4 else "stalled or hit errors"
    tool_note = f" using {', '.join(tools_used[:3])}" if tools_used else ""
    return f"A {task_type} prompt that {outcome}{tool_note} (score {score}/10)."


def enrich_note(
    prompt_text: str,
    task_type: str,
    score: int,
    tools_used: list[str],
    api_key: str | None = None,
    transport: Transport = _default_transport,
) -> str:
    """Return a one-sentence note. Falls back deterministically with no key/no network call."""
    key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return _deterministic_fallback(prompt_text, task_type, score, tools_used)

    body = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 80,
        "messages": [
            {
                "role": "user",
                "content": (
                    "In one short sentence, explain why this coding prompt likely worked well, "
                    "given only these facts (do not invent details beyond them):\n"
                    f"Prompt: {prompt_text}\n"
                    f"Task type: {task_type}\n"
                    f"Effectiveness score (0-10): {score}\n"
                    f"Tools used afterward: {', '.join(tools_used) if tools_used else 'none'}"
                ),
            }
        ],
    }
    headers = {
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
    }

    try:
        raw = transport(ANTHROPIC_URL, json.dumps(body).encode("utf-8"), headers)
        parsed = json.loads(raw)
        parts = parsed.get("content", [])
        for block in parts:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "").strip()
                if text:
                    return text
        return _deterministic_fallback(prompt_text, task_type, score, tools_used)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
        return _deterministic_fallback(prompt_text, task_type, score, tools_used)
