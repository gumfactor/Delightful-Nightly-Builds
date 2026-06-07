"""Session data model — the unit of storage for ctxlog."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
import uuid


@dataclass
class Session:
    id: str
    timestamp: str  # ISO 8601 UTC, e.g. "2026-06-06T08:44:00Z"
    project: str
    summary: str
    context: str
    next_steps: List[str]
    files: List[str]
    tags: List[str]

    @classmethod
    def create(
        cls,
        project: str,
        summary: str,
        context: str = "",
        next_steps: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> "Session":
        return cls(
            id=str(uuid.uuid4()).replace("-", "")[:8],
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            project=project,
            summary=summary,
            context=context,
            next_steps=next_steps or [],
            files=files or [],
            tags=tags or [],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "project": self.project,
            "summary": self.summary,
            "context": self.context,
            "next_steps": self.next_steps,
            "files": self.files,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            project=data["project"],
            summary=data["summary"],
            context=data.get("context", ""),
            next_steps=data.get("next_steps", []),
            files=data.get("files", []),
            tags=data.get("tags", []),
        )
