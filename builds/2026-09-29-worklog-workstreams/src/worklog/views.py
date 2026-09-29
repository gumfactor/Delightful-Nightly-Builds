"""Evidence-backed views. Every claim carries a citation; provenance is labelled.

Labels:  [recorded] stored source event   [observed] read from the checkout/last sync
         [inferred] heuristic, may be wrong   [STALE] recorded state no longer matches the repo
"""
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from .correlate import Workstream
from .freshness import _tokens, is_stale
from .project import WorklogError

LEGEND = "Legend: [recorded] from source events · [observed] read from checkout · [inferred] heuristic · [STALE] out of date"
SUPERSEDE_OVERLAP = 0.6


def parse_since(text: str, now: Optional[datetime] = None) -> str:
    """'yesterday', 'today', '3d', '12h', '2 weeks', '2026-09-01' -> UTC ISO timestamp."""
    now = now or datetime.now(timezone.utc)
    lowered = text.strip().lower()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if lowered == "today":
        start = midnight
    elif lowered == "yesterday":
        start = midnight - timedelta(days=1)
    else:
        match = re.fullmatch(r"(\d+)\s*(h|hour|hours|d|day|days|w|week|weeks)", lowered)
        if match:
            unit = {"h": "hours", "d": "days", "w": "weeks"}[match.group(2)[0]]
            start = now - timedelta(**{unit: int(match.group(1))})
        else:
            try:
                start = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
            except ValueError as exc:
                raise WorklogError(f"cannot understand --since {text!r} (try 'yesterday', '3d', or 2026-09-01)") from exc
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
    return start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cite(event: dict) -> str:
    """Compact, resolvable citation: `[commit abc1234 | evt_1a2b3c4d]`."""
    meta = event["metadata"]
    if event["type"] == "commit":
        label = f"commit {event['ref'][:7]}"
    elif event["type"] in ("pr", "issue", "review"):
        label = f"{event['type']} #{meta.get('number', '?')}"
    elif event["type"] == "ci":
        label = f"ci {meta.get('name', '')}".strip()
    elif event["type"] == "checkpoint":
        label = f"{event['provider']} session {(meta.get('session_id') or event['ref'])[:12]}"
    else:
        label = event["type"]
    return f"[{label} | {event['id'][:12]}]"


def _cites(events: list[dict], limit: int = 4) -> str:
    shown = " ".join(cite(e) for e in events[:limit])
    return shown + (f" +{len(events) - limit} more" if len(events) > limit else "")


def decision_states(ws: Workstream) -> list[tuple[dict, Optional[dict]]]:
    """Pair each decision with the later decision that supersedes it (or None)."""
    decisions = ws.by_type("decision")
    out = []
    for i, decision in enumerate(decisions):
        superseder = None
        own = _tokens(decision["summary"])
        for later in decisions[i + 1:]:
            target = _tokens(later["metadata"].get("supersedes") or "")
            if target and own and len(target & own) / len(target) >= SUPERSEDE_OVERLAP:
                superseder = later
        out.append((decision, superseder))
    return out


def _activity_line(ws: Workstream, since: Optional[str]) -> str:
    events = [e for e in ws.events if not since or e["ts"] >= since]
    commits = [e for e in events if e["type"] == "commit"]
    parts = []
    if commits:
        ins = sum(c["metadata"].get("insertions", 0) for c in commits)
        dele = sum(c["metadata"].get("deletions", 0) for c in commits)
        files = {f for c in commits for f in c["files"]}
        parts.append(f"{len(commits)} commit(s), {len(files)} file(s), +{ins}/-{dele}")
    for event in events:
        if event["type"] in ("pr", "issue") and event["ref"].endswith((":merged", ":closed", ":opened")):
            parts.append(event["summary"].split(":")[0])
    ci = [e for e in events if e["type"] == "ci"]
    if ci:
        parts.append(f"CI {ci[-1]['status']}")
    return "; ".join(dict.fromkeys(parts)) or "activity recorded"


