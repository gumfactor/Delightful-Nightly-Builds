"""Evidence-backed read views over the ledger: standup, resume, why, timeline, search."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import util
from .ledger import Event, Ledger
from .project import ProjectState, is_ancestor


# ------------------------------- standup -----------------------------------------------------

@dataclass
class StandupReport:
    since: str
    completed: list = field(default_factory=list)   # [{workstream_id, title, commit_count, latest_summary}]
    in_progress: list = field(default_factory=list)  # [{workstream_id, title, detail}]
    blocked: list = field(default_factory=list)      # [{workstream_id, title, reason}]
    next_actions: list = field(default_factory=list)  # [{workstream_id, title, step}]


def standup(ledger: Ledger, project_id: str, since_text: str = "24h") -> StandupReport:
    cutoff = util.parse_since(since_text)
    report = StandupReport(since=since_text)

    # Completed: commits since cutoff, grouped by workstream.
    by_ws: dict[str, list[Event]] = {}
    for event in ledger.events_for_project(project_id, "commit"):
        if util.parse_iso(event.timestamp) < cutoff or not event.workstream_id:
            continue
        by_ws.setdefault(event.workstream_id, []).append(event)
    for ws_id, events in by_ws.items():
        ws = ledger.get_workstream(ws_id)
        title = ws["title"] if ws else ws_id
        latest = max(events, key=lambda e: e.timestamp)
        report.completed.append(
            {
                "workstream_id": ws_id,
                "title": title,
                "commit_count": len(events),
                "latest_summary": latest.summary,
            }
        )

    # In-progress / blocked / next: driven by the latest checkpoint per workstream.
    latest_checkpoint_by_ws: dict[str, Event] = {}
    for event in ledger.events_for_project(project_id, "checkpoint"):
        if not event.workstream_id:
            continue
        current = latest_checkpoint_by_ws.get(event.workstream_id)
        if current is None or event.timestamp > current.timestamp:
            latest_checkpoint_by_ws[event.workstream_id] = event

    for ws_id, event in latest_checkpoint_by_ws.items():
        ws = ledger.get_workstream(ws_id)
        title = ws["title"] if ws else ws_id
        failed_validation = [
            v for v in event.metadata.get("validation", []) if v.get("result") != "passed"
        ]
        if failed_validation:
            report.blocked.append(
                {
                    "workstream_id": ws_id,
                    "title": title,
                    "reason": f"{len(failed_validation)} failing validation step(s): "
                    + "; ".join(v.get("command", "?") for v in failed_validation),
                }
            )
        elif event.metadata.get("unresolved") or event.metadata.get("next_steps"):
            detail = event.metadata.get("unresolved") or event.metadata.get("next_steps")
            report.in_progress.append(
                {"workstream_id": ws_id, "title": title, "detail": detail[0] if detail else ""}
            )
        for step in event.metadata.get("next_steps", []):
            report.next_actions.append({"workstream_id": ws_id, "title": title, "step": step})

    return report


# ------------------------------- resume ------------------------------------------------------

@dataclass
class ResumePackage:
    workstream_id: Optional[str]
    title: str
    objective: str
    decisions: list = field(default_factory=list)
    unresolved: list = field(default_factory=list)
    next_steps: list = field(default_factory=list)
    files: list = field(default_factory=list)
    event_count: int = 0
    source_event_ids: list = field(default_factory=list)
    head_stale: bool = False
    head_stale_detail: str = ""
    dirty_now: list = field(default_factory=list)
    untracked_now: list = field(default_factory=list)
    stale_checkpoints: list = field(default_factory=list)  # [{event_id, commit_ref}]
    no_data: bool = False


def _most_recently_active_workstream(ledger: Ledger, project_id: str) -> Optional[str]:
    workstreams = ledger.workstreams_for_project(project_id)
    return workstreams[0]["id"] if workstreams else None


def resume(ledger: Ledger, project: ProjectState, workstream_id: Optional[str] = None) -> ResumePackage:
    project_id = project.project_id
    if workstream_id is None:
        workstream_id = _most_recently_active_workstream(ledger, project_id)

    if workstream_id is None:
        return ResumePackage(workstream_id=None, title="", objective="", no_data=True)

    ws = ledger.get_workstream(workstream_id)
    title = ws["title"] if ws else workstream_id
    events = ledger.events_for_workstream(workstream_id)

    package = ResumePackage(workstream_id=workstream_id, title=title, objective=title)
    package.event_count = len(events)
    package.source_event_ids = [e.id for e in events]

    files: set = set()
    for event in events:
        if event.type == "checkpoint":
            package.objective = event.summary
            package.unresolved.extend(event.metadata.get("unresolved", []))
            package.next_steps.extend(event.metadata.get("next_steps", []))
            files.update(event.metadata.get("files", []))
            commit_ref = event.metadata.get("commit_ref")
            if commit_ref and project.head_sha and not is_ancestor(project.repo_root, commit_ref, project.head_sha):
                package.stale_checkpoints.append({"event_id": event.id, "commit_ref": commit_ref})
        elif event.type == "decision":
            package.decisions.append({"summary": event.summary, "reason": event.metadata.get("reason", "")})
        elif event.type == "commit":
            files.update(event.metadata.get("files", []))

    package.files = sorted(files)

    recorded_head = ledger.get_state(project_id, "last_sync_head")
    if recorded_head and project.head_sha and recorded_head != project.head_sha:
        package.head_stale = True
        package.head_stale_detail = f"recorded HEAD {recorded_head[:10]}, current HEAD {project.head_sha[:10]}"

    package.dirty_now = project.dirty_files
    package.untracked_now = project.untracked_files
    return package


# ------------------------------- why ---------------------------------------------------------

@dataclass
class WhyResult:
    decision_summary: str
    reason: str
    workstream_id: Optional[str]
    workstream_title: str
    source_event_id: str
    later_events: list = field(default_factory=list)  # [summary strings]


def why(ledger: Ledger, project_id: str, query: str) -> list[WhyResult]:
    query_lower = query.lower()
    results = []
    for event in ledger.events_for_project(project_id, "decision"):
        haystack = f"{event.summary} {event.metadata.get('reason', '')}".lower()
        if query_lower not in haystack:
            continue
        ws = ledger.get_workstream(event.workstream_id) if event.workstream_id else None
        later = []
        if event.workstream_id:
            for other in ledger.events_for_workstream(event.workstream_id):
                if other.timestamp > event.timestamp and other.id != event.id:
                    later.append(f"[{other.type}] {other.summary}")
        results.append(
            WhyResult(
                decision_summary=event.summary,
                reason=event.metadata.get("reason", ""),
                workstream_id=event.workstream_id,
                workstream_title=ws["title"] if ws else "(uncorrelated)",
                source_event_id=event.metadata.get("checkpoint_event_id", event.id),
                later_events=later,
            )
        )
    return results


# ------------------------------- other views --------------------------------------------------

def timeline(ledger: Ledger, project_id: str, workstream_id: Optional[str] = None) -> list[Event]:
    if workstream_id:
        return ledger.events_for_workstream(workstream_id)
    return ledger.events_for_project(project_id)


def workstreams_view(ledger: Ledger, project_id: str) -> list[dict]:
    out = []
    for ws in ledger.workstreams_for_project(project_id):
        events = ledger.events_for_workstream(ws["id"])
        signals = {e.correlation.get("signal") for e in events if e.correlation}
        out.append(
            {
                "id": ws["id"],
                "title": ws["title"],
                "event_count": len(events),
                "updated_at": ws["updated_at"],
                "signals": sorted(s for s in signals if s),
            }
        )
    return out


def show_event(ledger: Ledger, event_id: str) -> Optional[Event]:
    return ledger.get_event(event_id)


def search(ledger: Ledger, project_id: str, query: str) -> list[Event]:
    return ledger.search_events(project_id, query)
