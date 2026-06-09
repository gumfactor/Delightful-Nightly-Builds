"""JSON flat-file persistence for ctxlog sessions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import Session


class Storage:
    def __init__(self, data_path: Path) -> None:
        self.data_path = Path(data_path)

    def _ensure_file(self) -> None:
        """Create the data file and any missing parent directories."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_path.exists():
            self.data_path.write_text(json.dumps({"sessions": []}))

    def load_all(self) -> List[Session]:
        """Return all stored sessions, oldest first."""
        self._ensure_file()
        raw = json.loads(self.data_path.read_text(encoding="utf-8"))
        return [Session.from_dict(s) for s in raw.get("sessions", [])]

    def save_all(self, sessions: List[Session]) -> None:
        """Overwrite storage with the given list of sessions."""
        self._ensure_file()
        data = {"sessions": [s.to_dict() for s in sessions]}
        self.data_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def append(self, session: Session) -> None:
        """Add a single session without touching the others."""
        sessions = self.load_all()
        sessions.append(session)
        self.save_all(sessions)
