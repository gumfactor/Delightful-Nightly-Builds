import json
import os
import urllib.error
import urllib.request
from typing import List, Optional

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"


def build_brief_prompt(project: dict, activities: List[dict]) -> str:
    name = project.get("name", "")
    description = project.get("description", "")
    proj_type = project.get("type", "")

    if activities:
        lines = []
        for act in activities[:20]:
            date_str = (act.get("occurred_at") or "")[:10]
            lines.append(f"  - [{date_str}] {act.get('title', '')}")
        activity_text = "\n".join(lines)
    else:
        activity_text = "  (no recent activity logged)"

    return (
        f"You are a brief, direct assistant helping a busy researcher and founder "
        f"switch context between projects.\n\n"
        f"Project: {name}\n"
        f"Type: {proj_type}\n"
        f"Description: {description}\n\n"
        f"Recent activity (last 30 days):\n{activity_text}\n\n"
        f"In 3-5 sentences, summarize: (1) what was being worked on recently, "
        f"(2) the most likely current status, and (3) the clearest next step to pick up. "
        f"Be direct and specific. No preamble."
    )


def generate_brief(
    project: dict,
    activities: List[dict],
    api_key: Optional[str] = None,
) -> str:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return _fallback_brief(project, activities)

    prompt = build_brief_prompt(project, activities)
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"].strip()
    except (urllib.error.URLError, urllib.error.HTTPError,
            KeyError, IndexError, json.JSONDecodeError):
        return _fallback_brief(project, activities)


def _fallback_brief(project: dict, activities: List[dict]) -> str:
    name = project.get("name", "Unknown")
    count = len(activities)
    if activities:
        last_date = (activities[0].get("occurred_at") or "")[:10]
        last_title = activities[0].get("title", "")
        return (
            f"{name}: {count} activities in the last 30 days. "
            f"Most recent ({last_date}): {last_title}. "
            f"Set ANTHROPIC_API_KEY for AI-generated context briefings."
        )
    return (
        f"{name}: No recent activity logged. "
        f"Run 'sync' to pull GitHub commits, or 'log' to add manual notes. "
        f"Set ANTHROPIC_API_KEY for AI-generated context briefings."
    )
