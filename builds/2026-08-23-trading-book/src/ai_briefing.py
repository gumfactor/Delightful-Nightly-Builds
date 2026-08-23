"""Optional Claude Haiku portfolio note.

Uses `urllib.request` directly rather than the `anthropic` package (which
this build container cannot install), matching the pattern used across
this catalog's other optional-AI builds. Falls back to a deterministic
template with zero network calls whenever ANTHROPIC_API_KEY is unset.

`summary` is always an aggregate-only dict — day-over-day percent change,
asset-class allocation percentages, and top movers by percent change —
never a dollar figure, account ID, or account number.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MODEL = "claude-haiku-4-5-20251001"


def build_briefing(summary: dict[str, Any], api_key: str | None = None) -> str:
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _deterministic_briefing(summary)

    try:
        return _call_anthropic(summary, api_key)
    except Exception:
        return _deterministic_briefing(summary)


def _call_anthropic(summary: dict[str, Any], api_key: str) -> str:
    prompt = _build_prompt(summary)
    payload = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        body = json.loads(response.read().decode("utf-8"))

    text = body["content"][0]["text"].strip()
    if not text:
        raise ValueError("empty response from Anthropic API")
    return text


def _build_prompt(summary: dict[str, Any]) -> str:
    movers = ", ".join(
        f"{m['symbol']} ({m['pct_change']:+.1f}%)" for m in summary.get("top_movers", [])
    ) or "none"
    allocation = ", ".join(
        f"{k}: {v:.0f}%" for k, v in summary.get("allocation_pct", {}).items()
    ) or "no positions"

    return (
        "You are a terse portfolio note-writer for a personal investing dashboard. "
        "Write one short plain-English paragraph (2-3 sentences, no markdown, no dollar "
        "figures, no account numbers) giving context on today's portfolio activity. "
        f"Day-over-day net liquidation change: {summary.get('day_change_pct', 0.0):+.2f}%. "
        f"Asset-class allocation: {allocation}. "
        f"Top movers by percent change: {movers}."
    )


def _deterministic_briefing(summary: dict[str, Any]) -> str:
    change = summary.get("day_change_pct", 0.0)
    direction = "up" if change > 0 else "down" if change < 0 else "flat"
    movers = summary.get("top_movers", [])
    if movers:
        top = movers[0]
        mover_note = f" {top['symbol']} moved the most, {top['pct_change']:+.1f}%."
    else:
        mover_note = ""
    return (
        f"Net liquidation is {direction} {abs(change):.2f}% since the last snapshot."
        f"{mover_note} Set ANTHROPIC_API_KEY for an AI-generated note instead of this template."
    )
