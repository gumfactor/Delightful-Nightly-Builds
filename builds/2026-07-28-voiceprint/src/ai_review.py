"""Optional Claude Haiku holistic second opinion on the worst-scoring paragraphs.

Runs only when the caller supplies an API key (from the runtime environment's
ANTHROPIC_API_KEY, never hardcoded). Falls back to a deterministic,
heuristics-only template whenever no key is present or the call fails for any
reason — the tool is always fully functional with zero configuration. Only
the user's own draft text is ever sent; no third-party personal data.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable, Optional

from . import heuristics

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_PARAGRAPHS = 3

RequestFn = Callable[[str, bytes, dict], bytes]


def _default_request_fn(url: str, data: bytes, headers: dict) -> bytes:
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def _build_prompt(paragraphs: list[str]) -> str:
    numbered = "\n\n".join(f"[{i + 1}] {p}" for i, p in enumerate(paragraphs))
    return (
        "You are a writing coach helping an author remove AI-sounding, "
        "formulaic prose from their own draft. For each numbered paragraph "
        "below, respond with a JSON array (and nothing else) of objects with "
        "keys 'diagnosis' (one sentence explaining what reads as formulaic) "
        "and 'rewrite' (a rewritten version in a more natural, human voice). "
        "Return exactly one object per paragraph, in order.\n\n" + numbered
    )


def call_claude_for_review(
    paragraphs: list[str],
    api_key: str,
    request_fn: RequestFn = _default_request_fn,
    model: str = DEFAULT_MODEL,
) -> Optional[dict]:
    if not paragraphs:
        return None
    payload = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": _build_prompt(paragraphs)}],
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "content-type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    try:
        raw = request_fn(ANTHROPIC_API_URL, data, headers)
    except (urllib.error.URLError, OSError, TimeoutError):
        return None

    try:
        parsed = json.loads(raw)
        text = parsed["content"][0]["text"]
        items = json.loads(text)
        if not isinstance(items, list) or len(items) != len(paragraphs):
            raise ValueError("unexpected item count")
        for item in items:
            if "diagnosis" not in item or "rewrite" not in item:
                raise ValueError("missing keys")
    except (KeyError, IndexError, ValueError, TypeError, json.JSONDecodeError):
        return None

    return {
        "source": "ai",
        "items": [
            {
                "paragraph": paragraphs[i],
                "diagnosis": items[i]["diagnosis"],
                "rewrite": items[i]["rewrite"],
            }
            for i in range(len(paragraphs))
        ],
    }


def _deterministic_advice_for_paragraph(paragraph: str, breakdown: dict) -> str:
    local_hits = heuristics.find_ai_tell_phrases(paragraph)
    if local_hits:
        phrases = sorted({hit["phrase"] for hit in local_hits})
        return (
            f"Contains {len(local_hits)} AI-tell phrase(s) ({', '.join(phrases[:4])}) "
            "— try replacing with more specific, concrete language."
        )
    worst_category = max(breakdown, key=lambda key: breakdown[key], default=None)
    if worst_category and breakdown.get(worst_category, 0) > 0:
        label = worst_category.replace("_", " ")
        return f"No AI-tell phrases here, but the document's dominant issue is {label} — check this paragraph for that pattern."
    return "No flagged patterns detected in this paragraph."


def deterministic_fallback(paragraphs: list[str], breakdown: dict) -> list[dict]:
    return [
        {
            "paragraph": paragraph,
            "diagnosis": _deterministic_advice_for_paragraph(paragraph, breakdown),
            "rewrite": None,
        }
        for paragraph in paragraphs
    ]


def get_review(
    paragraphs: list[str],
    breakdown: dict,
    api_key: Optional[str] = None,
    request_fn: RequestFn = _default_request_fn,
    model: str = DEFAULT_MODEL,
) -> dict:
    limited = paragraphs[:MAX_PARAGRAPHS]
    if api_key:
        result = call_claude_for_review(
            limited, api_key, request_fn=request_fn, model=model
        )
        if result is not None:
            return result
    return {"source": "fallback", "items": deterministic_fallback(limited, breakdown)}


def pick_worst_paragraphs(paragraphs: list[str], limit: int = MAX_PARAGRAPHS) -> list[str]:
    """Rank paragraphs by their own AI-tell hit density and return the worst."""
    if not paragraphs:
        return []
    scored = []
    for paragraph in paragraphs:
        hits = heuristics.find_ai_tell_phrases(paragraph)
        words = max(1, heuristics.word_count(paragraph))
        density = len(hits) / words
        scored.append((density, paragraph))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [paragraph for _, paragraph in scored[:limit]]