def standup_data(workstreams: list[Workstream], findings_by_ws: dict[str, list[dict]], since: str) -> dict:
    sections: dict[str, list[dict]] = {"completed": [], "in_progress": [], "blocked": [], "next": []}
    for ws in workstreams:
        recent = [e for e in ws.events if e["ts"] >= since]
        if not recent:
            continue
        findings = findings_by_ws.get(ws.id, [])
        item = {"id": ws.id, "title": ws.title, "activity": _activity_line(ws, since),
                "accomplished": [a for cp in ws.by_type("checkpoint") if cp["ts"] >= since
                                 for a in cp["metadata"].get("accomplished", [])],
                "evidence": [e["id"] for e in recent], "stale": is_stale(findings),
                "cites": _cites([e for e in recent if e["type"] != "decision"])}
        if ws.status == "blocked":
            item["blockers"] = [b["reason"] + f" ({b['kind']})" for b in ws.blockers]
        sections[ws.status if ws.status in sections else "in_progress"].append(item)
        checkpoints = ws.by_type("checkpoint")
        if ws.status != "completed" and checkpoints and checkpoints[-1]["metadata"].get("next_steps"):
            sections["next"].append({"id": ws.id, "title": ws.title, "steps": checkpoints[-1]["metadata"]["next_steps"],
                                     "stale": is_stale(findings), "cites": cite(checkpoints[-1])})
    return sections


