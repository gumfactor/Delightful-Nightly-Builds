"""
Anthropic API integration — generates a developer profile paragraph
from the computed stats dict.
"""

from __future__ import annotations

import anthropic

from .analyzer import DAY_NAMES, HOUR_LABELS


def _format_hour(h: int) -> str:
    return HOUR_LABELS[h]


def _format_day(d: int) -> str:
    return DAY_NAMES[d]


def _build_prompt(stats: dict) -> str:
    username = stats.get("username", "this developer")
    total = stats.get("total_commits", 0)
    active = stats.get("active_days", 0)
    cpd = stats.get("commits_per_active_day", 0)
    peak_h = _format_hour(stats.get("most_productive_hour", 0))
    peak_d = _format_day(stats.get("most_productive_day", 0))
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    top_repo = stats.get("top_repo", "")
    top_count = stats.get("top_repo_count", 0)
    months = stats.get("months", 12)

    hourly = stats.get("hourly_distribution", {})
    morning = sum(hourly.get(h, 0) for h in range(5, 12))
    afternoon = sum(hourly.get(h, 0) for h in range(12, 18))
    evening = sum(hourly.get(h, 0) for h in range(18, 24))
    night = sum(hourly.get(h, 0) for h in range(0, 5))

    daily = stats.get("day_distribution", {})
    weekday_total = sum(daily.get(d, 0) for d in range(5))
    weekend_total = sum(daily.get(d, 0) for d in range(5, 7))
    weekend_pct = round(100 * weekend_total / max(total, 1))

    repos = stats.get("repo_breakdown", [])
    repo_summary = ", ".join(
        f"{r['repo'].split('/')[-1]} ({r['count']})" for r in repos[:3]
    )

    return f"""You are writing a developer activity profile based on real GitHub commit data.
Write 3 short sentences (2–3 lines each) in direct, analytical prose. No bullet points.
No filler phrases ("It's clear that...", "Overall...", "In summary...").
Be specific. Use the actual numbers.

Data for {username} over the past {months} months:
- Total commits: {total} across {active} active days ({cpd} commits/active day)
- Peak commit hour: {peak_h} | Peak day: {peak_d}
- Streaks: current {streak} days, longest {longest} days
- Time-of-day breakdown: morning {morning}, afternoon {afternoon}, evening {evening}, late night {night}
- Weekend ratio: {weekend_pct}% of commits on weekends
- Top repos by commit count: {repo_summary or "N/A"}

Write the profile in second person ("You commit most heavily...").
Cover: (1) when they work, (2) how consistently they work, (3) where attention is focused.
Do not fabricate data not given above."""


def generate_insights(stats: dict, api_key: str) -> str:
    """
    Call Claude Haiku to generate a plain-English developer profile.
    Returns the text content, or a fallback message on error.
    """
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": _build_prompt(stats)}],
        )
        return message.content[0].text.strip()
    except Exception as exc:
        return f"AI insights unavailable: {exc}"
