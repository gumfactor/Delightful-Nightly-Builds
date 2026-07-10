"""Provider-neutral agent checkpoint schema validation and normalization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import util

SUPPORTED_SCHEMA_VERSION = 1

REQUIRED_FIELDS = ("schema_version", "provider", "objective")


class CheckpointValidationError(ValueError):
    pass


@dataclass
class Checkpoint:
    schema_version: int
    provider: str
    objective: str
    timestamp: str
    session_id: str = ""
    project_id: str = ""
    workstream_hint: str = ""
    accomplished: list = field(default_factory=list)
    decisions: list = field(default_factory=list)
    unresolved: list = field(default_factory=list)
    next_steps: list = field(default_factory=list)
    validation: list = field(default_factory=list)
    files: list = field(default_factory=list)
    source_refs: list = field(default_factory=list)


def validate_checkpoint(data: dict[str, Any]) -> Checkpoint:
    if not isinstance(data, dict):
        raise CheckpointValidationError("Checkpoint must be a JSON object")

    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        raise CheckpointValidationError(f"Missing required field(s): {', '.join(missing)}")

    if data["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        raise CheckpointValidationError(
            f"Unsupported schema_version {data['schema_version']!r}; "
            f"expected {SUPPORTED_SCHEMA_VERSION}"
        )

    if not isinstance(data["provider"], str) or not data["provider"].strip():
        raise CheckpointValidationError("'provider' must be a non-empty string")

    if not isinstance(data["objective"], str) or not data["objective"].strip():
        raise CheckpointValidationError("'objective' must be a non-empty string")

    for list_field in ("accomplished", "unresolved", "next_steps", "files"):
        value = data.get(list_field, [])
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise CheckpointValidationError(f"'{list_field}' must be a list of strings")

    decisions = data.get("decisions", [])
    if not isinstance(decisions, list):
        raise CheckpointValidationError("'decisions' must be a list")
    for decision in decisions:
        if not isinstance(decision, dict) or not decision.get("summary"):
            raise CheckpointValidationError("each decision must be an object with a 'summary'")

    validation_entries = data.get("validation", [])
    if not isinstance(validation_entries, list):
        raise CheckpointValidationError("'validation' must be a list")
    for entry in validation_entries:
        if not isinstance(entry, dict) or "command" not in entry or "result" not in entry:
            raise CheckpointValidationError(
                "each validation entry must have 'command' and 'result'"
            )

    source_refs = data.get("source_refs", [])
    if not isinstance(source_refs, list):
        raise CheckpointValidationError("'source_refs' must be a list")

    timestamp = data.get("timestamp") or util.utc_now_iso()
    try:
        util.parse_iso(timestamp)
    except ValueError as exc:
        raise CheckpointValidationError(f"invalid 'timestamp': {exc}") from exc

    return Checkpoint(
        schema_version=data["schema_version"],
        provider=data["provider"].strip(),
        objective=util.redact_secrets(data["objective"].strip()),
        timestamp=timestamp,
        session_id=str(data.get("session_id", "")),
        project_id=str(data.get("project_id", "")),
        workstream_hint=str(data.get("workstream_hint", "")),
        accomplished=[util.redact_secrets(s) for s in data.get("accomplished", [])],
        decisions=[
            {
                "summary": util.redact_secrets(d.get("summary", "")),
                "reason": util.redact_secrets(d.get("reason", "")),
            }
            for d in decisions
        ],
        unresolved=[util.redact_secrets(s) for s in data.get("unresolved", [])],
        next_steps=[util.redact_secrets(s) for s in data.get("next_steps", [])],
        validation=list(validation_entries),
        files=list(data.get("files", [])),
        source_refs=list(source_refs),
    )
