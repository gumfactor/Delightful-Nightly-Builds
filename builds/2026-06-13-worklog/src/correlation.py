"""
Workstream correlation — groups related events using deterministic signals:
  1. Explicit issue/PR references in commit messages or checkpoint objectives
  2. Branch name extracted from metadata
  3. Overlapping files within a 7-day window
  4. Temporal proximity (< 2 hours between events)

Each workstream is identified by a deterministic slug.  Confidence and
rationale are stored so groupings can be inspected and corrected.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional


_ISSUE_REF = re.compile(r"(?:fixes?|closes?|resolves?|refs?|see)?\s*#(\d+)", re.IGNORECASE)
_PR_REF = re.compile(r"\bpr[- ]?#?(\d+)\b", re.IGNORECASE)


def _parse_ts(ts: str) -> Optional[datetime]:
    """Parse UTC ISO-8601 timestamp string to datetime. Returns None on failure."""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S+00:00", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _slug_from_text(text: str, max_len: int = 40) -> str:
    """Produce a lowercase hyphenated slug from a text string."""
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text).lower()
    words = text.split()[:6]
    return "-".join(words)[:max_len] or "misc"


def _workstream_id(key: str) -> str:
    """Deterministic workstream ID from a correlation key."""
    return "ws_" + hashlib.sha256(key.encode()).hexdigest()[:16]


def _get_files(event: dict) -> list[str]:
    """Extract file list from event metadata."""
    meta = {}
    raw = event.get("metadata")
    if isinstance(raw, str):
        try:
            meta = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    elif isinstance(raw, dict):
        meta = raw
    return meta.get("files_changed") or meta.get("files") or []


def _get_branch(event: dict) -> Optional[str]:
    """Extract branch from event metadata (git commits or PR head_branch)."""
    meta = {}
    raw = event.get("metadata")
    if isinstance(raw, str):
        try:
            meta = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None
    elif isinstance(raw, dict):
        meta = raw
    return meta.get("branch") or meta.get("head_branch")


def _issue_refs(text: str) -> set[str]:
    """Extract issue numbers from commit message or objective text."""
    return {f"issue:{m}" for m in _ISSUE_REF.findall(text or "")}


def correlate_events(events: list[dict]) -> list[dict]:
    """
    Assign workstream IDs to events using deterministic correlation signals.
    Returns a new list of events with 'workstream_id' set.
    Also returns workstream records as a side-effect (embedded in returned events).
    """
    if not events:
        return [], {}

    # Index events by id for mutation
    by_id = {e["id"]: dict(e) for e in events}
    # workstream_id -> {title, evidence list}
    ws_meta: dict[str, dict] = {}

    # --- Pass 1: explicit issue/PR refs ---
    # Commit message or checkpoint objective containing "#42" → issue:42 workstream
    issue_to_ws: dict[str, str] = {}
    for evt in by_id.values():
        refs = _issue_refs(evt.get("summary") or "")
        for ref in refs:
            if ref not in issue_to_ws:
                ws_id = _workstream_id(ref)
                issue_to_ws[ref] = ws_id
                ws_meta.setdefault(ws_id, {"title": f"Work for {ref}", "evidence": []})
                ws_meta[ws_id]["evidence"].append(
                    {"signal": "issue_ref", "value": ref, "confidence": "high"}
                )
            ws_id = issue_to_ws[ref]
            by_id[evt["id"]]["workstream_id"] = ws_id

    # Also check PR metadata for linked issue refs
    for evt in by_id.values():
        if evt["type"] == "pull_request":
            meta = evt.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            head_branch = meta.get("head_branch") or ""
            refs = _issue_refs(head_branch)
            for ref in refs:
                ws_id = issue_to_ws.get(ref) or _workstream_id(ref)
                issue_to_ws.setdefault(ref, ws_id)
                ws_meta.setdefault(ws_id, {"title": f"Work for {ref}", "evidence": []})
                if not by_id[evt["id"]].get("workstream_id"):
                    by_id[evt["id"]]["workstream_id"] = ws_id
                    ws_meta[ws_id]["evidence"].append(
                        {"signal": "branch_issue_ref", "value": head_branch, "confidence": "medium"}
                    )

    # --- Pass 2: branch name grouping ---
    # Commits or dirty_file events on the same non-default branch → same workstream
    branch_to_ws: dict[str, str] = {}
    default_branches = {"main", "master", "develop", "trunk"}
    for evt in by_id.values():
        branch = _get_branch(evt)
        if not branch or branch in default_branches:
            continue
        if evt.get("workstream_id"):
            # Already assigned; map branch to that workstream for consistency
            branch_to_ws.setdefault(branch, evt["workstream_id"])
            continue
        if branch not in branch_to_ws:
            ws_id = _workstream_id(f"branch:{branch}")
            branch_to_ws[branch] = ws_id
            title = _slug_from_text(branch.replace("/", " ").replace("-", " "))
            ws_meta.setdefault(ws_id, {"title": title, "evidence": []})
            ws_meta[ws_id]["evidence"].append(
                {"signal": "branch_name", "value": branch, "confidence": "high"}
            )
        by_id[evt["id"]]["workstream_id"] = branch_to_ws[branch]

    # --- Pass 3: file overlap within 7-day windows ---
    file_event_map: dict[str, list[tuple[datetime, str]]] = defaultdict(list)
    for evt in by_id.values():
        ts = _parse_ts(evt.get("timestamp") or "")
        if ts is None:
            continue
        for f in _get_files(evt):
            file_event_map[f].append((ts, evt["id"]))

    for filename, entries in file_event_map.items():
        entries.sort(key=lambda x: x[0])
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                ts_i, id_i = entries[i]
                ts_j, id_j = entries[j]
                if (ts_j - ts_i) > timedelta(days=7):
                    break
                # Both events touch this file within 7 days
                ws_i = by_id[id_i].get("workstream_id")
                ws_j = by_id[id_j].get("workstream_id")
                if ws_i and not ws_j:
                    by_id[id_j]["workstream_id"] = ws_i
                    ws_meta[ws_i]["evidence"].append(
                        {"signal": "file_overlap", "value": filename, "confidence": "medium"}
                    )
                elif ws_j and not ws_i:
                    by_id[id_i]["workstream_id"] = ws_j
                    ws_meta[ws_j]["evidence"].append(
                        {"signal": "file_overlap", "value": filename, "confidence": "medium"}
                    )
                elif not ws_i and not ws_j:
                    ws_id = _workstream_id(f"file:{filename}")
                    by_id[id_i]["workstream_id"] = ws_id
                    by_id[id_j]["workstream_id"] = ws_id
                    ws_meta.setdefault(ws_id, {"title": _slug_from_text(filename), "evidence": []})
                    ws_meta[ws_id]["evidence"].append(
                        {"signal": "file_overlap", "value": filename, "confidence": "medium"}
                    )

    # --- Pass 4: temporal proximity (< 2 hours) for still-unassigned events ---
    sorted_events = sorted(
        [e for e in by_id.values() if e.get("timestamp")],
        key=lambda e: e["timestamp"],
    )
    for i in range(len(sorted_events) - 1):
        evt_a = sorted_events[i]
        evt_b = sorted_events[i + 1]
        if evt_a.get("workstream_id") or evt_b.get("workstream_id"):
            continue
        ts_a = _parse_ts(evt_a["timestamp"])
        ts_b = _parse_ts(evt_b["timestamp"])
        if ts_a and ts_b and (ts_b - ts_a) < timedelta(hours=2):
            ws_id = _workstream_id(f"temporal:{evt_a['id']}")
            by_id[evt_a["id"]]["workstream_id"] = ws_id
            by_id[evt_b["id"]]["workstream_id"] = ws_id
            ws_meta.setdefault(ws_id, {"title": "recent activity", "evidence": []})
            ws_meta[ws_id]["evidence"].append(
                {"signal": "temporal_proximity", "value": f"{evt_a['id']} + {evt_b['id']}", "confidence": "low"}
            )

    # --- Pass 5: fallback — assign uncorrelated events to a default workstream ---
    default_ws_id = _workstream_id("uncorrelated")
    ws_meta.setdefault(default_ws_id, {"title": "uncorrelated", "evidence": []})
    for evt in by_id.values():
        if not evt.get("workstream_id"):
            evt["workstream_id"] = default_ws_id

    return list(by_id.values()), ws_meta


def build_workstream_records(
    ws_meta: dict[str, dict],
    project_id: str,
    events: list[dict],
) -> list[dict]:
    """Produce workstream rows ready for ledger upsert."""
    from src.ledger import utcnow

    # Compute status per workstream from event statuses
    ws_statuses: dict[str, set[str]] = defaultdict(set)
    ws_latest: dict[str, str] = {}
    for evt in events:
        ws = evt.get("workstream_id")
        if ws:
            ws_statuses[ws].add(evt.get("status") or "unknown")
            ts = evt.get("timestamp") or ""
            if ts > ws_latest.get(ws, ""):
                ws_latest[ws] = ts

    records = []
    for ws_id, meta in ws_meta.items():
        statuses = ws_statuses.get(ws_id, set())
        if "open" in statuses or "failed" in statuses:
            status = "active"
        elif "stale" in statuses:
            status = "stale"
        else:
            status = "active"

        records.append(
            {
                "id": ws_id,
                "title": meta.get("title", ws_id),
                "status": status,
                "evidence": meta.get("evidence", []),
            }
        )
    return records
