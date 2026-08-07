"""Optional Claude Haiku enrichment of commit decision summaries.

Zero network calls when ANTHROPIC_API_KEY is unset — the deterministic
summary from scorer.py is always the fallback.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MODEL = "claude-haiku-4-5"


class EnrichmentError(Exception):
    """Raised when the Anthropic API call fails; callers should keep the fallback summary."""


def is_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _build_prompt(commit: dict[str, Any]) -> str:
    subject = commit.get("subject", "") or ""
    body = commit.get("body", "") or ""
    files_changed = commit.get("files_changed", 0) or 0
    insertions = commit.get("insertions", 0) or 0
    deletions = commit.get("deletions", 0) or 0

    return (
        "Rewrite this git commit into one clear plain-English sentence describing "
        "what changed and why, for someone scanning a project history months later. "
        "No preamble, no quotes, just the sentence.\n\n"
        f"Subject: {subject}\n"
        f"Body: {body or '(no body)'}\n"
        f"Files changed: {files_changed}, insertions: {insertions}, deletions: {deletions}"
    )


def enrich_commit(commit: dict[str, Any], api_key: str | None = None) -> str:
    """Call Claude Haiku to produce a refined summary. Raises EnrichmentError on failure."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise EnrichmentError("ANTHROPIC_API_KEY is not set")

    payload = {
        "model": MODEL,
        "max_tokens": 200,
        "messages": [{"role": "user", "content": _build_prompt(commit)}],
    }
    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=data,
        method="POST",
        headers={
            "x-api-key": key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise EnrichmentError(f"Anthropic API request failed: {exc}") from exc

    content = body.get("content", [])
    for block in content:
        if block.get("type") == "text":
            text = block.get("text", "").strip()
            if text:
                return text

    raise EnrichmentError("Anthropic API response contained no text content")
