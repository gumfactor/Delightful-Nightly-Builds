"""Full-text search across session fields."""

from __future__ import annotations

from typing import List, Optional

from .models import Session


def search_sessions(
    sessions: List[Session],
    query: str,
    project: Optional[str] = None,
) -> List[Session]:
    """Return sessions where query appears in any searchable field.

    Searchable fields: summary, context, project name, tags, files, next_steps.
    Matching is case-insensitive substring search.
    """
    q = query.lower().strip()
    if not q:
        return []

    results: List[Session] = []
    for session in sessions:
        if project and session.project.lower() != project.lower():
            continue

        haystack = " ".join([
            session.summary,
            session.context,
            session.project,
            " ".join(session.tags),
            " ".join(session.files),
            " ".join(session.next_steps),
        ]).lower()

        if q in haystack:
            results.append(session)

    return results
