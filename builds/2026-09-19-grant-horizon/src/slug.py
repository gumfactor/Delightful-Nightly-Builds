"""Topic slugification — turns an arbitrary topic string into a safe [a-z0-9-] id.

Used anywhere a topic name becomes a SQLite lookup key component or an HTML
element id, so it must never be able to smuggle path-traversal or markup
characters through.
"""
from __future__ import annotations

import re

_UNSAFE_RUN = re.compile(r"[^a-z0-9]+")


def slugify(topic: str) -> str:
    """Collapse any run of non [a-z0-9] characters into a single hyphen.

    Guarantees the result matches ^[a-z0-9]+(-[a-z0-9]+)*$ or is the
    literal string "topic" if the input contains no safe characters at all
    (e.g. an empty string, or a string made entirely of punctuation).
    """
    lowered = topic.strip().lower()
    collapsed = _UNSAFE_RUN.sub("-", lowered).strip("-")
    return collapsed if collapsed else "topic"
