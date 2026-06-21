import json
import urllib.error
import urllib.request
from typing import Callable, Optional


_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-haiku-4-5-20251001"


def _build_prompt(repos: list[dict]) -> str:
    sorted_repos = sorted(repos, key=lambda r: r["health_score"])[:25]
    lines = []
    for r in sorted_repos:
        lines.append(
            f"- {r['name']}: score={r['health_score']}, "
            f"label={r['health_label']}, pushed={r['days_since_push']}d ago, "
            f"issues={r['open_issues']}, ci={r['ci_status']}"
        )
    return (
        "GitHub repository health data (lowest health score first):\n"
        + "\n".join(lines)
        + "\n\nWrite 3-4 bullet points (one sentence each, under 20 words) as a morning briefing:\n"
        "• Flag specific repos with CI failures or high issue counts needing attention\n"
        "• Note any repos that have gone quiet (not pushed in weeks)\n"
        "• Highlight any positive patterns worth noting\n"
        "Start each bullet with the • character."
    )


def _default_post(payload: dict, api_key: str) -> dict:
    req = urllib.request.Request(
        _ANTHROPIC_URL,
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def generate_insights(
    repos: list[dict],
    api_key: Optional[str] = None,
    _post: Optional[Callable] = None,
) -> str:
    """Generate AI-powered briefing. Returns empty string if api_key is None or request fails."""
    if not api_key or not repos:
        return ""

    payload = {
        "model": _MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": _build_prompt(repos)}],
    }

    post_fn = _post or (lambda p: _default_post(p, api_key))
    try:
        response = post_fn(payload)
        return response["content"][0]["text"].strip()
    except Exception:
        return ""
