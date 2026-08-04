"""Optional Claude Haiku season-readiness briefing.

Makes zero network calls when no ANTHROPIC_API_KEY is available - the
deterministic template path below is the unconditional fallback, exercised
whenever the API call fails or is skipped entirely.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"
REQUEST_TIMEOUT_SECONDS = 20
MAX_TOKENS = 300


def build_prompt(site_name: str, task_summaries: list, boating_score_today: Optional[float]) -> str:
    lines = [f"Site: {site_name}"]
    if boating_score_today is not None:
        lines.append(f"Today's boating comfort score: {boating_score_today}/100")
    lines.append("Task readiness this week:")
    for summary in task_summaries:
        lines.append(f"- {summary}")
    lines.append(
        "\nWrite a short (2-4 sentence), plain, practical briefing for the cottage/boat "
        "owner summarizing what's actionable this week and what to wait on. No preamble."
    )
    return "\n".join(lines)


def _call_anthropic(prompt: str, api_key: str) -> str:
    payload = json.dumps({
        "model": ANTHROPIC_MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    content = body.get("content") or []
    text_parts = [block.get("text", "") for block in content if block.get("type") == "text"]
    text = "".join(text_parts).strip()
    if not text:
        raise ValueError("Anthropic response contained no text content")
    return text


def deterministic_briefing(site_name: str, task_summaries: list) -> str:
    if not task_summaries:
        return (
            f"No active tasks configured for {site_name}. "
            "Add tasks with `add-task` to get readiness scoring."
        )
    ready = [s for s in task_summaries if "ready_now" in s or "ready_soon" in s]
    blocked = [s for s in task_summaries if "not_ready" in s or "overdue" in s]
    parts = [f"Season status for {site_name}:"]
    if ready:
        parts.append(f"{len(ready)} task(s) are ready or ready soon this week.")
    if blocked:
        parts.append(f"{len(blocked)} task(s) are blocked or overdue — check the readiness breakdown below.")
    if not ready and not blocked:
        parts.append("All active tasks are currently off-season.")
    return " ".join(parts)


def generate_briefing(site_name: str, task_summaries: list,
                       boating_score_today: Optional[float] = None,
                       api_key: Optional[str] = None):
    """Returns (text, source) where source is "ai" or "template".

    Makes zero network calls whenever no API key is available (neither
    passed explicitly nor present in ANTHROPIC_API_KEY).
    """
    key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return deterministic_briefing(site_name, task_summaries), "template"

    prompt = build_prompt(site_name, task_summaries, boating_score_today)
    try:
        text = _call_anthropic(prompt, key)
        return text, "ai"
    except (urllib.error.URLError, ValueError, json.JSONDecodeError, TimeoutError, OSError):
        return deterministic_briefing(site_name, task_summaries), "template"
