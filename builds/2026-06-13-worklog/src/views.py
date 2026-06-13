"""
Evidence-backed view renderers: standup, resume, why.

Each renderer takes ledger query results and formats them as plaintext.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from src.ledger import (
    query_decisions,
    query_events,
    query_workstreams,
    get_latest_event_of_type,
)
from src.freshness import check_freshness, FreshnessReport


def _parse_ts(ts: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S+00:00", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _since_timestamp(days: int) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")


def _meta(event: dict) -> dict:
    raw = event.get("metadata")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return raw or {}


def _short_ref(event: dict) -> str:
    ref = event.get("source_ref") or ""
    if event["type"] == "commit" and len(ref) >= 7:
        return ref[:7]
    return ref[:20] if ref else event["id"][:12]


def render_standup(
    db_path,
    project_id: str,
    since_days: int = 1,
) -> str:
    """
    Produce a standup-style report grouping recent events into:
    done / in-progress / blocked / next.
    """
    since = _since_timestamp(since_days)
    events = query_events(db_path, project_id, since=since, limit=200)

    if not events:
        return f"No events recorded in the last {since_days} day(s).\n"

    workstreams = {ws["id"]: ws for ws in query_workstreams(db_path, project_id)}

    # Group events by workstream
    ws_events: dict[str, list[dict]] = {}
    for evt in events:
        ws_id = evt.get("workstream_id") or "uncorrelated"
        ws_events.setdefault(ws_id, []).append(evt)

    done: list[str] = []
    in_progress: list[str] = []
    blocked: list[str] = []
    next_items: list[str] = []

    for ws_id, evts in ws_events.items():
        ws_title = (workstreams.get(ws_id) or {}).get("title") or ws_id

        # Classify by the most severe status in this workstream
        statuses = {e.get("status") for e in evts}
        has_open = "open" in statuses
        has_failed = "failed" in statuses
        has_completed = "completed" in statuses or "merged" in statuses or "closed" in statuses

        # Collect evidence lines (deduplicated summaries)
        seen_summaries: set[str] = set()
        lines: list[str] = []
        for evt in sorted(evts, key=lambda e: e.get("timestamp") or "", reverse=True):
            summary = (evt.get("summary") or "").strip()
            if summary and summary not in seen_summaries:
                seen_summaries.add(summary)
                lines.append(f"  [{_short_ref(evt)}] {summary}")

        section_text = f"**{ws_title}**\n" + "\n".join(lines[:5])

        if has_failed:
            blocked.append(section_text)
        elif has_open and not has_completed:
            in_progress.append(section_text)
        elif has_completed and not has_open:
            done.append(section_text)
        else:
            in_progress.append(section_text)

    # Collect next_steps from recent checkpoints
    checkpoints = query_events(db_path, project_id, since=since, event_type="checkpoint", limit=10)
    for ckpt in checkpoints:
        meta = _meta(ckpt)
        for step in meta.get("next_steps") or []:
            next_items.append(f"  • {step} [from checkpoint {ckpt['id'][:12]}]")

    lines_out = [f"# Standup — last {since_days} day(s)\n"]
    if done:
        lines_out.append("## Done\n" + "\n\n".join(done))
    if in_progress:
        lines_out.append("## In Progress\n" + "\n\n".join(in_progress))
    if blocked:
        lines_out.append("## Blocked\n" + "\n\n".join(blocked))
    if next_items:
        lines_out.append("## Next\n" + "\n".join(next_items))

    return "\n\n".join(lines_out) + "\n"


def render_resume(
    db_path,
    project_id: str,
    workstream_id: Optional[str],
    git_root,
) -> str:
    """
    Produce a resumption brief for a fresh agent or human.
    Includes freshness warnings when HEAD has moved on.
    """
    freshness = check_freshness(db_path, project_id, git_root)
    lines_out: list[str] = ["# Resume Brief\n"]

    # Freshness warnings at top
    for w in freshness.warning_lines():
        lines_out.append(w)
    if freshness.warning_lines():
        lines_out.append("")

    # Determine scope: single workstream or most-recent checkpoint's workstream
    target_ws_id = workstream_id
    if not target_ws_id:
        recent_ckpt = get_latest_event_of_type(db_path, project_id, "checkpoint")
        if recent_ckpt:
            target_ws_id = recent_ckpt.get("workstream_id")

    if target_ws_id:
        events = query_events(db_path, project_id, workstream_id=target_ws_id, limit=100)
        decisions = query_decisions(db_path, workstream_id=target_ws_id)
        ws_label = target_ws_id
    else:
        events = query_events(db_path, project_id, limit=50)
        decisions = query_decisions(db_path)
        ws_label = "recent activity"

    lines_out.append(f"## Workstream: {ws_label}\n")

    # Objective from checkpoint
    checkpoints = [e for e in events if e["type"] == "checkpoint"]
    if checkpoints:
        latest_ckpt = max(checkpoints, key=lambda e: e.get("timestamp") or "")
        meta = _meta(latest_ckpt)
        lines_out.append(f"**Objective:** {latest_ckpt.get('summary') or '—'}\n")

        if meta.get("accomplished"):
            lines_out.append("**Accomplished:**")
            for item in meta["accomplished"]:
                lines_out.append(f"  - {item}")
            lines_out.append("")

        if meta.get("unresolved"):
            lines_out.append("**Unresolved:**")
            for item in meta["unresolved"]:
                lines_out.append(f"  - {item}")
            lines_out.append("")

        if meta.get("next_steps"):
            lines_out.append("**Next steps:**")
            for step in meta["next_steps"]:
                lines_out.append(f"  - {step}")
            lines_out.append("")

        if meta.get("files"):
            lines_out.append(f"**Relevant files:** {', '.join(meta['files'][:10])}\n")

    # Decisions
    if decisions:
        lines_out.append("**Decisions made:**")
        for dec in decisions[:5]:
            alts = json.loads(dec.get("alternatives") or "[]")
            lines_out.append(f"  - {dec['summary']}")
            if dec.get("reason"):
                lines_out.append(f"    Reason: {dec['reason']}")
            if alts:
                for a in alts:
                    lines_out.append(f"    Rejected: {a}")
        lines_out.append("")

    # Recent commits
    commits = [e for e in events if e["type"] == "commit"][:5]
    if commits:
        lines_out.append("**Recent commits:**")
        for c in sorted(commits, key=lambda e: e.get("timestamp") or "", reverse=True):
            lines_out.append(f"  [{_short_ref(c)}] {c.get('summary') or ''}")
        lines_out.append("")

    # GitHub state
    prs = [e for e in events if e["type"] == "pull_request" and e.get("status") == "open"]
    if prs:
        lines_out.append("**Open PRs:**")
        for pr in prs[:3]:
            url = pr.get("source_url") or ""
            lines_out.append(f"  {pr.get('summary') or pr['id']} {url}")
        lines_out.append("")

    # Source session refs
    if checkpoints:
        lines_out.append("**Source session IDs:**")
        for ckpt in checkpoints[:3]:
            meta = _meta(ckpt)
            sid = meta.get("session_id") or "—"
            lines_out.append(f"  {ckpt['actor_name']} session {sid} [{ckpt['id'][:12]}]")
        lines_out.append("")

    lines_out.append(
        f"*Generated from ledger — {len(events)} event(s). "
        f"Run `worklog sync` before this if you have not synced recently.*"
    )

    return "\n".join(lines_out) + "\n"


def render_why(
    db_path,
    project_id: str,
    query: str,
) -> str:
    """
    Search decisions by keyword and display each with rationale and evidence.
    """
    decisions = query_decisions(db_path, keyword=query)

    if not decisions:
        return f"No decisions found matching '{query}'.\n"

    lines_out = [f"# Why: '{query}'\n", f"{len(decisions)} decision(s) found.\n"]

    for dec in decisions:
        alts = []
        try:
            alts = json.loads(dec.get("alternatives") or "[]")
        except Exception:
            pass

        lines_out.append(f"## {dec['summary']}")
        lines_out.append(f"**Recorded:** {(dec.get('timestamp') or '')[:10]}")
        if dec.get("reason"):
            lines_out.append(f"**Reason:** {dec['reason']}")
        if alts:
            lines_out.append("**Alternatives rejected:**")
            for a in alts:
                lines_out.append(f"  - {a}")
        ws = dec.get("workstream_id")
        if ws:
            lines_out.append(f"**Workstream:** {ws}")
        lines_out.append(f"**Event:** {dec.get('event_id') or '—'}")
        lines_out.append("")

    return "\n".join(lines_out)


def render_workstreams(db_path, project_id: str) -> str:
    """List all workstreams with event counts."""
    workstreams = query_workstreams(db_path, project_id)
    if not workstreams:
        return "No workstreams found. Run `worklog sync` first.\n"

    lines_out = [f"# Workstreams ({len(workstreams)} total)\n"]
    lines_out.append(f"{'ID':<22} {'Title':<35} {'Status':<10} {'Events':>6}")
    lines_out.append("-" * 78)
    for ws in workstreams:
        ws_id = ws["id"][:20]
        title = (ws.get("title") or "")[:33]
        status = (ws.get("status") or "")[:8]
        count = ws.get("event_count", 0)
        lines_out.append(f"{ws_id:<22} {title:<35} {status:<10} {count:>6}")

    return "\n".join(lines_out) + "\n"


def render_events(
    db_path,
    project_id: str,
    since_days: Optional[int],
    event_type: Optional[str],
    workstream_id: Optional[str],
) -> str:
    """Show raw events with provenance for inspection."""
    since = _since_timestamp(since_days) if since_days else None
    events = query_events(
        db_path,
        project_id,
        since=since,
        event_type=event_type,
        workstream_id=workstream_id,
        limit=100,
    )

    if not events:
        return "No events found matching the given filters.\n"

    lines_out = [f"# Events ({len(events)} shown)\n"]
    for evt in events:
        ts = (evt.get("timestamp") or "")[:19]
        etype = evt.get("type") or ""
        summary = (evt.get("summary") or "")[:60]
        ref = _short_ref(evt)
        provider = evt.get("provider") or ""
        ws = (evt.get("workstream_id") or "")[:16]
        lines_out.append(
            f"{ts}  [{etype:<12}] [{provider:<6}] [{ws:<16}] {ref:<10} {summary}"
        )

    return "\n".join(lines_out) + "\n"
