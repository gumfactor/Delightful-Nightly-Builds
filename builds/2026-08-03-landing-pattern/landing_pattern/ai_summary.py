"""Optional one-line AI notes for blocked PRs via the Claude API.

Uses raw urllib (no SDK dependency), matching this repo's stdlib-only
convention. Makes zero network calls when no ANTHROPIC_API_KEY is set.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5"

_DETERMINISTIC_TEMPLATES: dict[str, str] = {
    "conflict": "Merge conflict against the base branch — rebase or merge the base branch in before this can land.",
    "ci_failing": "CI is failing — check the latest run and fix or re-run it before merging.",
    "changes_requested": "A reviewer requested changes — address the review feedback before merging.",
    "ci_pending": "CI is still running — wait for it to finish before merging.",
    "awaiting_review": "No review yet — request a review to move this forward.",
    "behind_base": "This branch is behind the base branch — update it before merging to avoid surprises.",
    "unknown": "Readiness could not be determined from the available PR data — check it manually.",
}


def deterministic_note(label: str) -> str:
    """Template fallback note for a blocked-PR label. Always available, no network call."""
    return _DETERMINISTIC_TEMPLATES.get(label, _DETERMINISTIC_TEMPLATES["unknown"])


def _call_claude(prompt: str, api_key: str, http_post: Any) -> str:
    """POST a single-turn request to the Messages API. Raises on any failure."""
    body = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 100,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    response = http_post(request)
    parsed = json.loads(response.read().decode("utf-8"))
    for block in parsed.get("content", []):
        if block.get("type") == "text":
            return block["text"].strip()
    raise ValueError("No text block in Claude response")


def summarize_blocked_pr(
    pr: dict[str, Any],
    api_key: str | None,
    http_post: Any = urllib.request.urlopen,
) -> str:
    """One-sentence plain-English note on what to do about a blocked PR.

    Sends only title, blocking label, changed-file count, and age — never
    diff content. Falls back to a deterministic template when no API key is
    set or the call fails; makes zero network calls without a key.
    """
    if not api_key:
        return deterministic_note(pr["label"])

    prompt = (
        "In one plain-English sentence, tell a developer what to do about this "
        "blocked pull request. Be specific and actionable, no preamble.\n\n"
        f"Title: {pr['title']}\n"
        f"Blocking reason: {pr['label']}\n"
        f"Changed files: {len(pr.get('files', []))}\n"
        f"Age: {pr['age_days']} days open\n"
    )
    try:
        return _call_claude(prompt, api_key, http_post)
    except (urllib.error.URLError, ValueError, KeyError, json.JSONDecodeError):
        return deterministic_note(pr["label"])
