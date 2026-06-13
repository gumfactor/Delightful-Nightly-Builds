"""
Agent checkpoint ingestion — parses a YAML checkpoint file and produces
ledger-ready event and decision dicts.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

import yaml

from src.ledger import make_decision_id, make_event_id, utcnow

SUPPORTED_SCHEMA_VERSIONS = {1}


class CheckpointError(ValueError):
    pass


def _validate(data: dict[str, Any]) -> None:
    """Raise CheckpointError if required fields are missing or schema version is unsupported."""
    version = data.get("schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise CheckpointError(
            f"Unsupported schema_version: {version!r}. "
            f"Supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )
    if not data.get("objective"):
        raise CheckpointError("Checkpoint must have a non-empty 'objective' field.")
    if not data.get("provider"):
        raise CheckpointError("Checkpoint must have a non-empty 'provider' field.")


def parse_checkpoint(raw: str) -> dict[str, Any]:
    """Parse YAML text and validate structure. Raises CheckpointError on bad input."""
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise CheckpointError(f"Invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise CheckpointError("Checkpoint must be a YAML mapping at the top level.")
    _validate(data)
    return data


def checkpoint_to_events(
    data: dict[str, Any],
    project_id: str,
) -> tuple[list[dict], list[dict]]:
    """
    Convert a parsed checkpoint into (events, decisions).

    One checkpoint event is produced per checkpoint file.
    One decision row is produced per entry in data['decisions'].
    """
    timestamp = str(data.get("timestamp") or utcnow())
    provider = data["provider"]
    session_id = data.get("session_id") or "unknown"
    objective = data["objective"]

    # Deterministic source_ref: provider + session_id + objective hash
    import hashlib
    obj_hash = hashlib.sha256(objective.encode()).hexdigest()[:12]
    source_ref = f"{provider}:{session_id}:{obj_hash}"

    event_id = make_event_id("agent", source_ref, "checkpoint")

    accomplished = data.get("accomplished") or []
    unresolved = data.get("unresolved") or []
    next_steps = data.get("next_steps") or []
    files = data.get("files") or []
    validation = data.get("validation") or []
    source_refs = data.get("source_refs") or []

    # Determine status from validation and unresolved
    has_failure = any(
        str(v.get("result", "")).lower() in ("failed", "fail", "error")
        for v in validation
        if isinstance(v, dict)
    )
    status = "failed" if has_failure else ("open" if unresolved else "completed")

    event: dict[str, Any] = {
        "id": event_id,
        "timestamp": timestamp,
        "project_id": project_id,
        "type": "checkpoint",
        "actor_kind": "agent",
        "actor_name": provider,
        "summary": objective,
        "status": status,
        "provider": "agent",
        "source_ref": source_ref,
        "source_url": None,
        "metadata": {
            "session_id": session_id,
            "accomplished": accomplished,
            "unresolved": unresolved,
            "next_steps": next_steps,
            "files": files,
            "validation": validation,
            "source_refs": source_refs,
        },
    }

    decisions: list[dict] = []
    for dec_raw in data.get("decisions") or []:
        if not isinstance(dec_raw, dict):
            continue
        summary = dec_raw.get("summary", "")
        if not summary:
            continue
        dec_id = make_decision_id(event_id, summary)
        decisions.append(
            {
                "id": dec_id,
                "event_id": event_id,
                "workstream_id": None,  # assigned later by correlation
                "summary": summary,
                "reason": dec_raw.get("reason", ""),
                "alternatives": dec_raw.get("alternatives") or [],
                "timestamp": timestamp,
            }
        )

    return [event], decisions


def load_checkpoint_file(path: Path) -> tuple[list[dict], list[dict]]:
    """Read, parse, and convert a checkpoint YAML file."""
    text = path.read_text(encoding="utf-8")
    return load_checkpoint_text(text)


def load_checkpoint_stdin() -> tuple[list[dict], list[dict]]:
    """Read a checkpoint from stdin."""
    text = sys.stdin.read()
    return load_checkpoint_text(text)


def load_checkpoint_text(text: str, project_id: str = "") -> tuple[list[dict], list[dict]]:
    """Parse checkpoint text and convert; project_id may be injected later."""
    data = parse_checkpoint(text)
    pid = project_id or data.get("project_id") or "unknown"
    return checkpoint_to_events(data, pid)
