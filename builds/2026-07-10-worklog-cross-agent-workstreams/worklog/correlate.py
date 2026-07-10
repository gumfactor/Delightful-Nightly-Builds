"""Deterministic workstream correlation.

Signal priority (highest confidence first):
  1. explicit_hint   — checkpoint author named the workstream directly
  2. self_anchor     — a GitHub issue/PR is the anchor for its own workstream
  3. issue_reference — event text references an issue/PR number with a known workstream
  4. branch          — event is scoped to a non-default branch already tied to a workstream
  5. file_overlap    — touched files overlap significantly with a recent workstream's commits
  6. general_bucket  — no correlating signal found; grouped by UTC date, low confidence

Every correlation decision is recorded with its signal and confidence so a "guess" is never
presented as a settled fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import util
from .ledger import Ledger
from .project import DEFAULT_BRANCHES

FILE_OVERLAP_THRESHOLD = 0.2
_CONFIDENCE_BY_SIGNAL = {
    "explicit_hint": "high",
    "self_anchor": "high",
    "issue_reference": "high",
    "branch": "medium",
    "file_overlap": "medium",
    "general_bucket": "low",
}


@dataclass
class CorrelationInput:
    timestamp: str
    explicit_hint: str = ""
    issue_refs: Optional[list[int]] = None
    branch: str = ""
    files: Optional[list[str]] = None
    self_anchor_number: Optional[int] = None
    fallback_title: str = ""


def _project_prefix(project_id: str) -> str:
    return util.path_hash(project_id)


def _find_overlap_workstream(ledger: Ledger, project_id: str, files: list[str]) -> Optional[str]:
    if not files:
        return None
    target = set(files)
    best_id, best_score = None, 0.0
    for commit_event in ledger.recent_commit_events(project_id, limit=50):
        commit_files = set(commit_event.metadata.get("files", []))
        if not commit_files or not commit_event.workstream_id:
            continue
        score = util.jaccard(target, commit_files)
        if score > best_score:
            best_score, best_id = score, commit_event.workstream_id
    if best_id and best_score >= FILE_OVERLAP_THRESHOLD:
        return best_id
    return None


def resolve_workstream(ledger: Ledger, project_id: str, params: CorrelationInput) -> tuple[str, dict]:
    prefix = _project_prefix(project_id)
    workstream_id: Optional[str] = None
    title: Optional[str] = None
    signal: Optional[str] = None

    if params.explicit_hint:
        slug = util.slugify(params.explicit_hint)
        workstream_id = f"ws_{prefix}_hint_{slug}"
        title = params.explicit_hint
        signal = "explicit_hint"
    elif params.self_anchor_number is not None:
        workstream_id = f"ws_{prefix}_issue_{params.self_anchor_number}"
        title = params.fallback_title or f"Issue/PR #{params.self_anchor_number}"
        signal = "self_anchor"
    elif params.issue_refs:
        number = params.issue_refs[0]
        existing = ledger.find_workstream_by_issue(project_id, number)
        if existing:
            workstream_id = existing
            signal = "issue_reference"
        else:
            workstream_id = f"ws_{prefix}_issue_{number}"
            title = f"Issue #{number}"
            signal = "issue_reference"
    elif params.branch and params.branch not in DEFAULT_BRANCHES:
        existing = ledger.find_workstream_by_branch(project_id, params.branch)
        if existing:
            workstream_id = existing
            signal = "branch"
        else:
            workstream_id = f"ws_{prefix}_branch_{util.slugify(params.branch)}"
            title = params.branch.replace("-", " ").replace("_", " ").strip().capitalize()
            signal = "branch"
    elif params.files:
        candidate = _find_overlap_workstream(ledger, project_id, params.files)
        if candidate:
            workstream_id = candidate
            signal = "file_overlap"

    if workstream_id is None:
        date_bucket = params.timestamp[:10]
        workstream_id = f"ws_{prefix}_general_{date_bucket}"
        title = f"General activity — {date_bucket}"
        signal = "general_bucket"

    if title is None:
        existing_ws = ledger.get_workstream(workstream_id)
        title = existing_ws["title"] if existing_ws else (params.fallback_title or workstream_id)

    ledger.upsert_workstream(workstream_id, project_id, title, params.timestamp)
    correlation = {"signal": signal, "confidence": _CONFIDENCE_BY_SIGNAL[signal]}
    return workstream_id, correlation
