"""Optional AI landscape briefing via the Anthropic API, with a deterministic template fallback.

Only aggregated statistics and a small sample of public NIH grant titles/abstracts
(already public U.S. government data) are ever sent — no personal or proprietary
data. ANTHROPIC_API_KEY is read from the environment by the caller (main.py);
this module never reads environment variables directly, which keeps it easy to
unit test in isolation.
"""

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Sequence

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
REQUEST_TIMEOUT_SECONDS = 30
SAMPLE_TITLE_COUNT = 6


class BriefingError(Exception):
    """Raised internally when the Anthropic API call fails; always caught and falls back."""


def _build_prompt(topic_label: str, stats: Dict[str, Any], top_institutes: Sequence, mechanisms: Dict[str, int], sample_titles: List[str]) -> str:
    institute_lines = "\n".join(
        f"- {name}: ${info['total_amount']:,} across {info['count']} project(s)"
        for name, info in top_institutes[:5]
    ) or "- (no institute data available)"

    mechanism_lines = "\n".join(
        f"- {code}: {count} project(s)" for code, count in list(mechanisms.items())[:5]
    ) or "- (no mechanism data available)"

    title_lines = "\n".join(f"- {title}" for title in sample_titles[:SAMPLE_TITLE_COUNT]) or "- (no titles available)"

    year_start, year_end = stats.get("fiscal_year_range", (None, None))
    year_range = f"{year_start}-{year_end}" if year_start else "unknown"

    return (
        f"You are a research funding strategist. Below is a summary of currently NIH-funded "
        f"projects in the topic area \"{topic_label}\", drawn from the public NIH RePORTER database.\n\n"
        f"Fiscal years covered: {year_range}\n"
        f"Total projects found: {stats.get('project_count', 0)}\n"
        f"Total award funding: ${stats.get('total_amount', 0):,}\n\n"
        f"Top funding Institutes/Centers by total award amount:\n{institute_lines}\n\n"
        f"Funding mechanism breakdown:\n{mechanism_lines}\n\n"
        f"Sample project titles:\n{title_lines}\n\n"
        "Write a concise 3-4 sentence plain-English briefing for a grant-writing researcher in this "
        "field: where the funding is currently concentrated, which mechanisms and Institutes/Centers "
        "look most active, and one concrete suggestion for how to position a grant application given "
        "this landscape. Do not invent facts beyond what is given above."
    )


def _call_anthropic(prompt: str, api_key: str, model: str) -> str:
    payload = {
        "model": model,
        "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise BriefingError(f"Anthropic API returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise BriefingError(f"Could not reach Anthropic API: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise BriefingError("Anthropic API returned malformed JSON") from exc

    content = body.get("content")
    if not isinstance(content, list) or not content:
        raise BriefingError("Anthropic API response had no content")

    text_parts = [block.get("text", "") for block in content if isinstance(block, dict)]
    text = "".join(text_parts).strip()
    if not text:
        raise BriefingError("Anthropic API response had empty text")
    return text


def _template_briefing(topic_label: str, stats: Dict[str, Any], top_institutes: Sequence, mechanisms: Dict[str, int]) -> str:
    project_count = stats.get("project_count", 0)
    total_amount = stats.get("total_amount", 0)
    year_start, year_end = stats.get("fiscal_year_range", (None, None))
    year_range = f"{year_start}-{year_end}" if year_start else "no fiscal years recorded"

    if project_count == 0:
        return (
            f"No funded projects are currently stored for \"{topic_label}\". "
            "Run `sync` to fetch data from NIH RePORTER before generating a briefing."
        )

    top_institute_name = top_institutes[0][0] if top_institutes else "no single institute"
    top_mechanism = next(iter(mechanisms), "no dominant mechanism")

    return (
        f"\"{topic_label}\" has {project_count} funded project(s) on record ({year_range}), "
        f"totaling ${total_amount:,} in award funding. {top_institute_name} is the leading funding "
        f"Institute/Center by total award amount, and {top_mechanism} is the most common funding "
        "mechanism in this dataset. (Deterministic summary — set ANTHROPIC_API_KEY for an AI-generated "
        "briefing with strategic positioning suggestions.)"
    )


def generate_briefing(
    topic_label: str,
    projects: Sequence[Any],
    stats: Dict[str, Any],
    top_institutes: Sequence,
    mechanisms: Dict[str, int],
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> Dict[str, str]:
    """Return {"text": str, "source": "ai" | "template"}. Never raises."""
    sample_titles = [project["title"] for project in projects[:SAMPLE_TITLE_COUNT] if project["title"]]

    if api_key:
        prompt = _build_prompt(topic_label, stats, top_institutes, mechanisms, sample_titles)
        try:
            text = _call_anthropic(prompt, api_key, model)
            return {"text": text, "source": "ai"}
        except BriefingError:
            pass

    return {"text": _template_briefing(topic_label, stats, top_institutes, mechanisms), "source": "template"}
