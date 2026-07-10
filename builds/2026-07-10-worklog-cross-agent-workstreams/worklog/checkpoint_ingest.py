"""Ingests a validated Checkpoint into the ledger: one checkpoint event + one event per decision."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import util
from .checkpoint import Checkpoint
from .correlate import CorrelationInput, resolve_workstream
from .ledger import Event, Ledger
from .project import ProjectState


@dataclass
class CheckpointIngestResult:
    checkpoint_event_id: str
    workstream_id: str
    decision_event_ids: list = field(default_factory=list)
    newly_inserted: bool = True


def ingest_checkpoint(ledger: Ledger, project: ProjectState, checkpoint: Checkpoint) -> CheckpointIngestResult:
    project_id = checkpoint.project_id or project.project_id

    # Deterministic ref: session_id if given, else a hash of objective+timestamp so re-ingesting
    # the exact same checkpoint file is a no-op, but two different checkpoints with the same
    # objective text at different times are treated as distinct.
    ref_basis = checkpoint.session_id or f"{checkpoint.objective}|{checkpoint.timestamp}"
    source_ref = util.path_hash(f"{checkpoint.provider}|{ref_basis}")

    checkpoint_event_id = util.event_id(project_id, "checkpoint", source_ref, "checkpoint")

    commit_ref = None
    for ref in checkpoint.source_refs:
        if isinstance(ref, dict) and ref.get("commit"):
            commit_ref = ref["commit"]
            break

    issue_refs = util.extract_issue_refs(checkpoint.objective)
    for item in checkpoint.accomplished + checkpoint.unresolved + checkpoint.next_steps:
        issue_refs.extend(n for n in util.extract_issue_refs(item) if n not in issue_refs)

    event = Event(
        id=checkpoint_event_id,
        project_id=project_id,
        timestamp=checkpoint.timestamp,
        type="checkpoint",
        actor_kind="agent",
        actor_name=checkpoint.provider,
        summary=checkpoint.objective,
        status="open" if checkpoint.unresolved or checkpoint.next_steps else "completed",
        source_provider="checkpoint",
        source_ref=source_ref,
        metadata={
            "session_id": checkpoint.session_id,
            "accomplished": checkpoint.accomplished,
            "unresolved": checkpoint.unresolved,
            "next_steps": checkpoint.next_steps,
            "validation": checkpoint.validation,
            "files": checkpoint.files,
            "source_refs": checkpoint.source_refs,
            "commit_ref": commit_ref,
        },
    )
    newly_inserted = ledger.upsert_event(event)

    params = CorrelationInput(
        timestamp=checkpoint.timestamp,
        explicit_hint=checkpoint.workstream_hint,
        issue_refs=issue_refs or None,
        files=checkpoint.files or None,
        fallback_title=checkpoint.objective,
    )
    workstream_id, correlation = resolve_workstream(ledger, project_id, params)
    ledger.set_event_workstream(checkpoint_event_id, workstream_id, correlation)

    decision_event_ids = []
    if newly_inserted:
        for index, decision in enumerate(checkpoint.decisions):
            decision_ref = f"{source_ref}:decision:{index}"
            decision_event_id = util.event_id(project_id, "checkpoint", decision_ref, "decision")
            decision_event = Event(
                id=decision_event_id,
                project_id=project_id,
                timestamp=checkpoint.timestamp,
                type="decision",
                actor_kind="agent",
                actor_name=checkpoint.provider,
                summary=decision["summary"],
                status="recorded",
                workstream_id=workstream_id,
                source_provider="checkpoint",
                source_ref=decision_ref,
                metadata={"reason": decision.get("reason", ""), "checkpoint_event_id": checkpoint_event_id},
                correlation=correlation,
            )
            ledger.upsert_event(decision_event)
            decision_event_ids.append(decision_event_id)

    return CheckpointIngestResult(
        checkpoint_event_id=checkpoint_event_id,
        workstream_id=workstream_id,
        decision_event_ids=decision_event_ids,
        newly_inserted=newly_inserted,
    )
