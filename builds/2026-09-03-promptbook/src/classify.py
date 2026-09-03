"""Deterministic task-type classifier for prompt text.

Rules are checked in a fixed priority order (most specific first) so overlapping keywords
resolve predictably; each branch is exercised by a boundary-case test in
``tests/test_classify.py``.
"""
from __future__ import annotations

import re

TASK_TYPES = (
    "bug-fix",
    "test",
    "docs",
    "config",
    "review",
    "refactor",
    "research",
    "feature",
    "other",
)

_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "bug-fix",
        re.compile(
            r"\b(fix(es|ed|ing)?|bug|broken|crash(es|ed|ing)?|regression|not working|"
            r"doesn'?t work|error(s)?\b|traceback|fails?\b)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "test",
        re.compile(
            r"\b(write|add|fix)\s+(a\s+|some\s+)?tests?\b|\bunit tests?\b|\btest coverage\b|"
            r"\bpytest\b|\bwrite tests?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "docs",
        re.compile(
            r"\b(document(ation)?|docstring|readme|write.{0,15}\bdocs\b|comment(s)? explaining)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "config",
        re.compile(
            r"\b(config(ure|uration)?|settings|environment variable|env var|\.env\b|"
            r"set up|setup\b|install(ation)?|dependency|dependencies)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "review",
        re.compile(
            r"\b(review|audit|check (this|my|the)|critique|feedback on|look over)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "refactor",
        re.compile(
            r"\b(refactor|clean\s?up|simplify|reorganize|restructure|rename|extract (a|the)\s+"
            r"(function|method|module))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "research",
        re.compile(
            r"\b(why (does|is|do)|explain|how does|investigate|what is|what'?s the difference|"
            r"understand|figure out why)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "feature",
        re.compile(
            r"\b(add|implement|build|create|write)\s+(?:(?:a|an|the|new)\s+)*"
            r"(feature|endpoint|page|component|function|script|tool|command)\b",
            re.IGNORECASE,
        ),
    ),
)


def classify(prompt_text: str) -> str:
    """Return one of TASK_TYPES for the given prompt text, defaulting to 'other'."""
    for task_type, pattern in _RULES:
        if pattern.search(prompt_text):
            return task_type
    return "other"
