"""Generate a structured markdown handoff document for priming a new AI session."""

from __future__ import annotations

from typing import List, Optional

from .models import Session


def generate_handoff(
    sessions: List[Session],
    project: Optional[str] = None,
    n_sessions: int = 3,
) -> str:
    """Build a markdown document suitable for pasting into a new AI session.

    Shows the latest session's full detail as "Current State", then summarises
    up to n_sessions-1 prior sessions as "Recent History".
    """
    if project:
        sessions = [s for s in sessions if s.project.lower() == project.lower()]

    sessions = sorted(sessions, key=lambda s: s.timestamp, reverse=True)[:n_sessions]

    if not sessions:
        target = f" for project '{project}'" if project else ""
        return f"# AI Session Handoff\n\nNo sessions recorded{target}. Start fresh!\n"

    latest = sessions[0]
    lines: List[str] = [
        f"# AI Session Handoff — {latest.project}",
        f"> Generated from {len(sessions)} most recent session(s)  ",
        "",
        "## Current State",
        "",
        f"**Project:** {latest.project}  ",
        f"**Last session:** {latest.timestamp}  ",
        f"**Summary:** {latest.summary}",
        "",
    ]

    if latest.context:
        lines += [
            "## Context / State at End of Last Session",
            "",
            latest.context,
            "",
        ]

    if latest.next_steps:
        lines += ["## Next Steps", ""]
        for i, step in enumerate(latest.next_steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")

    if latest.files:
        lines += ["## Files Being Worked On", ""]
        for f in latest.files:
            lines.append(f"- `{f}`")
        lines.append("")

    if latest.tags:
        lines += [f"**Tags:** {', '.join(latest.tags)}", ""]

    if len(sessions) > 1:
        lines += ["## Recent Session History", ""]
        for s in sessions[1:]:
            lines.append(f"### {s.timestamp} — {s.project}")
            lines.append("")
            lines.append(s.summary)
            if s.next_steps:
                previewed = ", ".join(s.next_steps[:3])
                suffix = " ..." if len(s.next_steps) > 3 else ""
                lines.append(f"*Next steps: {previewed}{suffix}*")
            lines.append("")

    return "\n".join(lines)