def render_standup(data: dict, since: str) -> str:
    lines = [f"# Standup since {since}", LEGEND, ""]
    titles = {"completed": "Completed", "in_progress": "In progress", "blocked": "Blocked", "next": "Next"}
    for key in ("completed", "in_progress", "blocked", "next"):
        lines.append(f"## {titles[key]}")
        if not data[key]:
            lines += ["- (none)", ""]
            continue
        for item in data[key]:
            stale = " [STALE]" if item["stale"] else ""
            if key == "next":
                lines.append(f"- {item['title']}{stale} {item['cites']}")
                lines += [f"    - {step}" for step in item["steps"]]
                continue
            lines.append(f"- {item['title']} — {item['activity']}{stale} [recorded]")
            for done in item["accomplished"]:
                lines.append(f"    - {done}")
            for blocker in item.get("blockers", []):
                lines.append(f"    - BLOCKED: {blocker}")
            lines.append(f"    evidence: {item['cites']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def top_files(ws: Workstream, limit: int = 12) -> list[tuple[str, int]]:
    counts = Counter(f for e in ws.events if e["type"] in ("commit", "checkpoint") for f in e["files"])
    return counts.most_common(limit)


def resume_data(ws: Workstream, findings: list[dict], observed: dict, synced_at: Optional[str]) -> dict:
    checkpoints = ws.by_type("checkpoint")
    latest = checkpoints[-1] if checkpoints else None
    next_steps = list(latest["metadata"].get("next_steps", [])) if latest else []
    maybe_done = {f["text"].split("'")[1] for f in findings if f["text"].startswith("inferred: next step '")}
    files = {f for f, _ in top_files(ws, 200)}
    overlap = sorted(set(observed.get("dirty", []) + observed.get("untracked", [])) & files)
    return {
        "id": ws.id, "objective": ws.title, "status": ws.status, "stale": is_stale(findings),
        "blockers": ws.blockers, "findings": findings,
        "decisions": [{"summary": d["summary"], "reason": d["metadata"].get("reason"),
                       "rejected": d["metadata"].get("rejected", []), "files": d["files"],
                       "superseded_by": s["summary"] if s else None, "cite": cite(d)}
                      for d, s in decision_states(ws)],
        "accomplished": [a for cp in checkpoints for a in cp["metadata"].get("accomplished", [])],
        "unresolved": list(latest["metadata"].get("unresolved", [])) if latest else [],
        "next_steps": [{"step": step, "maybe_done": step in maybe_done} for step in next_steps],
        "files": top_files(ws), "observed": {**observed, "dirty_overlap": overlap}, "synced_at": synced_at,
        "sessions": [{"provider": cp["provider"], "session": cp["metadata"].get("session_id"), "at": cp["ts"],
                      "cite": cite(cp)} for cp in checkpoints],
        "commits": [cite(c) for c in ws.by_type("commit")][-8:],
        "github": [e["summary"] + " " + cite(e) for e in ws.by_type("pr", "issue")
                   if e["ref"].endswith((":opened", ":merged", ":closed"))],
        "ci": [e["summary"] + " " + cite(e) for e in ws.by_type("ci")][-3:],
        "links": [{"kind": ln.kind, "rationale": ln.rationale, "confidence": ln.confidence} for ln in ws.links],
    }


def render_resume(data: dict) -> str:
    out = [f"# Resume: {data['objective']}", LEGEND, ""]
    out.append(f"Workstream {data['id']} · status: {data['status']} [recorded]")
    if data["stale"]:
        out.append("WARNING [STALE]: recorded agent state is out of date — verify before acting (see Freshness).")
    out += ["", "## Freshness"]
    empty = "- checkpoints match the repository [observed]" if data["sessions"] else "- no agent checkpoints recorded"
    out += [f"- [{f['level'].upper()}] {f['text']}" for f in data["findings"]] or [empty]
    out += ["", "## Decisions that constrain the work"]
    live = [d for d in data["decisions"] if not d["superseded_by"]]
    for d in live:
        out.append(f"- {d['summary']} [recorded] {d['cite']}")
        if d["reason"]:
            out.append(f"    why: {d['reason']}")
        if d["rejected"]:
            out.append(f"    rejected: {'; '.join(d['rejected'])}")
    out += ["- (none recorded)"] if not live else []
    for d in data["decisions"]:
        if d["superseded_by"]:
            out.append(f"- SUPERSEDED: {d['summary']} → by '{d['superseded_by']}' {d['cite']}")
    out += ["", "## Done so far"] + [f"- {a} [recorded]" for a in data["accomplished"]]
    out += ["- (no accomplishments recorded)"] if not data["accomplished"] else []
    out += ["", "## Unresolved / blockers"]
    out += [f"- BLOCKER ({b['kind']}): {b['reason']} [recorded]" for b in data["blockers"]]
    out += [f"- {u} [recorded]" for u in data["unresolved"]]
    out += ["- (none)"] if not data["blockers"] and not data["unresolved"] else []
    out += ["", "## Next actions"]
    for step in data["next_steps"]:
        out.append(f"- {step['step']} [recorded]" + ("  [inferred: a later commit may have done this]" if step["maybe_done"] else ""))
    out += ["- (no next steps recorded)"] if not data["next_steps"] else []
    out += ["", "## Relevant files"] + [f"- {path} (touched {count}x) [recorded]" for path, count in data["files"]]
    obs = data["observed"]
    out += ["", "## Current repository state [observed]",
            f"- branch {obs.get('branch')} at {(obs.get('head') or 'none')[:8]}",
            f"- uncommitted: {', '.join(obs.get('dirty', [])[:8]) or 'none'}"]
    if obs.get("dirty_overlap"):
        out.append(f"- uncommitted changes touching this workstream's files: {', '.join(obs['dirty_overlap'][:8])}")
    out += ["", f"## GitHub state [recorded as of last sync {data['synced_at'] or 'never'}]"]
    out += [f"- {line}" for line in data["github"] + data["ci"]] or ["- none recorded (Git-only or not synced)"]
    out += ["", "## Evidence"]
    out += [f"- session {s['cite']} at {s['at']}" for s in data["sessions"]]
    out += [f"- {c}" for c in data["commits"]]
    out += [f"- link ({ln['kind']}, {ln['confidence']}): {ln['rationale']}" for ln in data["links"]]
    return "\n".join(out) + "\n"


def why_data(workstreams: list[Workstream], query: str, only: Optional[Workstream] = None) -> dict:
    terms = [t for t in re.findall(r"[a-z0-9_]+", query.lower()) if t]
    matches, commit_hits = [], []
    for ws in (workstreams if only is None else [only]):
        states = {d["id"]: s for d, s in decision_states(ws)}
        for event in ws.by_type("decision", "note"):
            meta = event["metadata"]
            haystack = " ".join([event["summary"], str(meta.get("reason") or ""), " ".join(meta.get("rejected") or []),
                                 str(meta.get("supersedes") or "")]).lower()
            if terms and all(t in haystack for t in terms):
                later = [e for e in ws.events if e["ts"] > event["ts"] and e["id"] != event["id"]
                         and (set(e["files"]) & set(event["files"]) or e["type"] in ("ci",))]
                passed = [e for e in later if e["type"] == "ci" and e["status"] == "completed"]
                failed = [e for e in later if e["type"] == "ci" and e["status"] == "failed"]
                superseder = states.get(event["id"])
                matches.append({
                    "decision": event["summary"], "reason": meta.get("reason"), "rejected": meta.get("rejected", []),
                    "workstream": ws.title, "workstream_id": ws.id, "at": event["ts"], "by": event["actor_name"],
                    "cite": cite(event), "superseded_by": superseder["summary"] if superseder else None,
                    "superseded_cite": cite(superseder) if superseder else None,
                    "later_evidence": [cite(e) + " " + e["summary"] for e in later if e["type"] != "ci"][:5],
                    "confirmed_by": [cite(e) for e in passed][:3], "contradicted_by": [cite(e) for e in failed][:3]})
        for event in ws.by_type("commit"):
            if terms and all(t in event["summary"].lower() for t in terms):
                commit_hits.append(f"{event['summary']} {cite(event)}")
    return {"query": query, "matches": matches, "commit_mentions": commit_hits[:8]}


def render_why(data: dict) -> str:
    out = [f"# Why: {data['query']}", LEGEND, ""]
    if not data["matches"]:
        out.append("No recorded decision matches. Nothing is being inferred as a decision.")
    for m in data["matches"]:
        out.append(f"## {m['decision']}")
        out.append(f"- workstream: {m['workstream']} ({m['workstream_id']}) · recorded {m['at']} by {m['by']} {m['cite']} [recorded]")
        out.append(f"- rationale: {m['reason'] or '(none recorded)'}")
        if m["rejected"]:
            out.append(f"- alternatives rejected: {'; '.join(m['rejected'])}")
        if m["superseded_by"]:
            out.append(f"- SUPERSEDED by: {m['superseded_by']} {m['superseded_cite']}")
        if m["confirmed_by"]:
            out.append(f"- later passing CI on this workstream: {' '.join(m['confirmed_by'])} [inferred support]")
        if m["contradicted_by"]:
            out.append(f"- later failing CI: {' '.join(m['contradicted_by'])} [inferred: may contradict]")
        out += [f"- later change: {line}" for line in m["later_evidence"]]
        out.append("")
    if data["commit_mentions"]:
        out.append("## Commits mentioning the query (not decisions) [recorded]")
        out += [f"- {line}" for line in data["commit_mentions"]]
    return "\n".join(out).rstrip() + "\n"


def render_timeline(ws: Workstream) -> str:
    out = [f"# Timeline: {ws.title}", LEGEND, f"Workstream {ws.id} · {ws.status} · {ws.first_ts} → {ws.last_ts}", ""]
    for event in ws.events:
        out.append(f"{event['ts']}  {event['type']:<10} {event['actor_kind']}:{event['actor_name']}  "
                   f"{event['summary']}  {cite(event)}")
    out += ["", "## Why these events are grouped"]
    for link in ws.links:
        tag = "confirmed" if link.kind == "confirmed" else "[inferred]"
        out.append(f"- {tag} {link.signal} ({link.confidence}): {link.rationale}")
    if not ws.links:
        out.append("- single event")
    if ws.suggestions:
        out += ["", "## Possible links (NOT applied — use `worklog merge` to accept)"]
        out += [f"- {s.rationale}; events {', '.join(i[:12] for i in s.events[:4])}" for s in ws.suggestions]
    return "\n".join(out) + "\n"


def render_workstreams(workstreams: list[Workstream]) -> str:
    if not workstreams:
        return "No workstreams yet. Run `worklog sync` first.\n"
    lines = [f"{'ID':<11} {'STATUS':<12} {'LAST ACTIVITY':<21} {'EVENTS':>6}  TITLE"]
    for ws in workstreams:
        inferred = " (inferred links)" if any(ln.kind == "inferred" for ln in ws.links) else ""
        lines.append(f"{ws.id:<11} {ws.status:<12} {ws.last_ts:<21} {len(ws.events):>6}  {ws.title[:70]}{inferred}")
    return "\n".join(lines) + "\n"
