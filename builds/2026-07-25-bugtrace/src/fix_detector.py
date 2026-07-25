"""Heuristics for deciding whether a commit message describes a bug fix."""

import re

_FIX_KEYWORDS = re.compile(
    r"\b(fix(?:e[sd]|ing)?|bug ?fix(?:e[sd])?|\bbug\b|patch(?:ed|es)?|resolve[sd]?|"
    r"correct(?:ed|ion|s)?|crash(?:ed|es)?|broken|typo)\b",
    re.IGNORECASE,
)


def is_fix_commit(message: str) -> bool:
    """Return True if a commit message looks like a bug-fix commit.

    Merge and revert commits are always excluded, even if their subject line
    happens to contain a fix-shaped keyword (e.g. 'Revert "fix crash"').
    """
    if not message or not message.strip():
        return False
    first_line = message.strip().splitlines()[0].strip()
    lower = first_line.lower()
    if lower.startswith("merge "):
        return False
    if lower.startswith("revert"):
        return False
    return bool(_FIX_KEYWORDS.search(lower))
