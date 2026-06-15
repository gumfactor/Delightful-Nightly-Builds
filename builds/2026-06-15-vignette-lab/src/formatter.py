"""Markdown output formatting for generated vignettes."""

from __future__ import annotations

from datetime import datetime, timezone

from .generator import Vignette


def _header(title: str, theme: str, count: int) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        f"# {title}\n\n"
        f"**Theme:** {theme.capitalize()}  \n"
        f"**Vignettes:** {count}  \n"
        f"**Generated:** {date_str}\n\n"
        f"---\n\n"
    )


def format_participant(vignettes: list[Vignette]) -> str:
    """
    Participant-facing version: numbered vignette text + response prompt only.
    No manipulation checks or researcher notes.
    """
    if not vignettes:
        return "*(No vignettes generated)*\n"

    theme = vignettes[0].theme
    lines = [_header("Vignette Set — Participant Version", theme, len(vignettes))]

    for v in vignettes:
        lines.append(f"## Vignette {v.index}\n\n")
        lines.append(f"{v.narrative}\n\n")
        lines.append(f"**{v.prompt}**\n\n")
        lines.append("---\n\n")

    return "".join(lines)


def format_researcher(vignettes: list[Vignette]) -> str:
    """
    Researcher version: includes narrative, manipulation checks, response prompt,
    and design notes for each vignette.
    """
    if not vignettes:
        return "*(No vignettes generated)*\n"

    theme = vignettes[0].theme
    lines = [_header("Vignette Set — Researcher Version", theme, len(vignettes))]

    # One-time theme note at the top
    note = vignettes[0].researcher_note
    lines.append(f"> **Theme note:** {note}\n\n---\n\n")

    for v in vignettes:
        lines.append(f"## Vignette {v.index}\n\n")
        lines.append(f"**Character:** {v.character['name']} ({v.character['age']}, {v.character['role']})\n\n")
        lines.append(f"### Scenario\n\n{v.narrative}\n\n")
        lines.append(f"### Response Prompt\n\n{v.prompt}\n\n")
        lines.append("### Manipulation Checks\n\n")
        for j, check in enumerate(v.checks, start=1):
            lines.append(f"{j}. {check}\n")
        lines.append("\n---\n\n")

    return "".join(lines)


def format_stdout(vignettes: list[Vignette], researcher: bool = False) -> str:
    """Choose researcher or participant format for terminal/stdout display."""
    if researcher:
        return format_researcher(vignettes)
    return format_participant(vignettes)
