"""Per-style author-name and author-list formatting.

Family names are never case-converted (they're proper nouns supplied as-is).
Only the "given name -> initials" transform and the join/et-al rules differ
by style.
"""

from __future__ import annotations

import re

from .models import Author


def get_initials(given: str) -> str:
    """'Jane Marie' -> 'J. M.'; 'Jean-Paul' -> 'J.-P.'; 'J.' -> 'J.'"""
    given = given.strip()
    if not given:
        return ""
    out_parts = []
    for part in given.split():
        clean = part.strip(".")
        if not clean:
            continue
        subparts = [sp for sp in clean.split("-") if sp]
        initials_sub = [sp[0].upper() + "." for sp in subparts]
        out_parts.append("-".join(initials_sub))
    return " ".join(out_parts)


def get_initials_compact(given: str) -> str:
    """'Jane Marie' -> 'JM'; 'Jean-Paul' -> 'JP' (AMA/Vancouver convention)."""
    parts = [p for p in re.split(r"[\s\-]+", given.strip()) if p]
    return "".join(p[0].upper() for p in parts)


def format_author_apa(author: Author) -> str:
    initials = get_initials(author.given)
    return f"{author.family}, {initials}" if initials else author.family


def format_author_ama_vancouver(author: Author) -> str:
    initials = get_initials_compact(author.given)
    return f"{author.family} {initials}" if initials else author.family


def format_authors_apa(authors: list[Author]) -> str:
    if not authors:
        return ""
    formatted = [format_author_apa(a) for a in authors]
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) <= 20:
        return ", ".join(formatted[:-1]) + ", & " + formatted[-1]
    return ", ".join(formatted[:19]) + ", ... " + formatted[-1]


def format_authors_ama(authors: list[Author]) -> str:
    if not authors:
        return ""
    formatted = [format_author_ama_vancouver(a) for a in authors]
    if len(formatted) <= 6:
        return ", ".join(formatted)
    return ", ".join(formatted[:3]) + ", et al."


def format_authors_vancouver(authors: list[Author]) -> str:
    if not authors:
        return ""
    formatted = [format_author_ama_vancouver(a) for a in authors]
    if len(formatted) <= 6:
        return ", ".join(formatted)
    return ", ".join(formatted[:6]) + ", et al."


def _chicago_inverted(author: Author) -> str:
    given = author.given.strip()
    return f"{author.family}, {given}" if given else author.family


def _chicago_normal(author: Author) -> str:
    given = author.given.strip()
    return f"{given} {author.family}" if given else author.family


def format_authors_chicago(authors: list[Author]) -> str:
    if not authors:
        return ""
    n = len(authors)
    if n == 1:
        return _chicago_inverted(authors[0])
    display = authors if n <= 10 else authors[:7]
    parts = [_chicago_inverted(display[0])] + [_chicago_normal(a) for a in display[1:]]
    if n > 10:
        return ", ".join(parts) + ", et al."
    return ", ".join(parts[:-1]) + ", and " + parts[-1]
