"""AI synthesizer — builds briefing prompt and calls Anthropic API via urllib."""
from __future__ import annotations

import json
import os
import urllib.request

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"


def format_prompt(github_data: dict, portfolio_data: dict, weather_data: dict) -> str:
    """Assemble a structured prompt describing today's data for Claude to summarize."""
    lines = [
        "You are generating a concise morning briefing for a researcher and founder.",
        "Summarize what needs attention today in 4-5 bullet points. Be specific, not generic.",
        "",
    ]

    # GitHub
    recent = github_data.get("recent_repos", [])
    stale = github_data.get("stale_repos", [])
    prs = github_data.get("open_prs", [])
    lines.append("## GitHub Activity (last 24h)")
    lines.append(f"- {len(recent)} repos had recent pushes, {len(stale)} repos are stale (7+ days)")
    lines.append(f"- {len(prs)} open pull requests across active repos")
    if recent:
        lines.append(f"- Most recently active: {recent[0]['name']}")
    if stale:
        lines.append(f"- Stalest repo: {stale[0]['name']}")
    lines.append("")

    # Portfolio
    total_up = portfolio_data.get("total_up", 0)
    total_down = portfolio_data.get("total_down", 0)
    total_flat = portfolio_data.get("total_flat", 0)
    gainers = portfolio_data.get("top_gainers", [])
    losers = portfolio_data.get("top_losers", [])
    lines.append("## Portfolio Moves")
    lines.append(f"- {total_up} up, {total_down} down, {total_flat} flat")
    if gainers:
        lines.append(f"- Top gainer: {gainers[0]['ticker']} {gainers[0]['formatted_change']}")
    if losers:
        lines.append(f"- Top loser: {losers[0]['ticker']} {losers[0]['formatted_change']}")
    lines.append("")

    # Weather
    hours = weather_data.get("hours", [])
    best_run = weather_data.get("best_run", [])
    lines.append("## Today's Conditions (Toronto)")
    if hours:
        noon = next((h for h in hours if h["hour"] == 12), hours[len(hours) // 2] if hours else None)
        if noon:
            lines.append(f"- Midday: {noon['temp_c']}°C, {noon['wind_kph']} km/h wind, {noon['precip_prob']}% precip")
    if best_run:
        best = best_run[0]
        lines.append(f"- Best run window: {best['time'][-5:]} (score {best['scores']['run']}/100)")
    lines.append("")

    lines.append("Write 4-5 bullet points summarizing what this person should pay attention to today.")
    lines.append("Focus on actionable items or notable conditions, not routine status.")

    return "\n".join(lines)


def synthesize(github_data: dict, portfolio_data: dict, weather_data: dict) -> str:
    """Call Claude Haiku to produce a morning briefing summary. Returns '' on any failure."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return ""

    prompt = format_prompt(github_data, portfolio_data, weather_data)
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            content = result.get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", "")
            return ""
    except Exception:
        return ""
