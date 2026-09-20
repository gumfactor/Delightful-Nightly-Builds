"""Deterministic parsers for reviewer-comment files and author-response files.

Both formats are plain text. No third-party dependencies are used here on
purpose: parsing is the load-bearing, testable core of this tool and must
never depend on network access or an optional package.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

REVIEWER_HEADER_RE = re.compile(r"^\s*#{0,6}\s*reviewer\s*#?\s*(\d+)\b", re.IGNORECASE)
COMMENT_START_RE = re.compile(r"^\s*(\d+)[.\)]\s+(.*\S.*)$")
RESPONSE_KEY_RE = re.compile(r"^\s*\[\s*[Rr](\d+)\s*[Cc](\d+)\s*\]\s*$")


class ParseError(ValueError):
    """Raised when a comments or responses file cannot be parsed."""


@dataclass(frozen=True)
class Comment:
    reviewer_num: int
    comment_num: int
    text: str

    @property
    def id(self) -> str:
        return f"R{self.reviewer_num}C{self.comment_num}"


def parse_comments(text: str) -> list[Comment]:
    """Parse a reviewer-comments file into an ordered list of Comment objects.

    Supports multiple reviewers (``Reviewer 1``, ``## Reviewer #2``, case
    insensitive), numbered comments in either ``1.`` or ``1)`` style, and
    comment text that continues across multiple lines until the next
    numbered item, the next reviewer header, or end of file.

    When no reviewer header appears before the first numbered comment, all
    comments are attributed to Reviewer 1 (a single-reviewer letter).
    """
    lines = text.splitlines()

    comments: list[Comment] = []
    seen_ids: set[str] = set()

    current_reviewer: int | None = None
    current_comment_num: int | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_comment_num is None:
            return
        reviewer_num = current_reviewer if current_reviewer is not None else 1
        comment_text = "\n".join(current_lines).strip()
        comment = Comment(reviewer_num, current_comment_num, comment_text)
        if comment.id in seen_ids:
            raise ParseError(
                f"Duplicate comment ID {comment.id} found in reviewer comments file."
            )
        seen_ids.add(comment.id)
        comments.append(comment)

    for line in lines:
        header_match = REVIEWER_HEADER_RE.match(line)
        if header_match:
            flush()
            current_reviewer = int(header_match.group(1))
            current_comment_num = None
            current_lines = []
            continue

        comment_match = COMMENT_START_RE.match(line)
        if comment_match:
            flush()
            current_comment_num = int(comment_match.group(1))
            current_lines = [comment_match.group(2).strip()]
            continue

        if current_comment_num is not None:
            current_lines.append(line.rstrip())

    flush()

    if not comments:
        raise ParseError(
            "No numbered reviewer comments found. Expected lines like "
            "'1. Please clarify...' under a 'Reviewer N' heading."
        )

    return sorted(comments, key=lambda c: (c.reviewer_num, c.comment_num))


def parse_responses(text: str) -> dict[str, str]:
    """Parse a response file into a dict of normalized comment ID -> response text.

    Format::

        [R1C1]
        Response text, can span
        multiple lines.

        [R1C2]
        Another response.
    """
    lines = text.splitlines()

    responses: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_key is None:
            return
        body = "\n".join(current_lines).strip()
        if current_key in responses:
            raise ParseError(f"Duplicate response key [{current_key}] in responses file.")
        responses[current_key] = body

    for line in lines:
        key_match = RESPONSE_KEY_RE.match(line)
        if key_match:
            flush()
            reviewer_num, comment_num = key_match.groups()
            current_key = f"R{int(reviewer_num)}C{int(comment_num)}"
            current_lines = []
            continue

        if current_key is not None:
            current_lines.append(line.rstrip())

    flush()

    if not responses:
        raise ParseError(
            "No response blocks found. Expected lines like '[R1C1]' followed "
            "by the response text."
        )

    return responses
