"""Optional Claude Haiku 'what to fix first' briefing.

The prompt is built exclusively from already-computed aggregate counts and
dependency/repo *names* — never file contents, never a full requirements
list. With no ANTHROPIC_API_KEY this module makes zero network calls and
returns a deterministic template built from the same aggregate numbers.
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional

from .drift import DriftEntry
from .http import Transport, default_transport

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-haiku-4-5-20251001"


def _deterministic_briefing(drift_entries: List[DriftEntry], repo_summary: Dict[str, dict]) -> str:
    if not drift_entries:
        sentence = "No cross-repo dependency drift detected in the latest sync."
    else:
        top = drift_entries[:3]
        named = ", ".join(f"{e['dependency']} ({e['severity']})" for e in top)
        sentence = (
            f"{len(drift_entries)} dependencies are pinned inconsistently across your repos. "
            f"Highest priority: {named}."
        )
    worst_repo = None
    worst_major_count = 0
    for repo, stats in repo_summary.items():
        if stats["major_count"] > worst_major_count:
            worst_repo = repo
            worst_major_count = stats["major_count"]
    if worst_repo:
        sentence += (
            f" {worst_repo} has the most major-version-behind dependencies ({worst_major_count})."
        )
    return sentence


def build_briefing(
    drift_entries: List[DriftEntry],
    repo_summary: Dict[str, dict],
    api_key: Optional[str] = None,
    transport: Transport = default_transport,
) -> str:
    """Build the fix-first briefing, falling back to a deterministic
    template on a missing key, network error, or malformed response."""
    fallback = _deterministic_briefing(drift_entries, repo_summary)
    if not api_key:
        return fallback

    top = drift_entries[:5]
    summary_payload = {
        "drifted_dependency_count": len(drift_entries),
        "top_drifted": [
            {"dependency": e["dependency"], "ecosystem": e["ecosystem"], "severity": e["severity"]}
            for e in top
        ],
        "repos_with_major_staleness": [
            repo for repo, stats in repo_summary.items() if stats["major_count"] > 0
        ],
    }
    prompt = (
        "You are a terse engineering assistant. Given this aggregate dependency-drift "
        "summary (dependency names, ecosystems, and severities only — no file contents "
        "or full dependency lists), write 2-3 sentences on what to fix first and why.\n\n"
        f"{json.dumps(summary_payload)}"
    )
    body = json.dumps(
        {"model": _MODEL, "max_tokens": 200, "messages": [{"role": "user", "content": prompt}]}
    ).encode("utf-8")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    try:
        status, response_body = transport(_ANTHROPIC_URL, headers, method="POST", data=body)
    except Exception:
        return fallback
    if status != 200:
        return fallback
    try:
        data = json.loads(response_body.decode("utf-8"))
        content = data.get("content")
        if isinstance(content, list) and content and "text" in content[0]:
            text = content[0]["text"].strip()
            return text or fallback
    except (json.JSONDecodeError, AttributeError, IndexError, KeyError, TypeError, UnicodeDecodeError):
        return fallback
    return fallback
