"""AI-drafted (or deterministically templated) 'Participants & Data Quality' paragraph.

Calls the Anthropic Messages API directly over HTTPS via stdlib `urllib` -- no
`anthropic` SDK or third-party HTTP library dependency. Falls back to a fully-computed
deterministic template whenever no API key is set, or the request fails for any
reason, so the report is always complete.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional

from qc import ConditionSummary, QCConfig, SubjectSummary

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"
REQUEST_TIMEOUT_SECONDS = 20


def _deterministic_paragraph(
    subjects: list[SubjectSummary],
    conditions: list[ConditionSummary],
    excluded: list[SubjectSummary],
    config: QCConfig,
) -> str:
    n_total = len(subjects)
    n_excluded = len(excluded)
    n_final = n_total - n_excluded
    condition_names = ", ".join(c.condition for c in conditions) if conditions else "the task"

    if n_total == 0:
        return "No subjects were present in the supplied dataset; no data-quality summary can be generated."

    reason_counts: dict[str, int] = {}
    for s in excluded:
        for flag in s.flags:
            key = flag.split(" (")[0]
            reason_counts[key] = reason_counts.get(key, 0) + 1

    reason_text = ""
    if reason_counts:
        parts = [f"{count} for {reason.replace('_', ' ')}" for reason, count in sorted(reason_counts.items())]
        reason_text = " Exclusion reasons included " + "; ".join(parts) + "."

    pct_excluded = (n_excluded / n_total * 100) if n_total else 0.0

    return (
        f"Of {n_total} participants who completed {condition_names}, "
        f"{n_excluded} ({pct_excluded:.1f}%) were excluded from analysis based on pre-registered "
        f"data-quality criteria (reaction times below {config.rt_floor_ms:.0f} ms, response times "
        f"more than {config.sd_outlier:.1f} SD from a participant's own mean or above "
        f"{config.rt_ceiling_ms:.0f} ms, accuracy not distinguishable from chance performance at "
        f"{config.chance_rate:.0%}, or incomplete data below {config.min_completion:.0%} of expected "
        f"trials), leaving a final analytic sample of {n_final}.{reason_text}"
    )


def _build_ai_prompt(
    subjects: list[SubjectSummary],
    conditions: list[ConditionSummary],
    excluded: list[SubjectSummary],
    config: QCConfig,
) -> str:
    lines = [
        "Write one concise, publication-ready methods-section paragraph (3-5 sentences, "
        "plain scientific prose, no bullet points, no headings) describing participant "
        "data-quality exclusions for a behavioral reaction-time study, using ONLY the "
        "statistics given below. Do not invent numbers.",
        "",
        f"Total participants: {len(subjects)}",
        f"Conditions: {', '.join(c.condition for c in conditions)}",
        f"Participants excluded: {len(excluded)}",
        f"Final analytic sample: {len(subjects) - len(excluded)}",
        f"RT floor (anticipatory response) threshold: {config.rt_floor_ms} ms",
        f"RT outlier threshold: {config.sd_outlier} SD from each participant's own mean, "
        f"or above {config.rt_ceiling_ms} ms",
        f"Chance performance threshold: {config.chance_rate:.0%}",
        f"Minimum completion fraction: {config.min_completion:.0%}",
    ]
    if excluded:
        lines.append("Exclusion reasons observed: " + "; ".join(sorted({f.split(' (')[0] for s in excluded for f in s.flags})))
    return "\n".join(lines)


def _post_json(url: str, headers: dict, payload: dict, timeout: float) -> tuple[Optional[int], Optional[dict]]:
    """POST a JSON payload and return (status_code, parsed_json). Never raises."""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            data = json.loads(response.read().decode("utf-8"))
            return status, data
    except urllib.error.HTTPError as exc:
        try:
            data = json.loads(exc.read().decode("utf-8"))
        except (ValueError, AttributeError):
            data = None
        return exc.code, data
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None, None


def _call_anthropic(prompt: str, api_key: str) -> Optional[str]:
    status, data = _post_json(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        payload={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if status != 200 or data is None:
        return None

    try:
        blocks = data.get("content", [])
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        return text.strip() or None
    except (AttributeError, TypeError):
        return None


def generate_methods_paragraph(
    subjects: list[SubjectSummary],
    conditions: list[ConditionSummary],
    excluded: list[SubjectSummary],
    config: QCConfig,
) -> tuple[str, str]:
    """Returns (paragraph, source) where source is "ai" or "template"."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        prompt = _build_ai_prompt(subjects, conditions, excluded, config)
        ai_text = _call_anthropic(prompt, api_key)
        if ai_text:
            return ai_text, "ai"

    return _deterministic_paragraph(subjects, conditions, excluded, config), "template"
