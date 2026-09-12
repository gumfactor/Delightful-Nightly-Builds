"""Per-cluster narrative synthesis: deterministic by default, optional AI.

The AI path is strictly additive: it is only ever attempted when the caller
passes `use_ai=True` AND `ANTHROPIC_API_KEY` is set, and any failure falls
back unconditionally to the deterministic template. No other code path ever
touches the network.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Callable

AI_MODEL = "claude-haiku-4-5-20251001"
AI_URL = "https://api.anthropic.com/v1/messages"

AiTransport = Callable[[str, dict, bytes], bytes]

FALLBACK_TRIGGERS = (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError, OSError)


def _default_ai_transport(url: str, headers: dict, body: bytes) -> bytes:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def deterministic_narrative(cluster: dict) -> str:
    papers = cluster.get("papers") or []
    years = [p["year"] for p in papers if p["year"]]
    year_range = f"{min(years)}–{max(years)}" if years else "year unknown"
    total_citations = sum(p["citation_count"] or 0 for p in papers)
    titles = "; ".join(p["title"] for p in papers)
    count = len(papers)
    plural = "paper" if count == 1 else "papers"
    return (
        f"Cluster “{cluster['label']}” ({count} {plural}, {year_range}, "
        f"{total_citations} total citations): {titles}."
    )


def _build_prompt(cluster: dict) -> str:
    papers = cluster.get("papers") or []
    lines = [
        f"- {p['title']} ({p['year'] or 'n.d.'}): "
        f"{(p['abstract'] or 'no abstract available')[:400]}"
        for p in papers
    ]
    keywords = ", ".join(cluster.get("keywords", [])[:8])
    return (
        "You are helping a researcher describe one thematic cluster of their own "
        "published work for a grant biosketch or manuscript introduction. Write a "
        "single, concise paragraph (3-5 sentences) synthesizing the throughline "
        "connecting these papers. Do not invent facts not supported by the titles "
        "and abstracts below. Do not mention the word 'cluster'.\n\n"
        f"Shared keywords: {keywords}\n\nPapers:\n" + "\n".join(lines)
    )


def generate_narrative(
    cluster: dict, use_ai: bool = False, transport: AiTransport = _default_ai_transport
) -> tuple:
    """Returns (text, source) where source is 'ai' or 'deterministic'."""
    deterministic = deterministic_narrative(cluster)

    if not use_ai:
        return deterministic, "deterministic"

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return deterministic, "deterministic"

    try:
        body = json.dumps(
            {
                "model": AI_MODEL,
                "max_tokens": 300,
                "messages": [{"role": "user", "content": _build_prompt(cluster)}],
            }
        ).encode("utf-8")
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        raw = transport(AI_URL, headers, body)
        data = json.loads(raw)
        text = "".join(
            block.get("text", "") for block in data["content"] if block.get("type") == "text"
        ).strip()
        if not text:
            return deterministic, "deterministic"
        return text, "ai"
    except FALLBACK_TRIGGERS:
        return deterministic, "deterministic"
