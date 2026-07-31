"""Anthropic API integration for CI bottleneck insights. Graceful fallback on error."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-haiku-4-5-20251001"


def build_prompt(
    global_stats: dict[str, Any],
    top_workflows: list[dict[str, Any]],
) -> str:
    """Build a prompt for CI bottleneck analysis."""
    lines = [
        "You are a CI/CD performance analyst. Analyze this GitHub Actions data and write 4–5 actionable bullet points.",
        "Each bullet names a specific workflow or repo and suggests one concrete improvement.",
        "Be specific — not generic advice. Use the data provided.",
        "",
        "## Global stats",
        f"- Total runs (last 30d): {global_stats.get('total_runs', 0)}",
        f"- Total CI minutes burned: {global_stats.get('total_ci_minutes', 0):.1f}",
        f"- Overall failure rate: {global_stats.get('overall_failure_rate', 0)*100:.1f}%",
        f"- Repos with CI: {global_stats.get('repos_with_ci', 0)}",
        f"- Slowest workflow: {global_stats.get('slowest_workflow', 'N/A')}",
        f"- Most failed workflow: {global_stats.get('most_failed_workflow', 'N/A')}",
        "",
        "## Top workflows by improvement potential",
    ]
    for i, wf in enumerate(top_workflows[:8], 1):
        avg = wf.get("avg_duration_s", 0)
        p95 = wf.get("p95_duration_s", 0)
        frate = wf.get("failure_rate", 0) * 100
        runs = wf.get("total_runs", 0)
        lines.append(
            f"{i}. {wf.get('repo', '?')}/{wf.get('workflow_name', '?')}: "
            f"avg {avg:.0f}s, p95 {p95:.0f}s, {frate:.0f}% failure rate, {runs} runs"
        )

    lines += [
        "",
        "Write 4–5 concise bullet points (start each with •). No preamble or summary paragraph.",
    ]
    return "\n".join(lines)


def get_insights(
    global_stats: dict[str, Any],
    top_workflows: list[dict[str, Any]],
    api_key: str | None = None,
) -> str:
    """Call Claude Haiku for CI insights. Returns bullet-point string or fallback."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return ""

    prompt = build_prompt(global_stats, top_workflows)
    payload = json.dumps({
        "model": _MODEL,
        "max_tokens": 512,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        _ANTHROPIC_API_URL,
        data=payload,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            text = data.get("content", [{}])[0].get("text", "").strip()
            return text
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, KeyError, IndexError) as exc:
        print(f"AI insights unavailable: {exc}", file=sys.stderr)
        return ""
