"""Optional Claude Haiku "coach note" — one paragraph of behavioral
observation built strictly from aggregate streak numbers. Never sends a
date, a manual-checkin note, or a Garmin activity title. Falls back to a
deterministic template on any missing key or request failure, so the
dashboard always has real content and the tool never requires a network
call to be useful.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

_MODEL = "claude-haiku-4-5-20251001"
_API_URL = "https://api.anthropic.com/v1/messages"
_TIMEOUT_SECONDS = 20


@dataclass(frozen=True)
class CoachNote:
    text: str
    source: str  # "ai" or "deterministic"


def _aggregate_summary(habit_stats: list[dict]) -> list[dict]:
    """Strip habit_stats down to the aggregate-only fields sent to the API
    (or used by the deterministic template): no dates, no notes, no
    activity titles.
    """
    return [
        {
            "name": h["name"],
            "cadence": h["cadence"],
            "current_streak": h["current_streak"],
            "longest_streak": h["longest_streak"],
            "completion_rate": round(h["completion_rate"], 2),
        }
        for h in habit_stats
    ]


def _deterministic_note(habit_stats: list[dict]) -> str:
    if not habit_stats:
        return "No habits configured yet — add one to habits.json to get started."

    best = max(habit_stats, key=lambda h: h["current_streak"])
    weakest = min(habit_stats, key=lambda h: h["completion_rate"])

    parts = []
    if best["current_streak"] > 0:
        unit = "week" if best["cadence"] == "weekly" else "day"
        plural = "s" if best["current_streak"] != 1 else ""
        parts.append(
            f"{best['name']} is your strongest thread right now, at a "
            f"{best['current_streak']}-{unit}{plural} streak."
        )
    else:
        parts.append("No habit currently has an active streak.")

    if weakest["completion_rate"] < 0.5:
        parts.append(
            f"{weakest['name']} has the lowest consistency "
            f"({weakest['completion_rate']:.0%} of the period covered) — "
            "that's the one most likely to need a deliberate nudge this week."
        )
    else:
        parts.append("Every habit is holding at least 50% consistency over the period shown.")

    return " ".join(parts)


def _call_anthropic(summary: list[dict], api_key: str) -> str:
    prompt = (
        "You are a behavioral-science-informed habit coach. Given this "
        "aggregate JSON of habit streak statistics (no personal details, "
        "just names and numbers), write one short paragraph (3-4 sentences) "
        "of genuinely useful observation: what's working, what's slipping, "
        "and one concrete, specific suggestion. No greetings, no fluff.\n\n"
        f"{json.dumps(summary)}"
    )
    payload = json.dumps(
        {
            "model": _MODEL,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        _API_URL,
        data=payload,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        body = json.loads(response.read().decode("utf-8"))

    return "".join(block.get("text", "") for block in body.get("content", [])).strip()


def generate_coach_note(habit_stats: list[dict], api_key: str | None) -> CoachNote:
    summary = _aggregate_summary(habit_stats)

    if not api_key:
        return CoachNote(text=_deterministic_note(habit_stats), source="deterministic")

    try:
        text = _call_anthropic(summary, api_key)
        if text:
            return CoachNote(text=text, source="ai")
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
        pass

    return CoachNote(text=_deterministic_note(habit_stats), source="deterministic")
