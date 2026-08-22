"""Optional Claude Haiku 'This Week's Admin Briefing', with an unconditional
deterministic fallback.

Only aggregate urgency-bucket counts and item titles/categories are ever sent
to the API — never raw RDAP/TLS payloads, registrar account details, or any
personally identifying information. Makes zero network calls when
ANTHROPIC_API_KEY is unset.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"
TIMEOUT_SECONDS = 20


def _deterministic_briefing(items: list[dict[str, Any]]) -> str:
    overdue = [item for item in items if item["urgency"] == "Overdue"]
    this_week = [item for item in items if item["urgency"] == "Due This Week"]
    this_month = [item for item in items if item["urgency"] == "Due This Month"]

    if not overdue and not this_week and not this_month:
        return "Nothing needs attention this week — every tracked domain, certificate, and renewal is Upcoming or Healthy."

    parts = []
    if overdue:
        names = ", ".join(item["title"] for item in overdue[:3])
        parts.append(f"{len(overdue)} item(s) already overdue ({names}) — handle these first.")
    if this_week:
        names = ", ".join(item["title"] for item in this_week[:3])
        parts.append(f"{len(this_week)} due within 7 days ({names}).")
    if this_month:
        parts.append(f"{len(this_month)} due within the next 30 days — worth a glance now to avoid a scramble later.")
    return " ".join(parts)


def generate_briefing(items: list[dict[str, Any]]) -> tuple[str, bool]:
    """Return (briefing_text, used_ai). Falls back to a deterministic summary on any failure.

    `items` is a list of {"title": str, "category": str, "urgency": str} dicts —
    the aggregate view only, never raw lookup payloads.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _deterministic_briefing(items), False

    bucket_counts: dict[str, int] = {}
    for item in items:
        bucket_counts[item["urgency"]] = bucket_counts.get(item["urgency"], 0) + 1

    urgent_titles = [item["title"] for item in items if item["urgency"] in ("Overdue", "Due This Week")]

    prompt = (
        "You are writing a short (<=3 sentence) admin briefing for a solo founder/researcher "
        "reviewing their domain, SSL certificate, and administrative renewal tracker. "
        f"Urgency bucket counts: {bucket_counts}. "
        f"Items due this week or already overdue: {', '.join(urgent_titles) if urgent_titles else 'none'}. "
        "Summarize what needs attention and in what order. No greeting, no sign-off, plain text only."
    )

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
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        text = body["content"][0]["text"].strip()
        if text:
            return text, True
        return _deterministic_briefing(items), False
    except Exception:
        return _deterministic_briefing(items), False
