"""Self-contained dark-mode HTML report renderer. No external network
resources — every rule is inlined so the report opens correctly from a
file:// URL or a phone browser with no connectivity."""
from __future__ import annotations

import html as html_lib
from typing import List

SEVERITY_COLORS = {"breaking": "#ff5f56", "risky": "#ffbd2e", "safe": "#27c93f"}


def render_html(report: dict) -> str:
    title = "Schema Sentinel Report"
    if report["mode"] == "diff":
        entries_all = report["entries"]
    else:
        entries_all = [entry for rev in report["timeline"] for entry in rev["entries"]]

    counts = {"breaking": 0, "risky": 0, "safe": 0}
    for entry in entries_all:
        counts[entry["severity"]] += 1

    body_parts: List[str] = []
    if report["mode"] == "diff":
        body_parts.append(
            f'<h2>{html_lib.escape(report["old_label"])} &rarr; '
            f'{html_lib.escape(report["new_label"])}</h2>'
        )
        body_parts.append(_render_table(report["entries"]))
    else:
        body_parts.append(f'<h2>History: {html_lib.escape(report["path"])}</h2>')
        if not report["timeline"]:
            note = report.get("note", "No revisions to compare.")
            body_parts.append(f'<p class="note">{html_lib.escape(note)}</p>')
        for rev in report["timeline"]:
            body_parts.append(
                f'<h3>{html_lib.escape(rev["sha"])} &mdash; {html_lib.escape(rev["date"])}</h3>'
            )
            body_parts.append(_render_table(rev["entries"]))

    if report.get("ai_summary"):
        body_parts.append(
            '<div class="summary"><h3>Migration Summary</h3><p>'
            f'{html_lib.escape(report["ai_summary"])}</p></div>'
        )

    summary_line = (
        '<div class="counts">'
        f'<span class="breaking">{counts["breaking"]} breaking</span> &middot; '
        f'<span class="risky">{counts["risky"]} risky</span> &middot; '
        f'<span class="safe">{counts["safe"]} safe</span>'
        "</div>"
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_lib.escape(title)}</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ background:#0d1117; color:#c9d1d9; font-family: -apple-system, "Segoe UI", sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
  h1 {{ font-size: 1.4rem; }}
  h2, h3 {{ color:#e6edf3; }}
  table {{ width:100%; border-collapse: collapse; margin-bottom: 1.5rem; }}
  th, td {{ text-align:left; padding: 0.4rem 0.6rem; border-bottom: 1px solid #30363d; font-size: 0.9rem; word-break: break-word; }}
  th {{ color:#8b949e; font-weight:600; }}
  .breaking {{ color:{SEVERITY_COLORS['breaking']}; font-weight:600; }}
  .risky {{ color:{SEVERITY_COLORS['risky']}; font-weight:600; }}
  .safe {{ color:{SEVERITY_COLORS['safe']}; font-weight:600; }}
  .counts {{ margin: 1rem 0; font-size: 1rem; }}
  .summary {{ background:#161b22; border:1px solid #30363d; border-radius:6px; padding:1rem; margin-top:1.5rem; }}
  .note {{ color:#8b949e; font-style: italic; }}
  @media (max-width: 600px) {{
    body {{ margin: 1rem auto; }}
    th, td {{ font-size: 0.8rem; padding: 0.3rem; }}
  }}
</style>
</head>
<body>
<h1>{html_lib.escape(title)}</h1>
{summary_line}
{''.join(body_parts)}
</body>
</html>
"""


def _render_table(entries: List[dict]) -> str:
    if not entries:
        return '<p class="note">No structural changes detected.</p>'
    rows = []
    for entry in entries:
        old_display = "" if entry.get("old") is None else html_lib.escape(str(entry["old"]))
        new_display = "" if entry.get("new") is None else html_lib.escape(str(entry["new"]))
        rows.append(
            f'<tr><td class="{entry["severity"]}">{html_lib.escape(entry["severity"])}</td>'
            f'<td>{html_lib.escape(entry["field"])}</td>'
            f'<td>{html_lib.escape(entry["change"])}</td>'
            f'<td>{old_display}</td>'
            f'<td>{new_display}</td>'
            f'<td>{html_lib.escape(entry["detail"])}</td></tr>'
        )
    return (
        "<table><thead><tr><th>Severity</th><th>Field</th><th>Change</th>"
        "<th>Old</th><th>New</th><th>Detail</th></tr></thead>"
        f'<tbody>{"".join(rows)}</tbody></table>'
    )
