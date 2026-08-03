"""Render a Landing Pattern report as text, JSON, or a self-contained HTML page."""

from __future__ import annotations

import html
import json
from typing import Any

LABEL_TITLES: dict[str, str] = {
    "conflict": "Merge conflict",
    "ci_failing": "CI failing",
    "changes_requested": "Changes requested",
    "ci_pending": "CI pending",
    "awaiting_review": "Awaiting review",
    "behind_base": "Behind base branch",
    "unknown": "Unknown",
}


def render_text(report: dict[str, Any], ai_notes: dict[int, str] | None = None) -> str:
    """Plain-text terminal report."""
    ai_notes = ai_notes or {}
    lines: list[str] = []
    lines.append(f"Landing Pattern — {report['repo']}")
    lines.append(f"Synced at {report['synced_at']}")
    lines.append("")

    lines.append(f"Batch 1 — merge now, in order ({len(report['batch1'])}):")
    for pr in report["batch1"]:
        lines.append(f"  #{pr['number']}  {pr['title']}  ({pr['age_days']}d old)")
    if not report["batch1"]:
        lines.append("  (none)")
    lines.append("")

    lines.append(f"Batch 2 — merge after rebasing ({len(report['batch2'])}):")
    for pr in report["batch2"]:
        conflicts = ", ".join(f"#{n}" for n in pr["conflicts_with"]) or "an earlier PR"
        lines.append(f"  #{pr['number']}  {pr['title']}  (will conflict with {conflicts})")
    if not report["batch2"]:
        lines.append("  (none)")
    lines.append("")

    lines.append(f"Blocked ({len(report['blocked'])}):")
    for pr in report["blocked"]:
        label = LABEL_TITLES.get(pr["label"], pr["label"])
        lines.append(f"  #{pr['number']}  {pr['title']}  [{label}]  ({pr['age_days']}d old)")
        note = ai_notes.get(pr["number"])
        if note:
            lines.append(f"      -> {note}")
    if not report["blocked"]:
        lines.append("  (none)")
    lines.append("")

    lines.append(f"Drafts ({len(report['drafts'])}):")
    for pr in report["drafts"]:
        lines.append(f"  #{pr['number']}  {pr['title']}  ({pr['age_days']}d old)")
    if not report["drafts"]:
        lines.append("  (none)")

    return "\n".join(lines)


def render_json(report: dict[str, Any]) -> str:
    """JSON report, round-trippable through json.loads."""
    return json.dumps(report, indent=2)


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _pr_row_html(pr: dict[str, Any], extra: str = "") -> str:
    return (
        "<tr>"
        f"<td>#{_escape(pr['number'])}</td>"
        f"<td>{_escape(pr['title'])}</td>"
        f"<td>{_escape(pr['age_days'])}d</td>"
        f"<td>{extra}</td>"
        "</tr>"
    )


def render_html(report: dict[str, Any], ai_notes: dict[int, str] | None = None) -> str:
    """Self-contained dark-mode HTML report. Opens directly via file://."""
    ai_notes = ai_notes or {}

    batch1_rows = "".join(_pr_row_html(pr) for pr in report["batch1"]) or (
        '<tr><td colspan="4">None — nothing is immediately ready.</td></tr>'
    )
    batch2_rows = "".join(
        _pr_row_html(
            pr,
            extra="conflicts with "
            + ", ".join(f"#{n}" for n in pr["conflicts_with"]),
        )
        for pr in report["batch2"]
    ) or '<tr><td colspan="4">None.</td></tr>'
    blocked_rows = "".join(
        _pr_row_html(
            pr,
            extra=_escape(LABEL_TITLES.get(pr["label"], pr["label"]))
            + (
                f"<div class='note'>{_escape(ai_notes[pr['number']])}</div>"
                if ai_notes.get(pr["number"])
                else ""
            ),
        )
        for pr in report["blocked"]
    ) or '<tr><td colspan="4">None.</td></tr>'
    draft_rows = "".join(_pr_row_html(pr) for pr in report["drafts"]) or (
        '<tr><td colspan="4">None.</td></tr>'
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Landing Pattern — {_escape(report['repo'])}</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{
    background: #0d1117; color: #c9d1d9; font-family: -apple-system, system-ui, sans-serif;
    margin: 0; padding: 2rem; line-height: 1.5;
  }}
  h1 {{ color: #e6edf3; font-size: 1.4rem; margin-bottom: 0.2rem; }}
  .subtitle {{ color: #8b949e; margin-bottom: 2rem; font-size: 0.9rem; }}
  h2 {{ color: #e6edf3; font-size: 1.05rem; border-bottom: 1px solid #21262d; padding-bottom: 0.4rem; margin-top: 2rem; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 0.75rem; }}
  th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #21262d; font-size: 0.9rem; }}
  th {{ color: #8b949e; font-weight: 600; }}
  .note {{ color: #8b949e; font-size: 0.85rem; margin-top: 0.25rem; font-style: italic; }}
  .batch1 {{ border-left: 3px solid #3fb950; padding-left: 1rem; }}
  .batch2 {{ border-left: 3px solid #d29922; padding-left: 1rem; }}
  .blocked {{ border-left: 3px solid #f85149; padding-left: 1rem; }}
  .drafts {{ border-left: 3px solid #8b949e; padding-left: 1rem; }}
</style>
</head>
<body>
  <h1>Landing Pattern</h1>
  <div class="subtitle">{_escape(report['repo'])} &middot; synced {_escape(report['synced_at'])}</div>

  <div class="batch1">
    <h2>Batch 1 — merge now, in order ({len(report['batch1'])})</h2>
    <table><tr><th>PR</th><th>Title</th><th>Age</th><th></th></tr>{batch1_rows}</table>
  </div>

  <div class="batch2">
    <h2>Batch 2 — merge after rebasing ({len(report['batch2'])})</h2>
    <table><tr><th>PR</th><th>Title</th><th>Age</th><th>Conflicts</th></tr>{batch2_rows}</table>
  </div>

  <div class="blocked">
    <h2>Blocked ({len(report['blocked'])})</h2>
    <table><tr><th>PR</th><th>Title</th><th>Age</th><th>Reason</th></tr>{blocked_rows}</table>
  </div>

  <div class="drafts">
    <h2>Drafts ({len(report['drafts'])})</h2>
    <table><tr><th>PR</th><th>Title</th><th>Age</th><th></th></tr>{draft_rows}</table>
  </div>
</body>
</html>
"""
