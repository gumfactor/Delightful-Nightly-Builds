"""Optional Claude Haiku drafting pass, strictly constrained to outline facts.

No SDK dependency — calls the Anthropic Messages API directly via
`urllib.request`, matching this catalog's established pattern for optional
runtime-only AI calls. `ANTHROPIC_API_KEY` is never present in the build
environment; this module must therefore work correctly, with zero network
calls attempted, when the key is absent — verified in tests.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional

from outline_builder import DigestOutline

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-haiku-4-5"
REQUIRED_SECTIONS = ("intro", "trend_section", "facts_section", "takeaway")

SYSTEM_PROMPT = (
    "You are drafting a short research-digest article section set for a "
    "researcher's blog. You are given a JSON object of already-verified "
    "facts extracted from real arXiv papers. Use ONLY the facts provided — "
    "never invent statistics, paper titles, authors, or claims not present "
    "in the input. Do not add outside knowledge about the topic. Reply with "
    "ONLY a JSON object with exactly these four string keys: "
    '"intro", "trend_section", "facts_section", "takeaway". No markdown '
    "fences, no other text."
)


@dataclass
class DigestDraft:
    intro: str
    trend_section: str
    facts_section: str
    takeaway: str
    source: str  # "ai" | "template"


def _facts_payload(outline: DigestOutline) -> dict:
    """Build the fact set the model is allowed to use — nothing else."""
    trend = outline.trend
    return {
        "topic": outline.topic,
        "window_months": outline.window_months,
        "total_papers": outline.total_papers,
        "hook_stat": outline.hook_stat,
        "trend_direction": trend.direction,
        "first_half_count": trend.first_half_count,
        "second_half_count": trend.second_half_count,
        "pct_change": trend.pct_change,
        "rising_keywords": list(outline.rising_keywords),
        "top_papers": [
            {"title": p.title, "published": p.published.isoformat(), "authors": p.authors}
            for p in outline.top_papers
        ],
        "notable_facts": [
            {
                "type": f.fact_type,
                "text": f.raw_text,
                "context": f.context,
                "paper_title": f.paper_title,
            }
            for f in outline.notable_facts
        ],
    }


def build_request_body(outline: DigestOutline, model: str) -> dict:
    facts = _facts_payload(outline)
    return {
        "model": model,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": "Facts (JSON):\n" + json.dumps(facts, indent=2),
            }
        ],
    }


def template_draft(outline: DigestOutline) -> DigestDraft:
    """Deterministic, always-available fallback — no network call, no AI."""
    trend = outline.trend

    intro = (
        f'{outline.hook_stat} This digest covers {outline.total_papers} arXiv '
        f'papers matching "{outline.topic}" from the past {outline.window_months} months.'
    )

    if outline.rising_keywords:
        kw_text = ", ".join(outline.rising_keywords)
        trend_section = (
            f"The trend is currently classified as **{trend.direction}**. "
            f"Terms showing up more often in recent papers than earlier ones: {kw_text}."
        )
    else:
        trend_section = (
            f"The trend is currently classified as **{trend.direction}**. "
            "No clearly rising keywords were detected in this window — the "
            "corpus may be too small or too stable to show a shift."
        )

    if outline.notable_facts:
        lines = [
            f"- **{f.fact_type.replace('_', ' ')}** ({f.raw_text}) in “{f.paper_title}”: "
            f"…{f.context}…"
            for f in outline.notable_facts
        ]
        facts_section = "Concrete figures reported in these papers:\n" + "\n".join(lines)
    else:
        facts_section = (
            "No structured statistics (sample sizes, p-values, correlations, "
            "effect sizes) were detected in the matched abstracts."
        )

    if outline.top_papers:
        newest = outline.top_papers[0]
        takeaway = (
            f'Worth a closer read: "{newest.title}" ({newest.published.isoformat()}), '
            f"the most recent match in this window."
        )
    else:
        takeaway = "No papers matched this query in the given window — try a broader topic or a longer window."

    return DigestDraft(
        intro=intro,
        trend_section=trend_section,
        facts_section=facts_section,
        takeaway=takeaway,
        source="template",
    )


def _extract_json_object(text: str) -> Optional[dict]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _validate_sections(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    return all(
        isinstance(data.get(key), str) and data.get(key).strip()
        for key in REQUIRED_SECTIONS
    )


def draft_sections(
    outline: DigestOutline,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    urlopen: Callable = urllib.request.urlopen,
) -> DigestDraft:
    """Draft the four article sections. Uses Claude Haiku when `api_key` is
    provided and the call succeeds; falls back to the deterministic template
    renderer otherwise, including on any network or parsing failure."""
    if not api_key:
        return template_draft(outline)

    model = model or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL
    body = build_request_body(outline, model)
    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
        payload = json.loads(raw)
        text = payload["content"][0]["text"]
        sections = _extract_json_object(text)
        if not _validate_sections(sections):
            return template_draft(outline)
        return DigestDraft(
            intro=sections["intro"],
            trend_section=sections["trend_section"],
            facts_section=sections["facts_section"],
            takeaway=sections["takeaway"],
            source="ai",
        )
    except (
        urllib.error.URLError,
        TimeoutError,
        KeyError,
        IndexError,
        ValueError,
        json.JSONDecodeError,
    ):
        return template_draft(outline)
