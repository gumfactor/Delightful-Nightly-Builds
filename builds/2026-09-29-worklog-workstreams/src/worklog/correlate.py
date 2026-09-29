"""Deterministic, explainable correlation of events into workstreams.

Strong signals (shared commit SHA, issue/PR number, non-default branch, checkpoint objective, explicit
user link) merge events and are recorded as *confirmed* links with the shared key as evidence.
Weak signals (overlapping files close in time) merge only above WEAK_MERGE and are labelled
*inferred*; between WEAK_SUGGEST and WEAK_MERGE they surface as suggestions and change nothing.
User overrides (merge / split / rename / resolve) always win.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

STRONG_CONFIDENCE = {"sha": 1.0, "evt": 1.0, "gh": 0.95, "branch": 0.9, "obj": 0.9, "override": 1.0}
WEAK_MERGE = 0.75
WEAK_SUGGEST = 0.4
WEAK_WINDOW_HOURS = 72.0
MAX_WEAK_CLUSTERS = 2000
FILE_EVENT_TYPES = {"commit", "checkpoint", "decision"}


@dataclass
class Link:
    kind: str            # 'confirmed' | 'inferred' | 'suggested'
    signal: str
    confidence: float
    rationale: str
    events: list[str]


@dataclass
class Workstream:
    id: str
    title: str
    events: list[dict]
    links: list[Link] = field(default_factory=list)
    suggestions: list[Link] = field(default_factory=list)
    status: str = "in_progress"
    blockers: list[dict] = field(default_factory=list)
    first_ts: str = ""
    last_ts: str = ""

    @property
    def files(self) -> list[str]:
        return sorted({f for e in self.events for f in e["files"]})

    def by_type(self, *types: str) -> list[dict]:
        return [e for e in self.events if e["type"] in types]


class _UnionFind:
    def __init__(self, items: list[str]):
        self.parent = {item: item for item in items}

    def find(self, item: str) -> str:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self.parent[max(root_a, root_b)] = min(root_a, root_b)


def _hours_between(a: str, b: str) -> float:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return abs((datetime.strptime(a, fmt) - datetime.strptime(b, fmt)).total_seconds()) / 3600


def _short(key: str) -> str:
    prefix, _, value = key.partition(":")
    return f"{prefix}:{value[:8]}" if prefix in ("sha", "evt") else key


def _weak_score(files_a: set[str], files_b: set[str], gap_hours: float) -> tuple[float, float]:
    union = files_a | files_b
    jaccard = len(files_a & files_b) / len(union) if union else 0.0
    time_factor = max(0.0, 1 - gap_hours / WEAK_WINDOW_HOURS)
    return 0.6 * jaccard + 0.4 * time_factor, jaccard


def correlate(events: list[dict], overrides: Optional[list[dict]] = None) -> list[Workstream]:
    overrides = overrides or []
    by_id = {e["id"]: e for e in events}
    split_ids = {o["event"] for o in overrides if o["kind"] == "split" and o.get("event") in by_id}
    uf = _UnionFind(list(by_id))
    links: list[Link] = []

    # --- strong signals ---
    groups: dict[str, list[str]] = defaultdict(list)
    for event in events:
        if event["id"] in split_ids:
            continue
        for key in {*event["keys"], f"evt:{event['id']}"}:
            groups[key].append(event["id"])
    for key, members in sorted(groups.items()):
        if len(members) < 2:
            continue
        prefix = key.partition(":")[0]
        for other in members[1:]:
            uf.union(members[0], other)
        links.append(Link("confirmed", prefix, STRONG_CONFIDENCE.get(prefix, 0.9),
                          f"shared {_short(key)}", sorted(members)))
    for override in overrides:
        if override["kind"] == "merge":
            ids = [i for i in override.get("events", []) if i in by_id]
            for other in ids[1:]:
                uf.union(ids[0], other)
            if len(ids) > 1:
                links.append(Link("confirmed", "override", 1.0, "merged by user", sorted(ids)))

    # --- weak signals ---
    clusters: dict[str, list[str]] = defaultdict(list)
    for event_id in by_id:
        clusters[uf.find(event_id)].append(event_id)
    suggestions: list[Link] = []
    candidates = {root: members for root, members in clusters.items()
                  if not (set(members) & split_ids) and any(by_id[m]["type"] in FILE_EVENT_TYPES and by_id[m]["files"]
                                                            for m in members)}
    if len(candidates) <= MAX_WEAK_CLUSTERS:
        info = {}
        for root, members in candidates.items():
            evs = [by_id[m] for m in members]
            info[root] = ({f for e in evs if e["type"] in FILE_EVENT_TYPES for f in e["files"]},
                          sorted(e["ts"] for e in evs))
        scored = []
        roots = sorted(info)
        for i, a in enumerate(roots):
            for b in roots[i + 1:]:
                files_a, times_a = info[a]
                files_b, times_b = info[b]
                gap = max(0.0, max(_hours_between(times_a[0], times_b[-1]) if times_a[0] > times_b[-1] else 0.0,
                                   _hours_between(times_b[0], times_a[-1]) if times_b[0] > times_a[-1] else 0.0))
                score, jaccard = _weak_score(files_a, files_b, gap)
                if jaccard > 0 and score >= WEAK_SUGGEST:
                    scored.append((score, jaccard, gap, a, b))
        for score, jaccard, gap, a, b in sorted(scored, key=lambda t: (-t[0], t[3], t[4])):
            shared = sorted(info[a][0] & info[b][0])
            rationale = (f"{len(shared)} shared file(s) [{', '.join(shared[:3])}], "
                         f"{gap:.0f}h apart (score {score:.2f})")
            members = sorted(clusters[a] + clusters[b])
            if score >= WEAK_MERGE and jaccard >= 0.5:
                uf.union(a, b)
                links.append(Link("inferred", "files+time", round(score, 2), rationale, members))
            else:
                suggestions.append(Link("suggested", "files+time", round(score, 2), rationale, members))

    # --- assemble workstreams ---
    final: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        final[uf.find(event["id"])].append(event)
    workstreams = []
    for members in final.values():
        members.sort(key=lambda e: (e["ts"], e["id"]))
        member_ids = {e["id"] for e in members}
        ws = Workstream(id="ws_" + members[0]["id"][4:12], title="", events=members,
                        first_ts=members[0]["ts"], last_ts=members[-1]["ts"])
        ws.links = [ln for ln in links if set(ln.events) & member_ids]
        ws.suggestions = [s for s in suggestions if set(s.events) & member_ids]
        ws.title = _title(ws, overrides)
        ws.status, ws.blockers = _status(ws, overrides)
        workstreams.append(ws)
    workstreams.sort(key=lambda w: (w.last_ts, w.id), reverse=True)
    for ws in workstreams:  # a suggestion is only useful from the other side too
        ws.suggestions = [s for s in ws.suggestions if not (set(s.events) <= {e["id"] for e in ws.events})]
    return workstreams


def _title(ws: Workstream, overrides: list[dict]) -> str:
    ids = {e["id"] for e in ws.events}
    renamed = [o["title"] for o in overrides if o["kind"] == "rename" and o.get("event") in ids]
    if renamed:
        return renamed[-1]
    checkpoints = ws.by_type("checkpoint")
    if checkpoints:
        return checkpoints[-1]["metadata"].get("objective") or checkpoints[-1]["summary"]
    for etype in ("pr", "issue"):
        found = ws.by_type(etype)
        if found:
            return found[0]["metadata"].get("title") or found[0]["summary"]
    for event in ws.events:
        for key in event["keys"]:
            if key.startswith("branch:"):
                return key[len("branch:"):]
    return ws.events[0]["summary"]


def _status(ws: Workstream, overrides: list[dict]) -> tuple[str, list[dict]]:
    resolved = {o["event"] for o in overrides if o["kind"] == "resolve"}
    done_ts = max((e["ts"] for e in ws.events
                   if e["ref"].endswith(":merged") or (e["type"] == "issue" and e["ref"].endswith(":closed"))),
                  default=None)
    work_events = [e for e in ws.events if e["type"] in ("commit", "checkpoint")]
    reopened = done_ts is not None and any(e["ts"] > done_ts for e in work_events)
    finished = done_ts is not None and not reopened

    blockers: list[dict] = []
    for event in ws.events:
        if event["id"] in resolved or (done_ts and event["ts"] < done_ts):
            continue
        later_commit = any(w["type"] == "commit" and w["ts"] > event["ts"] for w in ws.events)
        if event["type"] == "blocker" and event["status"] == "open":
            blockers.append({"event": event["id"], "reason": event["summary"], "kind": "recorded blocker"})
        elif event["type"] == "ci" and event["status"] == "failed" and not later_commit:
            blockers.append({"event": event["id"], "reason": event["summary"], "kind": "failing CI"})
        elif event["type"] == "review" and event["status"] == "blocked" and not later_commit:
            blockers.append({"event": event["id"], "reason": event["summary"], "kind": "changes requested"})
    checkpoints = ws.by_type("checkpoint")
    if checkpoints and checkpoints[-1]["id"] not in resolved:
        for text in checkpoints[-1]["metadata"].get("blockers", []):
            blockers.append({"event": checkpoints[-1]["id"], "reason": text, "kind": "checkpoint blocker"})
    if finished:
        return "completed", []
    if blockers:
        return "blocked", blockers
    if checkpoints and checkpoints[-1]["status"] == "completed" and not any(
            e["ts"] > checkpoints[-1]["ts"] for e in ws.events if e["type"] == "commit"):
        return "completed", []
    return "in_progress", []


def find_workstream(workstreams: list[Workstream], query: str) -> Optional[Workstream]:
    """Resolve by ws id (prefix), event id, or unique case-insensitive title substring."""
    query = query.strip()
    lowered = query.lower()
    for ws in workstreams:
        if ws.id == query or ws.id.startswith(query) and len(query) >= 6:
            return ws
    for ws in workstreams:
        if any(e["id"].startswith(query) for e in ws.events) and len(query) >= 8:
            return ws
    matches = [ws for ws in workstreams if lowered in ws.title.lower()]
    return matches[0] if len(matches) == 1 else None
