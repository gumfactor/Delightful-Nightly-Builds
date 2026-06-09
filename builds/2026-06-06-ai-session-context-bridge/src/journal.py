"""High-level journal operations over a Storage instance."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from .models import Session
from .storage import Storage


class Journal:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def add_session(
        self,
        project: str,
        summary: str,
        context: str = "",
        next_steps: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Session:
        """Create and persist a new session entry."""
        session = Session.create(
            project=project,
            summary=summary,
            context=context,
            next_steps=next_steps,
            files=files,
            tags=tags,
        )
        self.storage.append(session)
        return session

    def list_sessions(
        self,
        project: Optional[str] = None,
        limit: int = 10,
        today_only: bool = False,
    ) -> List[Session]:
        """Return sessions in reverse chronological order, with optional filters."""
        sessions = self.storage.load_all()

        if project:
            sessions = [s for s in sessions if s.project.lower() == project.lower()]

        if today_only:
            today_prefix = date.today().isoformat()
            sessions = [s for s in sessions if s.timestamp.startswith(today_prefix)]

        sessions.sort(key=lambda s: s.timestamp, reverse=True)
        return sessions[:limit]

    def get_session(self, session_id: str) -> Optional[Session]:
        """Return the session with the given ID, or None if not found."""
        for session in self.storage.load_all():
            if session.id == session_id:
                return session
        return None

    def get_projects(self) -> List[str]:
        """Return a sorted list of all unique project names."""
        seen: set = set()
        projects: List[str] = []
        for s in self.storage.load_all():
            if s.project not in seen:
                seen.add(s.project)
                projects.append(s.project)
        return sorted(projects)
