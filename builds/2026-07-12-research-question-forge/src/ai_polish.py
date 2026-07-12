"""Optional Claude polish pass for a generated question skeleton.

Uses urllib.request directly (no SDK dependency) so the tool has zero
third-party runtime dependencies. Falls back to a deterministic template
whenever ANTHROPIC_API_KEY is unset, the network call fails, or the
response cannot be parsed as expected -- the tool must always produce a
usable result.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
REQUEST_TIMEOUT_SECONDS = 20


def _deterministic_template(question: dict[str, str]) -> str:
    return (
        f"**Research Question:** {question['skeleton']}\n\n"
        f"**Hypothesis:** {question['rationale']}\n\n"
        f"**Testability:** {question['testability'].replace('-', ' ').capitalize()}."
    )


def _build_prompt(question: dict[str, str]) -> str:
    return (
        "You are helping a neuroscience researcher turn a research-question "
        "skeleton into a short, grant-ready paragraph. Given the skeleton and "
        "rationale below, write: (1) a single polished research question "
        "sentence, (2) a one-sentence testable hypothesis, (3) a one-sentence "
        "justification. Keep it under 120 words total, plain scientific prose, "
        "no headers, no markdown.\n\n"
        f"Skeleton: {question['skeleton']}\n"
        f"Rationale: {question['rationale']}\n"
        f"Testability: {question['testability']}"
    )


def polish_question(question: dict[str, str], api_key: str | None = None) -> tuple[str, str]:
    """Return (polished_text, source) where source is 'claude' or 'template'."""
    api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _deterministic_template(question), "template"

    payload = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": _build_prompt(question)}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        text_blocks = body.get("content", [])
        text = "".join(block.get("text", "") for block in text_blocks if block.get("type") == "text")
        text = text.strip()
        if not text:
            return _deterministic_template(question), "template"
        return text, "claude"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, KeyError, OSError):
        return _deterministic_template(question), "template"
