"""Provider-neutral agent checkpoints -> ledger events."""
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from .gitcollect import working_state
from .ledger import Ledger, make_event, utc_now
from .project import Project, WorklogError, git, refs_from_branch, refs_from_text

SCHEMA_VERSION = 1
LIST_FIELDS = ("accomplished", "unresolved", "blockers", "next_steps", "files")


def objective_key(objective: str) -> str:
    words = re.findall(r"[a-z0-9]+", objective.lower())
    return "obj:" + "-".join(words)[:80]


def load_file(path: Path) -> dict:
    """Read a checkpoint from JSON (always) or YAML (when PyYAML is installed)."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise WorklogError(f"cannot read checkpoint file: {exc}") from exc
    if Path(path).suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as exc:
            raise WorklogError("YAML checkpoints need PyYAML (pip install pyyaml); JSON works without it") from exc
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise WorklogError(f"invalid YAML: {exc}") from exc
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise WorklogError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise WorklogError("checkpoint must be a mapping")
    return data


def _as_list(value: Any, name: str) -> list:
    if value is None:
        return []
    if isinstance(value, (str, dict)):
        return [value]
    if isinstance(value, list):
        return value
    raise WorklogError(f"'{name}' must be a list")


def _iso(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def normalise(raw: dict) -> dict:
    """Validate and canonicalise a raw checkpoint mapping."""
    version = raw.get("schema_version", SCHEMA_VERSION)
    if version != SCHEMA_VERSION:
        raise WorklogError(f"unsupported checkpoint schema_version {version!r} (expected {SCHEMA_VERSION})")
    provider = str(raw.get("provider", "")).strip().lower()
    if not re.fullmatch(r"[a-z0-9._\-]{1,40}", provider):
        raise WorklogError("checkpoint needs a 'provider' (e.g. codex, claude-code, human)")
    objective = str(raw.get("objective", "")).strip()
    if not objective:
        raise WorklogError("checkpoint needs a non-empty 'objective'")
    timestamp = _iso(raw.get("timestamp") or utc_now())
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WorklogError(f"bad timestamp {timestamp!r}") from exc
    decisions = []
    for item in _as_list(raw.get("decisions"), "decisions"):
        entry = {"summary": item} if isinstance(item, str) else dict(item)
        if not str(entry.get("summary", "")).strip():
            raise WorklogError("each decision needs a 'summary'")
        entry["rejected"] = [str(x) for x in _as_list(entry.get("rejected"), "rejected")]
        entry["files"] = [str(x) for x in _as_list(entry.get("files"), "files")]
        decisions.append(entry)
    validation = []
    for item in _as_list(raw.get("validation"), "validation"):
        entry = {"command": item} if isinstance(item, str) else dict(item)
        entry["command"], entry["result"] = str(entry.get("command", "")), str(entry.get("result", "unknown"))
        validation.append(entry)
    refs = []
    for item in _as_list(raw.get("source_refs"), "source_refs"):
        if not isinstance(item, dict):
            raise WorklogError("each source_ref must be a mapping like {commit: abc123}")
        refs.append({str(k): str(v) for k, v in item.items()})
    out = {"schema_version": SCHEMA_VERSION, "timestamp": timestamp, "provider": provider,
           "session_id": str(raw["session_id"]) if raw.get("session_id") else None,
           "objective": objective, "decisions": decisions, "validation": validation, "source_refs": refs,
           "head": raw.get("head"), "branch": raw.get("branch"), "status": raw.get("status"),
           "auto": bool(raw.get("auto"))}
    if out["status"] not in (None, "completed", "in_progress", "blocked"):
        raise WorklogError("'status' must be completed, in_progress or blocked")
    for name in LIST_FIELDS:
        out[name] = [str(x) for x in _as_list(raw.get(name), name)]
    return out


def to_events(project: Project, cp: dict, resolved_shas: Optional[dict[str, str]] = None) -> list[dict]:
    """Checkpoint -> one 'checkpoint' event plus one 'decision' event per decision."""
    resolved_shas = resolved_shas or {}
    keys = [objective_key(cp["objective"]), *refs_from_text(cp["objective"])]
    for ref in cp["source_refs"]:
        for kind, value in ref.items():
            if kind == "commit":
                keys.append(f"sha:{resolved_shas.get(value, value)}")
            elif kind in ("issue", "pr"):
                keys.append(f"gh:{value.lstrip('#')}")
    branch = cp.get("branch")
    if branch and branch != project.default_branch and not project.config.branch_excluded(branch):
        keys += [f"branch:{branch}", *refs_from_branch(branch)]
    files = [f for f in cp["files"] if not project.config.path_excluded(f)]
    ref = f"{cp['provider']}:{cp['session_id']}" if cp["session_id"] else \
        f"{cp['provider']}:{cp['timestamp']}:{hashlib.sha1(cp['objective'].encode()).hexdigest()[:8]}"
    derived = "in_progress" if cp["next_steps"] or cp["unresolved"] else "completed"
    status = "blocked" if cp["blockers"] else (cp["status"] or derived)
    agent = cp["provider"] != "human"
    events = [make_event(
        ts=cp["timestamp"], project_id=project.project_id, etype="checkpoint", provider=cp["provider"], ref=ref,
        summary=cp["objective"], actor_kind="agent" if agent else "human", actor_name=cp["provider"], status=status,
        keys=keys, files=files,
        metadata={k: cp[k] for k in ("objective", "accomplished", "unresolved", "blockers", "next_steps",
                                     "validation", "session_id", "head", "branch", "auto")})]
    for decision in cp["decisions"]:
        digest = hashlib.sha1(decision["summary"].encode()).hexdigest()[:10]
        events.append(make_event(
            ts=cp["timestamp"], project_id=project.project_id, etype="decision", provider=cp["provider"],
            ref=f"{ref}:decision:{digest}", summary=decision["summary"],
            actor_kind="agent" if agent else "human", actor_name=cp["provider"], status="completed",
            keys=keys, files=decision["files"] or files,
            metadata={"reason": decision.get("reason"), "rejected": decision["rejected"],
                      "supersedes": decision.get("supersedes"), "checkpoint": ref}))
    return events


def capture(project: Project, ledger: Ledger, raw: dict) -> dict:
    """Validate, enrich with current git state if missing, and persist a checkpoint."""
    cp = normalise(raw)
    if not cp["head"] or not cp["branch"]:
        state = working_state(project)
        cp["head"] = cp["head"] or state["head"]
        cp["branch"] = cp["branch"] or state["branch"]
    resolved = {}
    for ref in cp["source_refs"]:
        if "commit" in ref:
            full = git(project.root, "rev-parse", "--verify", "--quiet", ref["commit"] + "^{commit}",
                       check=False).strip()
            if full:
                resolved[ref["commit"]] = full
    events = to_events(project, cp, resolved)
    ledger.ingest(events, replace=True)
    ledger.prune_children(events[0]["ref"] + ":decision:", keep=[e["id"] for e in events[1:]])
    return {"checkpoint_id": events[0]["id"], "decisions": len(events) - 1, "status": events[0]["status"]}
