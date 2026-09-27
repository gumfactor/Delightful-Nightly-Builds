"""Optional one-paragraph Claude Haiku briefing over aggregate sync counts.

Only aggregate bucket totals and a trend direction are ever sent — never
an item title, URL, or id from either Teamwork or Coda. With no
ANTHROPIC_API_KEY set, a deterministic template is returned and no
network call is attempted.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Callable, Optional

from store import SyncRun

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"

HttpPost = Callable[[str, dict[str, str], bytes], bytes]


class BriefingError(RuntimeError):
    pass


def _default_http_post(url: str, headers: dict[str, str], body: bytes) -> bytes:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise BriefingError(f"Anthropic API returned status {exc.code}") from exc


def _build_aggregate_summary(latest: SyncRun, history_runs: list[SyncRun]) -> dict:
    if len(history_runs) >= 2:
        previous_gap = history_runs[-2].gap_size
        trend = (
            "improving" if latest.gap_size < previous_gap
            else "worsening" if latest.gap_size > previous_gap
            else "unchanged"
        )
    else:
        trend = "first_run"
    return {
        "matched_ok": latest.matched_ok,
        "status_conflict": latest.status_conflict,
        "teamwork_only": latest.teamwork_only,
        "coda_only": latest.coda_only,
        "total_runs": len(history_runs),
        "trend": trend,
    }


def _deterministic_briefing(summary: dict) -> str:
    gap = summary["status_conflict"] + summary["teamwork_only"] + summary["coda_only"]
    trend_phrase = {
        "improving": "the gap has shrunk since the last sync",
        "worsening": "the gap has grown since the last sync",
        "unchanged": "the gap is unchanged since the last sync",
        "first_run": "this is the first recorded sync, so there's no trend yet",
    }[summary["trend"]]
    return (
        f"Parity found {summary['matched_ok']} items in sync, {gap} out of sync "
        f"({summary['status_conflict']} status conflicts, {summary['teamwork_only']} Teamwork-only, "
        f"{summary['coda_only']} Coda-only) across {summary['total_runs']} recorded sync run(s) — "
        f"{trend_phrase}."
    )


def generate_briefing(
    latest: SyncRun,
    history_runs: list[SyncRun],
    api_key: Optional[str] = None,
    http_post: Optional[HttpPost] = None,
) -> str:
    """Return a one-paragraph briefing, using Claude Haiku if a key is available."""
    api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    summary = _build_aggregate_summary(latest, history_runs)

    if not api_key:
        return _deterministic_briefing(summary)

    poster = http_post or _default_http_post
    prompt = (
        "You are summarizing a personal task-sync report in one short paragraph "
        "(2-3 sentences), plain and direct, no headers or bullet points. "
        "Here are the aggregate counts (no task names are included): "
        f"{json.dumps(summary)}"
    )
    body = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    try:
        raw_response = poster(ANTHROPIC_URL, headers, body)
        parsed = json.loads(raw_response)
        return parsed["content"][0]["text"].strip()
    except (BriefingError, KeyError, IndexError, json.JSONDecodeError):
        return _deterministic_briefing(summary)
