"""Optional Claude Haiku prose polish for a deterministically-assembled draft.

Sends only the already-assembled draft markdown — never raw CSV rows or any
personal data. Falls back unconditionally to the original draft on a missing
API key, network error, or malformed response, so the tool is always fully
functional with zero network calls when no key is set.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"
TIMEOUT_SECONDS = 20


def polish(draft_markdown: str, piece_type: str, api_key: str | None = None) -> tuple[str, bool]:
    """Return (text, was_polished). was_polished is False on any fallback path."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return draft_markdown, False

    prompt = (
        "Rewrite the following Canadian small-business editorial draft "
        f"(a '{piece_type}' piece) into more natural, non-repetitive prose. "
        "Preserve every business name, category, location, and factual claim "
        "exactly as given — do not invent, omit, or exaggerate anything. Keep "
        "roughly the same length and paragraph structure. Return only the "
        "rewritten text, no preamble.\n\n" + draft_markdown
    )

    payload = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=payload,
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        text = body["content"][0]["text"]
        if not isinstance(text, str) or not text.strip():
            return draft_markdown, False
        return text, True
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        OSError,
    ):
        return draft_markdown, False
