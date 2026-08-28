"""Optional Claude Haiku narrative for a flagged anomaly.

Privacy/scope guarantee: the only thing ever sent to the Anthropic API is
the already-computed aggregate anomaly dict (ticker, fiscal year, anomaly
type, and a short numeric detail string) -- never raw SEC filing text.

With no ANTHROPIC_API_KEY set, generate_narrative() makes zero network
calls and returns the deterministic template. Any network/parse failure
during a real call also falls back to the deterministic template rather
than raising, so render() always succeeds.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 120

ANOMALY_LABELS = {
    "revenue_decline": "Revenue decline",
    "margin_compression": "Margin compression",
    "leverage_spike": "Leverage spike",
    "negative_equity": "Negative equity",
    "swing_to_loss": "Swing to loss",
}


def deterministic_fallback(ticker: str, anomaly: dict[str, Any]) -> str:
    label = ANOMALY_LABELS.get(anomaly["type"], anomaly["type"].replace("_", " ").title())
    return f"{ticker} FY{anomaly['fiscal_year']}: {label} -- {anomaly['detail']}."


def _build_prompt(ticker: str, anomaly: dict[str, Any]) -> str:
    label = ANOMALY_LABELS.get(anomaly["type"], anomaly["type"])
    return (
        "You are annotating a financial anomaly dashboard for a personal investment "
        "research tool. Given only this aggregate data point, write exactly one plain "
        "English sentence (no preamble, no markdown) noting the finding in a neutral, "
        "analytical tone. Do not speculate beyond the numbers given.\n\n"
        f"Ticker: {ticker}\n"
        f"Fiscal year: {anomaly['fiscal_year']}\n"
        f"Anomaly type: {label}\n"
        f"Detail: {anomaly['detail']}\n"
    )


def generate_narrative(
    ticker: str,
    anomaly: dict[str, Any],
    api_key: str | None = None,
    urlopen_func: Callable[..., Any] = urllib.request.urlopen,
) -> str:
    """Return a one-sentence narrative for an anomaly.

    api_key defaults to reading ANTHROPIC_API_KEY from the environment when
    not passed explicitly (None means "not set" -- no network call).
    """
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return deterministic_fallback(ticker, anomaly)

    body = json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": _build_prompt(ticker, anomaly)}],
    }).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=body,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )

    try:
        with urlopen_func(request, timeout=20) as response:
            raw = response.read()
        parsed = json.loads(raw)
        text = parsed["content"][0]["text"].strip()
        return text if text else deterministic_fallback(ticker, anomaly)
    except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError, TypeError):
        return deterministic_fallback(ticker, anomaly)


def generate_narratives(
    anomalies_by_ticker: dict[str, list[dict[str, Any]]],
    api_key: str | None = None,
    urlopen_func: Callable[..., Any] = urllib.request.urlopen,
) -> dict[tuple[str, int, str], str]:
    """Generate a narrative for every anomaly, keyed by (ticker, fiscal_year, type)."""
    narratives: dict[tuple[str, int, str], str] = {}
    for ticker, anomalies in anomalies_by_ticker.items():
        for anomaly in anomalies:
            key = (ticker, anomaly["fiscal_year"], anomaly["type"])
            narratives[key] = generate_narrative(ticker, anomaly, api_key, urlopen_func)
    return narratives
