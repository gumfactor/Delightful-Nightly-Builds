"""Renders the final Response-to-Reviewers letter in three formats."""

from __future__ import annotations

from html import escape
from itertools import groupby

from .parser import Comment
from .response_matcher import CompletenessReport

MISSING_PLACEHOLDER = "[NO RESPONSE PROVIDED — add before submission]"


def _resolved_text(comment: Comment, polished: dict[str, str]) -> tuple[str, bool]:
    """Return (text, is_missing) for a comment's response."""
    if comment.id in polished:
        return polished[comment.id], False
    return MISSING_PLACEHOLDER, True


def render_markdown(
    comments: list[Comment], polished: dict[str, str], report: CompletenessReport
) -> str:
    lines = [
        "# Response to Reviewers",
        "",
        f"_{report.addressed}/{report.total} comments addressed "
        f"({report.percentage}%)_",
        "",
    ]

    for reviewer_num, group in groupby(comments, key=lambda c: c.reviewer_num):
        lines.append(f"## Reviewer {reviewer_num}")
        lines.append("")
        for comment in group:
            text, missing = _resolved_text(comment, polished)
            lines.append(f"**Comment {comment.reviewer_num}.{comment.comment_num}:** {comment.text}")
            lines.append("")
            flag = " ⚠ MISSING" if missing else ""
            lines.append(f"> Response{flag}: {text}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_plaintext(
    comments: list[Comment], polished: dict[str, str], report: CompletenessReport
) -> str:
    lines = [
        "RESPONSE TO REVIEWERS",
        f"{report.addressed}/{report.total} comments addressed ({report.percentage}%)",
        "",
    ]

    for reviewer_num, group in groupby(comments, key=lambda c: c.reviewer_num):
        lines.append(f"Reviewer {reviewer_num}")
        lines.append("-" * len(f"Reviewer {reviewer_num}"))
        for comment in group:
            text, missing = _resolved_text(comment, polished)
            lines.append(f"Comment {comment.reviewer_num}.{comment.comment_num}: {comment.text}")
            flag = " (MISSING)" if missing else ""
            lines.append(f"Response{flag}: {text}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Response to Reviewers</title>
<style>
  :root {{
    color-scheme: dark;
    --bg: #14161a;
    --panel: #1d2027;
    --text: #e6e6e6;
    --muted: #9aa0ab;
    --accent: #5fb3ff;
    --ok: #4caf7d;
    --warn: #e0955f;
  }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 860px;
    margin: 0 auto;
    padding: 2rem 1.25rem 4rem;
    line-height: 1.5;
  }}
  h1 {{ margin-bottom: 0.25rem; }}
  h2 {{
    margin-top: 2.5rem;
    border-bottom: 1px solid #333844;
    padding-bottom: 0.4rem;
  }}
  .dashboard {{
    background: var(--panel);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin: 1rem 0 2rem;
  }}
  .bar {{
    height: 10px;
    border-radius: 6px;
    background: #333844;
    overflow: hidden;
    margin-top: 0.5rem;
  }}
  .bar-fill {{
    height: 100%;
    background: var(--ok);
  }}
  .comment-block {{
    background: var(--panel);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
  }}
  .comment-block.missing {{
    border: 1px solid var(--warn);
  }}
  .comment-label {{
    color: var(--accent);
    font-weight: 600;
    margin-bottom: 0.25rem;
  }}
  .response-label {{
    color: var(--muted);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-top: 0.75rem;
  }}
  .flag {{
    color: var(--warn);
    font-weight: 600;
  }}
  blockquote {{
    margin: 0.25rem 0 0;
    white-space: pre-wrap;
  }}
</style>
</head>
<body>
<h1>Response to Reviewers</h1>
<div class="dashboard">
  <div>{addressed}/{total} comments addressed ({percentage}%)</div>
  <div class="bar"><div class="bar-fill" style="width: {percentage}%;"></div></div>
</div>
{sections}
</body>
</html>
"""


def render_html(
    comments: list[Comment], polished: dict[str, str], report: CompletenessReport
) -> str:
    section_parts: list[str] = []

    for reviewer_num, group in groupby(comments, key=lambda c: c.reviewer_num):
        section_parts.append(f"<h2>Reviewer {escape(str(reviewer_num))}</h2>")
        for comment in group:
            text, missing = _resolved_text(comment, polished)
            block_class = "comment-block missing" if missing else "comment-block"
            flag_html = '<span class="flag">MISSING</span>' if missing else ""
            section_parts.append(
                f'<div class="{block_class}">'
                f'<div class="comment-label">Comment {comment.reviewer_num}.{comment.comment_num}</div>'
                f"<blockquote>{escape(comment.text)}</blockquote>"
                f'<div class="response-label">Response {flag_html}</div>'
                f"<blockquote>{escape(text)}</blockquote>"
                f"</div>"
            )

    return _HTML_TEMPLATE.format(
        addressed=report.addressed,
        total=report.total,
        percentage=report.percentage,
        sections="\n".join(section_parts),
    )
