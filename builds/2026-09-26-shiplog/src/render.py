"""Markdown and self-contained HTML rendering for a changelog result."""
from __future__ import annotations

import json
from dataclasses import dataclass

from classify import Commit, SECTION_ORDER

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


@dataclass
class ChangelogResult:
    range_label: str
    total_commits: int
    sections: dict[str, list[Commit]]
    section_text: dict[str, str]
    cancelled_pairs: list[tuple[Commit, Commit]]
    suggested_bump: str


def render_markdown(result: ChangelogResult) -> str:
    lines = [f"# Changelog — {result.range_label}", ""]
    lines.append(f"**Suggested version bump:** `{result.suggested_bump}`  ")
    lines.append(f"**Commits in range:** {result.total_commits}  ")
    if result.cancelled_pairs:
        lines.append(f"**Cancelled revert/re-revert pairs:** {len(result.cancelled_pairs)}  ")
    lines.append("")

    for section_name in SECTION_ORDER:
        commits = result.sections.get(section_name)
        if not commits:
            continue
        lines.append(f"## {section_name}")
        lines.append("")
        text = result.section_text.get(section_name, "")
        lines.append(text)
        lines.append("")

    if not any(result.sections.get(name) for name in SECTION_ORDER):
        lines.append("_No changes in this range._")

    return "\n".join(lines).rstrip() + "\n"


def _escape_for_script_tag(payload: str) -> str:
    return payload.replace("</", "<\\/")


def render_html(result: ChangelogResult) -> str:
    chart_labels = [name for name in SECTION_ORDER if result.sections.get(name)]
    chart_counts = [len(result.sections[name]) for name in chart_labels]

    sections_html = []
    for section_name in SECTION_ORDER:
        commits = result.sections.get(section_name)
        if not commits:
            continue
        text = result.section_text.get(section_name, "")
        text_html = "".join(f"<p>{_html_escape(line)}</p>" for line in text.split("\n") if line.strip())
        commit_list = "".join(
            f"<li><code>{_html_escape(c.sha[:7])}</code> {_html_escape(c.subject)}</li>" for c in commits
        )
        sections_html.append(
            f'<section class="section"><h2>{_html_escape(section_name)} '
            f'<span class="count">{len(commits)}</span></h2>{text_html}'
            f'<ul class="commit-list">{commit_list}</ul></section>'
        )

    data_payload = {
        "labels": chart_labels,
        "counts": chart_counts,
    }
    data_json = _escape_for_script_tag(json.dumps(data_payload))

    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Shiplog — {_html_escape(result.range_label)}</title>
<style>
  :root {{
    --bg: #0f1115; --panel: #171a21; --text: #e6e9ef; --muted: #9aa3b2;
    --accent: #7dd3fc; --border: #262b36;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    background: var(--bg); color: var(--text); margin: 0; padding: 24px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }}
  .wrap {{ max-width: 860px; margin: 0 auto; }}
  h1 {{ font-size: 1.5rem; }}
  .banner {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
    padding: 16px; margin-bottom: 24px; display: flex; gap: 24px; flex-wrap: wrap;
  }}
  .banner .stat {{ display: flex; flex-direction: column; }}
  .banner .stat .label {{ color: var(--muted); font-size: 0.8rem; }}
  .banner .stat .value {{ font-size: 1.3rem; font-weight: 600; color: var(--accent); }}
  .section {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
    padding: 16px 20px; margin-bottom: 16px;
  }}
  .section h2 {{ font-size: 1.1rem; margin-top: 0; }}
  .count {{ color: var(--muted); font-weight: 400; font-size: 0.9rem; }}
  .commit-list {{ color: var(--muted); font-size: 0.85rem; padding-left: 20px; }}
  .commit-list code {{ color: var(--accent); }}
  canvas {{ max-height: 260px; }}
  @media (max-width: 480px) {{ body {{ padding: 12px; }} }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Shiplog — {_html_escape(result.range_label)}</h1>
  <div class="banner">
    <div class="stat"><span class="label">Suggested bump</span><span class="value">{_html_escape(result.suggested_bump)}</span></div>
    <div class="stat"><span class="label">Commits in range</span><span class="value">{result.total_commits}</span></div>
    <div class="stat"><span class="label">Cancelled pairs</span><span class="value">{len(result.cancelled_pairs)}</span></div>
  </div>
  <canvas id="typeChart"></canvas>
  {''.join(sections_html) if sections_html else '<p>No changes in this range.</p>'}
</div>
<script src="{CHART_JS_CDN}"></script>
<script>
  const shiplogData = {data_json};
  new Chart(document.getElementById('typeChart'), {{
    type: 'bar',
    data: {{
      labels: shiplogData.labels,
      datasets: [{{ label: 'Commits', data: shiplogData.counts, backgroundColor: '#7dd3fc' }}],
    }},
    options: {{
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }},
    }},
  }});
</script>
</body>
</html>
"""


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
