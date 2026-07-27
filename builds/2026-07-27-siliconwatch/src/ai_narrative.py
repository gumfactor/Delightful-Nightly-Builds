"""Optional Claude Haiku sector narrative, with an always-available deterministic fallback.

Only aggregated public-market numbers and public company names are ever sent —
never personal data. No `anthropic` package dependency: a direct HTTPS call via
urllib, matching this repo's established pattern for optional AI integrations.
"""
import json
import os
import urllib.request
from typing import Callable, Dict, Optional, Tuple

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"


def _fmt_money(value: Optional[float]) -> str:
    if value is None:
        return "an unknown amount"
    if value >= 1e12:
        return f"${value / 1e12:.2f}T"
    if value >= 1e9:
        return f"${value / 1e9:.1f}B"
    return f"${value:,.0f}"


def _fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "an unavailable percentage"
    return f"{value:.1f}%"


def build_template_narrative(aggregates: Dict) -> str:
    """Deterministic narrative built purely from arithmetic on the aggregates — no network call."""
    total_cap = _fmt_money(aggregates.get("total_market_cap"))
    avg_pe = aggregates.get("avg_pe_trailing")
    avg_margin = aggregates.get("avg_profit_margin")
    growth_count = aggregates.get("growth_positive_count", 0)
    tracked = aggregates.get("companies_tracked", 0)
    top_mover = aggregates.get("top_mover")
    laggard = aggregates.get("laggard")

    sentences = [
        f"Across the {tracked} tracked AI-infrastructure and semiconductor companies, "
        f"combined market capitalization stands at {total_cap}."
    ]
    if avg_pe is not None:
        sentences.append(
            f"The group trades at an average trailing P/E of {avg_pe:.1f}"
            + (
                f" with an average profit margin of {_fmt_pct(avg_margin * 100 if avg_margin is not None else None)}."
                if avg_margin is not None
                else "."
            )
        )
    sentences.append(
        f"{growth_count} of {tracked} companies are reporting positive revenue growth."
    )
    if top_mover:
        sentences.append(
            f"{top_mover['name']} ({top_mover['ticker']}) leads the group's price performance "
            f"over the tracked window at {_fmt_pct(top_mover['pct'])}."
        )
    if laggard and laggard.get("ticker") != (top_mover or {}).get("ticker"):
        sentences.append(
            f"{laggard['name']} ({laggard['ticker']}) has lagged, at {_fmt_pct(laggard['pct'])}."
        )
    return " ".join(sentences)


def _default_http_post(api_key: str, aggregates: Dict) -> str:
    prompt = (
        "You are a markets research assistant. In 100-150 words, write a plain-English "
        "paragraph about what these aggregated AI-infrastructure/semiconductor sector "
        "numbers suggest about the state of the AI compute buildout. Be specific, "
        "measured, and avoid generic filler. Data (all figures aggregated across public "
        f"companies, no personal data): {json.dumps(aggregates, default=str)}"
    )
    body = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["content"][0]["text"]


def generate_narrative(
    aggregates: Dict,
    api_key: Optional[str] = None,
    http_post: Optional[Callable[[str, Dict], str]] = None,
) -> Tuple[str, str]:
    """Return (narrative_text, source) where source is 'ai' or 'template'.

    Falls back to the deterministic template on a missing key, network error,
    or malformed response. Never raises.
    """
    key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return build_template_narrative(aggregates), "template"

    poster = http_post or _default_http_post
    try:
        text = poster(key, aggregates)
        if isinstance(text, str) and text.strip():
            return text.strip(), "ai"
    except Exception:
        pass
    return build_template_narrative(aggregates), "template"
