"""Project resume brief: a paste-ready markdown block for starting a new AI session."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from .store import Store
from .summarize import call_claude, heuristic_summary

BRIEF_SYSTEM = (
    "You tighten a project resume brief that will be pasted at the start of a new AI session. "
    "Keep every fact, file path and open item that appears; remove repetition. Plain markdown, no preamble, "
    "no marketing tone."
)


def summary_for(store: Store, session_id: str) -> dict[str, Any]:
    cached = store.get_summary(session_id)
    if cached:
        return cached
    session = store.session_object(session_id)
    return {"kind": "heuristic", **heuristic_summary(session)} if session else {}


def _cutoff(days: int | None) -> str:
    if not days:
        return ""
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")


def build_brief(store: Store, project: str, max_sessions: int = 6, days: int | None = None) -> str:
    sessions = [s for s in store.sessions(project=project, limit=max_sessions * 4)
                if (s["ended"] or "") >= _cutoff(days)][:max_sessions]
    if not sessions:
        return f"# {project}: resume brief\n\nNo sessions found."
    summaries = [(s, summary_for(store, s["id"])) for s in sessions]
    file_counts: Counter[str] = Counter(f for s, _ in summaries for f in s["files"])
    open_items = list(dict.fromkeys(i for _, sm in summaries for i in sm.get("open_items", [])))
    decisions = list(dict.fromkeys(d for _, sm in summaries for d in sm.get("decisions", [])))

    out = [f"# {project}: resume brief", "",
           f"Built from the {len(summaries)} most recent AI sessions on this project (newest first).", ""]
    latest_sm = summaries[0][1]
    if latest_sm.get("left_off"):
        out += ["## Where the last session stopped", latest_sm["left_off"], ""]
    if open_items:
        out += ["## Open items", *[f"- {item}" for item in open_items[:12]], ""]
    if decisions:
        out += ["## Decisions made", *[f"- {item}" for item in decisions[:10]], ""]
    if file_counts:
        out += ["## Files touched most", *[f"- `{path}` ({n} session{'s' if n != 1 else ''})" for path, n in file_counts.most_common(10)], ""]
    out += ["## Recent sessions"]
    for session, summary in summaries:
        date = (session["ended"] or session["started"] or "")[:10] or "undated"
        out.append(f"- **{date}**, {summary.get('title') or session['title']} ({session['source']}, "
                   f"{session['msg_count']} msgs): {summary.get('summary', '')}")
    return "\n".join(out).rstrip() + "\n"


def ai_brief(store: Store, project: str, api_key: str | None = None,
             post: Callable[..., dict[str, Any]] | None = None, **kwargs: Any) -> str:
    base = build_brief(store, project, **kwargs)
    extra = {"post": post} if post else {}
    result = call_claude(BRIEF_SYSTEM, base, api_key, max_tokens=1800, **extra).strip()
    store.save_brief(project, "ai", result)
    return result
