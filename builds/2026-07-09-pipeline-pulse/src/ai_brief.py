"""Optional Claude-generated "what needs attention" briefing, with a deterministic
fallback template. Only aggregate stats are ever sent — no build titles/notes text,
no repo contents.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Callable

from pipeline_stats import Summary

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"
TIMEOUT_SECONDS = 20

Fetcher = Callable[[str, bytes, dict], bytes]


def _default_fetch(url: str, payload: bytes, headers: dict) -> bytes:
    request = urllib.request.Request(url, data=payload, method="POST", headers=headers)
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def deterministic_brief(summary: Summary) -> str:
    """Rule-based fallback briefing built entirely from aggregate numbers."""
    parts = []
    if summary["backlog_count"] > 0:
        oldest = summary["oldest_unmerged"]
        oldest_desc = (
            f"the oldest, \"{oldest['title']}\" ({oldest['date']}), has been waiting "
            f"{oldest['backlog_days']} days"
            if oldest
            else "age could not be determined for all of them"
        )
        parts.append(
            f"{summary['backlog_count']} of {summary['total']} nightly builds "
            f"({summary['backlog_pct']:.0f}%) are still unmerged; {oldest_desc}."
        )
    else:
        parts.append(f"All {summary['total']} nightly builds are merged into the default branch.")

    if summary["rating_coverage_pct"] < 50:
        parts.append(
            f"Only {summary['rated_count']} builds ({summary['rating_coverage_pct']:.0f}%) "
            "have been rated, which limits how well the lottery weighting can learn your preferences."
        )
    elif summary["average_rating"] is not None:
        parts.append(f"Average rating across rated builds is {summary['average_rating']:.1f}/10.")

    return " ".join(parts)


def generate_brief(summary: Summary, fetch: Fetcher = _default_fetch) -> str:
    """Return an AI-generated briefing when ANTHROPIC_API_KEY is set and the call
    succeeds; otherwise return the deterministic fallback. Never raises."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return deterministic_brief(summary)

    aggregate_only = {
        "total": summary["total"],
        "merged_count": summary["merged_count"],
        "backlog_count": summary["backlog_count"],
        "backlog_pct": round(summary["backlog_pct"], 1),
        "oldest_unmerged_days": (
            summary["oldest_unmerged"]["backlog_days"] if summary["oldest_unmerged"] else None
        ),
        "rating_coverage_pct": round(summary["rating_coverage_pct"], 1),
        "average_rating": summary["average_rating"],
        "category_distribution": summary["category_distribution"],
    }
    prompt = (
        "Here are aggregate stats about a personal AI nightly-build pipeline (no titles, "
        "no personal data):\n"
        f"{json.dumps(aggregate_only)}\n\n"
        "Write a single short paragraph (2-4 sentences, plain English, no markdown) telling "
        "the owner what needs their attention most right now."
    )
    payload = json.dumps(
        {"model": MODEL, "max_tokens": 300, "messages": [{"role": "user", "content": prompt}]}
    ).encode("utf-8")
    headers = {
        "content-type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    try:
        body = fetch(API_URL, payload, headers)
        text = json.loads(body)["content"][0]["text"].strip()
        return text or deterministic_brief(summary)
    except (urllib.error.URLError, TimeoutError, ValueError, OSError, KeyError, IndexError):
        return deterministic_brief(summary)
