"""Build a markdown 'resume brief' for a project from indexed sessions."""
from __future__ import annotations

from . import store

MAX_SESSIONS = 5


def _dedupe(items: list[str]) -> list[str]:
    seen, out = set(), []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def build_brief(conn, project: str, max_sessions: int = MAX_SESSIONS) -> str | None:
    sessions = store.list_sessions(conn, project)[:max_sessions]
    if not sessions:
        return None
    latest = sessions[0]
    lines = [f"# Resume brief: {project}", "",
             f"Last active {latest['ended'][:16].replace('T', ' ')} UTC"
             + (f" on branch `{latest['branch']}`" if latest["branch"] else "") + ".", ""]
    threads = _dedupe([t for s in sessions if s["summary"] for t in s["summary"]["open_threads"]])
    steps = _dedupe([t for s in sessions if s["summary"] for t in s["summary"]["next_steps"]])
    decisions = _dedupe([t for s in sessions if s["summary"] for t in s["summary"]["decisions"]])
    unsummarized = sum(1 for s in sessions if not s["summary"])
    if threads:
        lines += ["## Open threads", *[f"- {t}" for t in threads], ""]
    if steps:
        lines += ["## Suggested next steps", *[f"- {t}" for t in steps], ""]
    if decisions:
        lines += ["## Decisions already made", *[f"- {t}" for t in decisions], ""]
    if not (threads or steps or decisions):
        lines += ["_No AI summaries yet — run `summarize` for open threads and decisions._", ""]
    lines += ["## Recent sessions"]
    for s in sessions:
        goal = (s["summary"] or {}).get("goal") or s["first_prompt"][:140]
        lines.append(f"- {s['ended'][:10]} — **{s['title']}** ({s['msg_count']} msgs): {goal}")
    ids = [s["id"] for s in sessions]
    marks = ",".join("?" * len(ids))
    files = conn.execute(
        f"SELECT path, SUM(touches) AS n FROM session_files WHERE session_id IN ({marks}) "
        "GROUP BY path ORDER BY n DESC, path LIMIT 10", ids).fetchall()
    if files:
        lines += ["", "## Files touched most", *[f"- `{r['path']}` ({r['n']}×)" for r in files]]
    if unsummarized and (threads or steps or decisions):
        lines += ["", f"_{unsummarized} of these sessions have no AI summary yet._"]
    return "\n".join(lines) + "\n"
