"""Optional AI commentary on the current rotation regime.

Strictly built from already-computed numbers (ticker, RS-Ratio, RS-Momentum,
quadrant, and quadrant transitions) -- never invents a sector, a number, or
outside knowledge. Uses stdlib `urllib.request` directly against the
Anthropic Messages API (no SDK dependency) so `ANTHROPIC_API_KEY` can be
supplied purely as a runtime environment variable, per PROFILE.md. Falls
back to a deterministic template on any missing key, network error, or
malformed response -- and makes zero network calls at all when no key is set.
"""

from __future__ import annotations

import json
import os
import urllib.request

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 300
REQUEST_TIMEOUT_SECONDS = 15


def _deterministic_commentary(snapshots: dict, transitions: list) -> str:
    by_quadrant: dict = {"Leading": [], "Weakening": [], "Lagging": [], "Improving": []}
    for ticker, result in snapshots.items():
        by_quadrant[result.latest.quadrant].append(ticker)
    for group in by_quadrant.values():
        group.sort()

    lines = []
    for quadrant in ("Leading", "Improving", "Weakening", "Lagging"):
        tickers = by_quadrant[quadrant]
        if tickers:
            lines.append(f"{quadrant}: {', '.join(tickers)}.")

    changed = sorted(t.ticker for t in transitions if t.changed)
    if changed:
        detail = "; ".join(
            f"{t.ticker} {t.previous_quadrant} -> {t.current_quadrant}"
            for t in transitions
            if t.changed
        )
        lines.append(f"Quadrant changes since the last run ({len(changed)}): {detail}.")
    elif any(t.previous_quadrant is not None for t in transitions):
        lines.append("No sector changed quadrant since the last run.")
    else:
        lines.append("This is the first recorded run -- no prior run to compare against.")

    return " ".join(lines)


def _build_summary_payload(snapshots: dict, transitions: list) -> str:
    rows = [
        {
            "ticker": ticker,
            "rs_ratio": round(result.latest.rs_ratio, 2),
            "rs_momentum": round(result.latest.rs_momentum, 2),
            "quadrant": result.latest.quadrant,
        }
        for ticker, result in sorted(snapshots.items())
    ]
    changes = [
        {"ticker": t.ticker, "from": t.previous_quadrant, "to": t.current_quadrant}
        for t in transitions
        if t.changed
    ]
    return json.dumps({"sectors": rows, "quadrant_changes": changes})


def _call_anthropic(api_key: str, summary_payload: str) -> str | None:
    system_prompt = (
        "You are a market-structure analyst. You will be given a JSON summary of "
        "sector relative-rotation data (RS-Ratio, RS-Momentum, and quadrant per "
        "sector ETF, plus any quadrant changes since the last run). Write a short "
        "(3-5 sentence) plain-English commentary on the current rotation regime. "
        "Use only the tickers, numbers, and quadrants given in the JSON -- never "
        "invent a sector, a number, or outside market knowledge not present in the data."
    )
    body = json.dumps(
        {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "system": system_prompt,
            "messages": [{"role": "user", "content": summary_payload}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - any network/API failure falls back, never crashes the build
        return None

    try:
        blocks = payload["content"]
        text = "".join(block["text"] for block in blocks if block.get("type") == "text")
    except (KeyError, TypeError):
        return None
    return text.strip() or None


def generate_commentary(snapshots: dict, transitions: list, api_key: str | None = None) -> str:
    """Return AI commentary if an API key is available and the call succeeds,
    otherwise the deterministic fallback. Never raises.
    """
    key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return _deterministic_commentary(snapshots, transitions)

    summary_payload = _build_summary_payload(snapshots, transitions)
    ai_text = _call_anthropic(key, summary_payload)
    return ai_text if ai_text is not None else _deterministic_commentary(snapshots, transitions)
