"""Optional Claude Haiku funding-landscape briefing, strictly grounded in computed aggregates.

Principal-investigator names and abstract text are never passed to this
module's prompt-building function at all -- by construction, not by
redaction -- so they cannot leak into a request under any code path here.
`generate_briefing` never raises: any missing API key, network failure, or
malformed response falls back to a deterministic template built from the
same aggregate numbers.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Callable, Optional

import aggregate

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"

HttpPostFn = Callable[[str, dict, dict], dict]  # url, headers, body -> parsed json


def default_http_post(url: str, headers: dict, body: dict) -> dict:
    """Real transport: POST JSON to `url` with `headers`, return the parsed JSON response."""
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def build_topic_summary(topic: str, projects: list) -> dict:
    """Strictly-grounded aggregate summary for one topic — no PI names, no abstracts."""
    year_totals = aggregate.funding_by_year(projects)
    institutions = aggregate.top_institutions(projects, n=5)
    return {
        "topic": topic,
        "total_funding": aggregate.total_funding(projects),
        "project_count": len(projects),
        "fiscal_years": sorted(year_totals.keys()),
        "funding_by_year": {
            str(year): round(data["total_amount"], 2) for year, data in year_totals.items()
        },
        "top_institutions": [
            {"name": name, "total": round(total, 2)} for name, total, _ in institutions
        ],
        "sample_titles": [project.title for project in projects[:8]],
    }


def build_prompt(summary: dict) -> str:
    """Build the Claude prompt from a topic summary. Contains no PI names or abstracts."""
    return (
        "You are drafting one short, factual paragraph (3-5 sentences) summarizing the "
        "current NIH funding landscape for a specific research topic, for a researcher "
        "preparing a grant application. Use ONLY the data below -- never invent a statistic, "
        "institution, or project that is not listed here.\n\n"
        f"Topic: {summary['topic']}\n"
        f"Total tracked funding: ${summary['total_funding']:,.0f} across {summary['project_count']} projects\n"
        f"Fiscal years covered: {summary['fiscal_years']}\n"
        f"Funding by fiscal year: {summary['funding_by_year']}\n"
        f"Top funded institutions: {summary['top_institutions']}\n"
        f"Sample project titles: {summary['sample_titles']}\n\n"
        "Write the paragraph now. Do not include a heading or preamble."
    )


def deterministic_fallback(summary: dict) -> str:
    """A complete, readable briefing built with zero network calls."""
    if summary["project_count"] == 0:
        return (
            f'No funded NIH projects were found for "{summary["topic"]}" in the tracked '
            f"fiscal years {summary['fiscal_years']}. Consider broadening the search term."
        )
    years = summary["fiscal_years"]
    year_range = f"{years[0]}–{years[-1]}" if len(years) > 1 else str(years[0])
    top_inst = summary["top_institutions"][0] if summary["top_institutions"] else None
    lead = (
        f"Across fiscal years {year_range}, {summary['project_count']} NIH-funded projects "
        f'matching "{summary["topic"]}" totaled ${summary["total_funding"]:,.0f}.'
    )
    if top_inst:
        lead += (
            f" The most heavily funded institution in this set was {top_inst['name']} "
            f"(${top_inst['total']:,.0f} across its tracked projects)."
        )
    return lead


def generate_briefing(
    topic: str,
    projects: list,
    api_key: Optional[str] = None,
    http_post: HttpPostFn = default_http_post,
) -> str:
    """AI-written briefing when an API key is set and the call succeeds; otherwise the
    deterministic fallback. With no api_key, http_post is never called."""
    summary = build_topic_summary(topic, projects)
    if not api_key:
        return deterministic_fallback(summary)

    prompt = build_prompt(summary)
    body = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    try:
        response = http_post(ANTHROPIC_URL, headers, body)
        text_blocks = response.get("content") or []
        text = "".join(
            block.get("text", "") for block in text_blocks if isinstance(block, dict)
        ).strip()
        if not text:
            raise ValueError("empty response from Anthropic API")
        return text
    except Exception:
        return deterministic_fallback(summary)
