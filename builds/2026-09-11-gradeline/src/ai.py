"""Optional Claude Haiku feedback drafting.

Fires only when the caller explicitly requests it (a truthy `api_key`) and
falls back to a deterministic template otherwise. The prompt is built from
only the criterion's own name/description and the submission's own text —
the student's identifier/filename is never passed to this module at all, so
it cannot leak into a prompt by construction. Any missing key, network
error, or malformed response returns None so the caller uses the
deterministic fallback, making zero network calls in that path.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

Transport = Callable[[str, dict], bytes]

_SYSTEM_PROMPT = (
    "You are a teaching assistant drafting one short, specific feedback "
    "paragraph (3-5 sentences) for a single rubric criterion on a student's "
    "written submission. Quote or paraphrase specific evidence from the "
    "submission text. Do not assign or imply a numeric score — scoring is "
    "handled separately. Do not address the student by name (you were not "
    "given one). Return only the feedback paragraph, no preamble."
)


def default_transport(url: str, payload: dict) -> bytes:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "x-api-key": os.environ.get("ANTHROPIC_API_KEY", ""),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 (fixed https host)
        return response.read()


def deterministic_feedback(
    criterion_name: str, hits: int, min_hits: int, score: float, max_points: float
) -> str:
    if min_hits <= 0:
        coverage = "not evaluated by keyword coverage (manual review criterion)"
    elif hits >= min_hits:
        coverage = f"met the expected keyword coverage ({hits}/{min_hits} target terms found)"
    else:
        coverage = f"fell short of the expected keyword coverage ({hits}/{min_hits} target terms found)"
    return (
        f"[Deterministic] '{criterion_name}': {coverage}. Score: {score}/{max_points}. "
        "Enable --ai with an ANTHROPIC_API_KEY set for a grounded narrative feedback draft."
    )


def draft_feedback(
    criterion_name: str,
    criterion_description: str,
    submission_text: str,
    api_key: str,
    transport: Transport = default_transport,
) -> str | None:
    """Returns AI-drafted feedback text, or None on any failure (caller falls
    back to `deterministic_feedback`). `submission_text` is the only
    identifying-content field sent — no student name or filename is ever
    a parameter of this function."""
    if not api_key:
        return None
    user_content = (
        f"Rubric criterion: {criterion_name}\n"
        f"Criterion description: {criterion_description}\n\n"
        f"Submission text:\n{submission_text}"
    )
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 300,
        "system": _SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_content}],
    }
    try:
        raw = transport(ANTHROPIC_URL, payload)
    except (urllib.error.HTTPError, urllib.error.URLError):
        return None
    try:
        response = json.loads(raw)
        text = response["content"][0]["text"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None
    stripped = text.strip()
    return stripped or None
