"""Optional Claude Haiku narrative layer for ItemScope.

Only aggregated per-item statistics are ever sent — never raw student
responses, names, or IDs. Always falls back to a deterministic
template-based suggestion when no API key is set or the call fails, so the
tool is fully functional offline.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from itemscope.stats import ItemStats

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"


def _template_suggestion(item: ItemStats) -> str:
    parts = []
    if "too_easy" in item.flags:
        parts.append(
            "Nearly everyone answered this correctly — consider retiring it or "
            "using it only as a warm-up item; it isn't distinguishing who "
            "learned the material."
        )
    if "too_hard" in item.flags:
        parts.append(
            "Very few students answered this correctly — check the wording for "
            "ambiguity or a mismatch with what was actually taught before "
            "assuming a knowledge gap."
        )
    if "negative_discrimination" in item.flags:
        parts.append(
            "Stronger students did worse on this item than weaker students — "
            "this is a strong signal the item is miskeyed or genuinely "
            "confusing; review the answer key first."
        )
    elif "poor_discrimination" in item.flags:
        parts.append(
            "This item barely distinguishes high- from low-scoring students — "
            "consider tightening the wording or replacing a weak distractor."
        )
    if "non_functioning_distractor" in item.flags:
        parts.append(
            "At least one wrong answer choice was never chosen by either the "
            "top or bottom scorers — it isn't pulling its weight as a "
            "distractor and could be replaced with a more plausible option."
        )
    if "reversed_distractor_pull" in item.flags:
        parts.append(
            "A wrong answer choice was picked more often by top scorers than "
            "bottom scorers — double check that option isn't defensible or "
            "that the key is correct."
        )
    if not parts:
        return "No issues detected for this item."
    return " ".join(parts)


def generate_item_suggestion(item: ItemStats, api_key: str | None = None) -> tuple[str, str]:
    """Return (suggestion_text, source) where source is 'ai' or 'template'."""
    template = _template_suggestion(item)
    key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return template, "template"

    payload = {
        "item_id": item.item_id,
        "p_value": round(item.p_value, 3),
        "discrimination": round(item.discrimination, 3) if item.discrimination is not None else None,
        "flags": item.flags,
    }
    prompt = (
        "You are helping a university instructor improve an exam item. Here are "
        "the aggregated psychometric statistics for one item (no student data "
        f"is included): {json.dumps(payload)}. In 2-3 sentences, give a specific, "
        "actionable suggestion for what to do with this item."
    )
    body = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
        text = "".join(
            block.get("text", "") for block in result.get("content", []) if block.get("type") == "text"
        )
        if text.strip():
            return text.strip(), "ai"
        return template, "template"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, KeyError):
        return template, "template"
