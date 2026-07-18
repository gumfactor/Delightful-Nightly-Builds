"""Optional AI-generated consumer-impact briefing, with a deterministic fallback.

Only aggregated numeric deltas are ever sent to the Anthropic API — never
raw personal data. The Anthropic API key is read from the environment at
runtime only; it is never hardcoded and is not present in the build
container. Every test in tests/test_briefing.py mocks this call.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Dict, Optional

from src.deltas import DeltaSummary

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"
REQUEST_TIMEOUT_SECONDS = 20
MAX_TOKENS = 300


def generate_briefing(
    deltas_by_label: Dict[str, Optional[DeltaSummary]],
    api_key: Optional[str],
) -> tuple[str, str]:
    """Return (briefing_text, source) where source is "ai" or "template".

    Falls back to the deterministic template on a missing key, any network
    error, a non-200 response, or an unexpected response shape — the
    dashboard must always have a complete briefing panel.
    """
    if api_key:
        ai_text = _try_ai_briefing(deltas_by_label, api_key)
        if ai_text:
            return ai_text, "ai"
    return _template_briefing(deltas_by_label), "template"


def _try_ai_briefing(
    deltas_by_label: Dict[str, Optional[DeltaSummary]], api_key: str
) -> Optional[str]:
    prompt = _build_prompt(deltas_by_label)
    body = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=body,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                return None
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, OSError):
        return None

    content = payload.get("content")
    if not isinstance(content, list) or not content:
        return None
    first_block = content[0]
    if not isinstance(first_block, dict):
        return None
    text = first_block.get("text")
    if not isinstance(text, str) or not text.strip():
        return None
    return text.strip()


def _build_prompt(deltas_by_label: Dict[str, Optional[DeltaSummary]]) -> str:
    lines = [
        "You are writing a short (3-4 sentence) plain-English briefing for a "
        "Canadian consumer-advocacy platform. Given the latest values and "
        "period-over-period changes for these Canadian macroeconomic "
        "indicators, explain what the movements imply for the relative cost "
        "of imported goods versus Canadian-made products, and for consumer "
        "purchasing power generally. Do not give investment advice. Numbers:",
    ]
    for label, summary in deltas_by_label.items():
        lines.append(_describe_indicator(label, summary))
    return "\n".join(lines)


def _template_briefing(deltas_by_label: Dict[str, Optional[DeltaSummary]]) -> str:
    described = [
        _describe_indicator(label, summary) for label, summary in deltas_by_label.items()
    ]
    if not described:
        return (
            "No indicator history is available yet. Run `sync` at least once "
            "to build a briefing from live data."
        )
    intro = "Latest snapshot of tracked Canadian economic indicators:"
    return intro + " " + " ".join(described)


def _describe_indicator(label: str, summary: Optional[DeltaSummary]) -> str:
    if summary is None:
        return f"{label}: no data synced yet."
    parts = [f"{label} is {summary.latest_value:g} as of {summary.latest_date.isoformat()}"]
    if summary.month is not None and summary.month.pct_change is not None:
        direction = "up" if summary.month.change >= 0 else "down"
        parts.append(f"({direction} {abs(summary.month.pct_change):.1f}% over the past month)")
    return " ".join(parts) + "."
