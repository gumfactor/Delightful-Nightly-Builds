"""Optional AI-generated 'Coach's Note' summarizing the week's conditions.

Sends only an aggregate numeric summary (best/worst day, limiting factor per
activity) to the Anthropic API — never raw personal data, never per-hour
data. With no ANTHROPIC_API_KEY set, a deterministic template produces an
equivalent note with zero network calls.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Callable, Optional, TypedDict

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"


class WeekSummary(TypedDict):
    best_running_day: str
    best_running_score: float
    worst_running_day: str
    worst_running_score: float
    running_limiting_factor: str
    best_golf_day: str
    best_golf_score: float
    worst_golf_day: str
    worst_golf_score: float
    golf_limiting_factor: str


Transport = Callable[[str, dict], str]


def default_transport(api_key: str, body: dict) -> str:
    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def _limiting_factor_phrase(factor: str) -> str:
    phrases = {
        "temp": "temperature",
        "wind": "wind",
        "precip": "rain risk",
        "aqi": "air quality",
        "uv": "UV exposure",
    }
    return phrases.get(factor, factor)


def deterministic_note(summary: WeekSummary) -> str:
    running_factor = _limiting_factor_phrase(summary["running_limiting_factor"])
    golf_factor = _limiting_factor_phrase(summary["golf_limiting_factor"])
    return (
        f"Best day to run is {summary['best_running_day']} "
        f"(score {summary['best_running_score']}/100); "
        f"{summary['worst_running_day']} is the weakest, mainly due to {running_factor}. "
        f"For golf, {summary['best_golf_day']} looks best "
        f"(score {summary['best_golf_score']}/100), while {summary['worst_golf_day']} "
        f"is the one to skip, mainly due to {golf_factor}."
    )


def generate_note(
    summary: WeekSummary,
    api_key: Optional[str] = None,
    transport: Transport = default_transport,
) -> str:
    """Return an AI-generated note if api_key is set, else the deterministic fallback.

    api_key defaults to the ANTHROPIC_API_KEY environment variable when not
    passed explicitly, matching the runtime-only-credential pattern used
    throughout this catalog.
    """
    key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return deterministic_note(summary)

    prompt = (
        "You are a terse outdoor-activity coach. Given this week's running and golf "
        "suitability summary, write a 2-3 sentence note recommending the best day for "
        "each activity and naming the main limiting factor for the worst day. "
        f"Summary: {json.dumps(summary)}"
    )
    body = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 200,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        raw = transport(key, body)
        payload = json.loads(raw)
        content = payload.get("content", [])
        if content and isinstance(content, list) and "text" in content[0]:
            text = content[0]["text"].strip()
            if text:
                return text
    except Exception:
        pass
    return deterministic_note(summary)
