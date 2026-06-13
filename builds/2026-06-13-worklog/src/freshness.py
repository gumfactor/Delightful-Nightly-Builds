"""
Freshness checks — detect stale worklog state before generating resume output.

Stale means: the HEAD SHA stored in the most recent commit event does not match
the current repository HEAD.  Stale checkpoints are flagged; stale state is
never presented as confirmed-current.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.collectors.git import get_head_sha
from src.ledger import get_latest_event_of_type, query_events


class FreshnessReport:
    """Encapsulates the result of a freshness check."""

    def __init__(
        self,
        is_stale: bool,
        stored_head: Optional[str],
        current_head: Optional[str],
        stale_checkpoints: list[str],
    ) -> None:
        self.is_stale = is_stale
        self.stored_head = stored_head
        self.current_head = current_head
        self.stale_checkpoints = stale_checkpoints

    def warning_lines(self) -> list[str]:
        """Return human-readable warning strings, empty if fresh."""
        lines = []
        if self.is_stale and self.stored_head and self.current_head:
            lines.append(
                f"⚠ STALE: stored HEAD {self.stored_head[:12]} != "
                f"current HEAD {self.current_head[:12]}"
            )
        for ckpt_id in self.stale_checkpoints:
            lines.append(f"⚠ Checkpoint {ckpt_id} may be stale — HEAD has moved on")
        return lines


def check_freshness(
    db_path: Path,
    project_id: str,
    git_root: Path,
) -> FreshnessReport:
    """
    Compare the most-recent commit event's stored SHA against the live HEAD.
    Also flag checkpoint events whose stored head_sha predates the live HEAD.
    """
    current_head = get_head_sha(git_root)

    latest_commit = get_latest_event_of_type(db_path, project_id, "commit")

    stored_head: Optional[str] = None
    if latest_commit:
        import json
        meta = latest_commit.get("metadata")
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        stored_head = (meta or {}).get("sha") or latest_commit.get("source_ref")

    is_stale = bool(
        stored_head
        and current_head
        and not current_head.startswith(stored_head[:12])
        and not stored_head.startswith(current_head[:12])
    )

    # Find checkpoint events that reference a commit SHA older than current HEAD
    stale_checkpoints: list[str] = []
    if is_stale:
        ckpts = query_events(db_path, project_id, event_type="checkpoint", limit=20)
        for ckpt in ckpts:
            import json
            meta = ckpt.get("metadata")
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    continue
            source_refs = (meta or {}).get("source_refs") or []
            for ref in source_refs:
                if isinstance(ref, dict):
                    commit_sha = ref.get("commit")
                elif isinstance(ref, str):
                    commit_sha = ref
                else:
                    continue
                if commit_sha and current_head and not current_head.startswith(
                    str(commit_sha)[:12]
                ):
                    stale_checkpoints.append(ckpt["id"])
                    break

    return FreshnessReport(
        is_stale=is_stale,
        stored_head=stored_head,
        current_head=current_head,
        stale_checkpoints=stale_checkpoints,
    )
