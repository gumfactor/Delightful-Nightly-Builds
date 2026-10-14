"""Optional Claude summary of the analysis. Sends only aggregate CI metrics, no secrets or source."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Callable

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-5-5"
Post = Callable[[str, dict[str, str], bytes], bytes]


def _urllib_post(url: str, headers: dict[str, str], body: bytes) -> bytes:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - https only
        return response.read()


def build_prompt(report: dict) -> str:
    compact = {
        "summary": report["summary"],
        "top_workflows": report["workflows"][:8],
        "top_steps": report["steps"][:8],
        "findings": report["findings"][:10],
    }
    return (
        "You are reviewing GitHub Actions CI metrics for one developer's repositories. "
        "Write a direct briefing of at most 150 words: the three highest-leverage fixes in order, "
        "each with the repo/workflow and the expected minutes saved. Use only the data given; "
        "do not invent numbers. No filler.\n\n" + json.dumps(compact, default=str)
    )


def summarize(report: dict, api_key: str | None = None, post: Post = _urllib_post) -> str | None:
    """Return a summary, or None when no key is set or the call fails (report still works)."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 500,
        "messages": [{"role": "user", "content": build_prompt(report)}],
    }).encode("utf-8")
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    try:
        data = json.loads(post(ANTHROPIC_URL, headers, payload))
        return "".join(block.get("text", "") for block in data.get("content", [])).strip() or None
    except (urllib.error.URLError, ValueError, OSError):
        return None
