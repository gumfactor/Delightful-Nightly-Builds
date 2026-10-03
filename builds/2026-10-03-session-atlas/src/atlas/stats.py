"""Aggregations over indexed sessions."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

CHURN_THRESHOLD = 4  # edits to one file within one session that suggest rework


def _local(stamp: str, tz_offset_hours: float) -> datetime | None:
    if not stamp:
        return None
    try:
        moment = datetime.fromisoformat(stamp)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone(timedelta(hours=tz_offset_hours)))


def cache_hit_ratio(input_tokens: int, cache_write: int, cache_read: int) -> float:
    denominator = input_tokens + cache_write + cache_read
    return cache_read / denominator if denominator else 0.0


def build_stats(sessions: list[dict[str, Any]], tz_offset_hours: float = 0.0) -> dict[str, Any]:
    """Compute everything the explorer needs from session dicts (see Store.sessions)."""
    daily: dict[str, dict[str, float]] = defaultdict(lambda: {"sessions": 0, "prompts": 0, "hours": 0.0, "cost": 0.0})
    heat = [[0] * 24 for _ in range(7)]  # Monday=0
    projects: dict[str, dict[str, Any]] = {}
    tools: Counter = Counter()
    models: Counter = Counter()
    churn: list[dict[str, Any]] = []

    for s in sessions:
        moment = _local(s["start"], tz_offset_hours)
        if moment is not None:
            day = daily[moment.date().isoformat()]
            day["sessions"] += 1
            day["prompts"] += s["prompts"]
            day["hours"] += s["active_seconds"] / 3600
            day["cost"] += s["cost_usd"]
            heat[moment.weekday()][moment.hour] += s["prompts"]

        proj = projects.setdefault(
            s["project"],
            {"project": s["project"], "path": s["project_path"], "sessions": 0, "prompts": 0, "hours": 0.0,
             "cost": 0.0, "tokens": 0, "edits": 0, "last": ""},
        )
        proj["sessions"] += 1
        proj["prompts"] += s["prompts"]
        proj["hours"] += s["active_seconds"] / 3600
        proj["cost"] += s["cost_usd"]
        proj["tokens"] += s["input_tokens"] + s["output_tokens"] + s["cache_write_tokens"] + s["cache_read_tokens"]
        proj["edits"] += sum(s["files"].values())
        proj["last"] = max(proj["last"], s["start"])

        tools.update(s["tools"])
        for model, usage in s["models"].items():
            models[model] += sum(usage.values())
        for path, count in s["files"].items():
            if count >= CHURN_THRESHOLD:
                churn.append({"file": path, "edits": count, "project": s["project"], "session": s["id"]})

    totals = {
        "sessions": len(sessions),
        "prompts": sum(s["prompts"] for s in sessions),
        "hours": round(sum(s["active_seconds"] for s in sessions) / 3600, 2),
        "cost": round(sum(s["cost_usd"] for s in sessions), 2),
        "unpriced": any(s["unpriced"] for s in sessions),
        "input": sum(s["input_tokens"] for s in sessions),
        "output": sum(s["output_tokens"] for s in sessions),
        "cache_write": sum(s["cache_write_tokens"] for s in sessions),
        "cache_read": sum(s["cache_read_tokens"] for s in sessions),
        "tool_errors": sum(s["tool_errors"] for s in sessions),
        "tool_calls": sum(tools.values()),
        "projects": len(projects),
    }
    totals["cache_hit"] = round(cache_hit_ratio(totals["input"], totals["cache_write"], totals["cache_read"]), 4)

    return {
        "totals": totals,
        "daily": [{"date": d, **{k: round(v, 3) for k, v in vals.items()}} for d, vals in sorted(daily.items())],
        "heatmap": heat,
        "projects": sorted(projects.values(), key=lambda p: p["hours"], reverse=True),
        "tools": tools.most_common(15),
        "models": models.most_common(),
        "churn": sorted(churn, key=lambda c: c["edits"], reverse=True)[:15],
    }


def resume_prompt(session: dict[str, Any], max_files: int = 8) -> str:
    """A paste-ready prompt that re-establishes context for a past session."""
    lines = [f"Resuming earlier work in {session['project_path'] or session['project']}."]
    if session.get("branch"):
        lines.append(f"Git branch at the time: {session['branch']}.")
    if session.get("title"):
        lines.append(f"Session topic: {session['title']}.")
    if session.get("summary"):
        lines.append(f"Where it ended: {session['summary']}")
    if session.get("first_prompt"):
        lines.append(f"\nI originally asked:\n> {_clip(session['first_prompt'], 500)}")
    if session.get("last_prompt") and session["last_prompt"] != session.get("first_prompt"):
        lines.append(f"\nMy last request was:\n> {_clip(session['last_prompt'], 500)}")
    files = sorted(session.get("files", {}).items(), key=lambda kv: kv[1], reverse=True)[:max_files]
    if files:
        lines.append("\nFiles I edited most:")
        lines.extend(f"- {path} ({count}x)" for path, count in files)
    if session.get("last_assistant"):
        lines.append(f"\nYour last message was:\n> {_clip(session['last_assistant'], 700)}")
    lines.append("\nRead the current state of those files and git status, then continue from there.")
    return "\n".join(lines)


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"
