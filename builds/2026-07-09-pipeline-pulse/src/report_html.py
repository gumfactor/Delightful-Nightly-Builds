"""Renders the self-contained dark-mode HTML dashboard."""
from __future__ import annotations

import json
from html import escape
from typing import Optional

from pipeline_stats import NON_ACTIONABLE_STATUSES, BuildStatus, Summary

CHART_JS_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"

CATEGORY_NAMES = {
    "A": "Dashboard / Visualizer",
    "B": "Productivity Utility",
    "C": "Personal Knowledge Tool",
    "D": "Creative / Generative",
    "E": "Learning Aid",
    "F": "Data Explorer",
    "G": "Game / Puzzle",
    "H": "Developer Tool",
    "I": "Life Admin Helper",
}


def _compare_url(owner: Optional[str], repo: Optional[str], default_branch: str, branch: str) -> Optional[str]:
    if not owner or not repo:
        return None
    branch_ref = branch.removeprefix("origin/")
    return f"https://github.com/{owner}/{repo}/compare/{default_branch}...{branch_ref}"


def _fmt_pct(value: float) -> str:
    return f"{value:.0f}%"


def _fmt_rating(value: Optional[int]) -> str:
    return str(value) if value is not None else "—"


def render(
    statuses: list[BuildStatus],
    summary: Summary,
    brief: str,
    owner: Optional[str],
    repo: Optional[str],
    default_branch: str,
) -> str:
    rows_html = []
    for s in sorted(statuses, key=lambda x: x["date"], reverse=True):
        if s["merged"]:
            merged_badge = '<span class="badge badge-merged">merged</span>'
        elif s["status"].lower() in NON_ACTIONABLE_STATUSES:
            merged_badge = '<span class="badge badge-closed">closed</span>'
        else:
            merged_badge = f'<span class="badge badge-backlog">backlog · {s["backlog_days"]}d</span>'
        link = _compare_url(owner, repo, default_branch, s["branch"]) if s["branch"] else None
        link_html = f' · <a href="{escape(link)}" target="_blank" rel="noopener">view</a>' if link else ""
        rows_html.append(
            "<tr>"
            f'<td data-col="date">{escape(s["date"])}</td>'
            f'<td data-col="category">{escape(s["category"])}</td>'
            f'<td data-col="complexity">{escape(s["complexity"])}</td>'
            f'<td data-col="title">{escape(s["title"])}{link_html}</td>'
            f'<td data-col="status">{escape(s["status"])}</td>'
            f'<td data-col="merged">{merged_badge}</td>'
            f'<td data-col="rating">{_fmt_rating(s["rating"])}</td>'
            "</tr>"
        )

    attention_items = []
    for s in summary["needs_attention"]:
        link = _compare_url(owner, repo, default_branch, s["branch"]) if s["branch"] else None
        link_html = f' — <a href="{escape(link)}" target="_blank" rel="noopener">review</a>' if link else ""
        attention_items.append(
            "<li><strong>"
            f'{escape(s["title"])}</strong> ({escape(s["date"])}, {s["backlog_days"]} days'
            f' waiting){link_html}</li>'
        )
    attention_html = (
        "<ul class=\"attention-list\">" + "".join(attention_items) + "</ul>"
        if attention_items
        else '<p class="empty-state">Nothing in the backlog — everything is merged.</p>'
    )

    category_labels = sorted(summary["category_distribution"])
    category_data = [summary["category_distribution"][c] for c in category_labels]
    category_full_labels = [f"{c} · {CATEGORY_NAMES.get(c, c)}" for c in category_labels]

    complexity_order = ["focused", "solid", "ambitious"]
    complexity_labels = [c for c in complexity_order if c in summary["complexity_distribution"]]
    complexity_labels += [c for c in summary["complexity_distribution"] if c not in complexity_labels]
    complexity_data = [summary["complexity_distribution"][c] for c in complexity_labels]

    rating_trend_labels = [pair[0] for pair in summary["rating_trend"]]
    rating_trend_data = [pair[1] for pair in summary["rating_trend"]]

    chart_data = {
        "mergedVsBacklog": {
            "labels": ["Merged", "Backlog"],
            "data": [summary["merged_count"], summary["backlog_count"]],
        },
        "category": {"labels": category_full_labels, "data": category_data},
        "complexity": {"labels": complexity_labels, "data": complexity_data},
        "ratingTrend": {"labels": rating_trend_labels, "data": rating_trend_data},
    }

    oldest = summary["oldest_unmerged"]
    oldest_stat = f'{oldest["backlog_days"]}d' if oldest else "—"
    avg_rating_stat = f'{summary["average_rating"]:.1f}' if summary["average_rating"] is not None else "—"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pipeline Pulse</title>
<script src="{CHART_JS_URL}"></script>
<style>
  :root {{
    --bg: #0b0e14; --panel: #131722; --panel-2: #1a1f2e; --border: #262c3d;
    --text: #e6e9f0; --text-dim: #9aa3b8; --accent: #6ea8fe; --accent-2: #ffd166;
    --good: #4ade80; --warn: #f87171;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 24px; line-height: 1.5;
  }}
  h1 {{ margin: 0 0 4px; font-size: 1.6rem; }}
  .subtitle {{ color: var(--text-dim); margin: 0 0 24px; font-size: 0.95rem; }}
  .hero {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 24px; }}
  .stat-tile {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }}
  .stat-tile .value {{ font-size: 1.8rem; font-weight: 700; }}
  .stat-tile .label {{ color: var(--text-dim); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }}
  .stat-tile.warn .value {{ color: var(--warn); }}
  .stat-tile.good .value {{ color: var(--good); }}
  .brief {{ background: var(--panel-2); border: 1px solid var(--border); border-left: 3px solid var(--accent);
    border-radius: 8px; padding: 14px 18px; margin-bottom: 24px; }}
  .charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .chart-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }}
  .chart-card h3 {{ margin: 0 0 12px; font-size: 0.95rem; color: var(--text-dim); font-weight: 600; }}
  .panels {{ display: grid; grid-template-columns: 1fr; gap: 16px; margin-bottom: 24px; }}
  .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }}
  .attention-list {{ margin: 0; padding-left: 1.2em; }}
  .attention-list li {{ margin-bottom: 6px; }}
  .empty-state {{ color: var(--text-dim); }}
  a {{ color: var(--accent); }}
  input#search {{ background: var(--panel-2); border: 1px solid var(--border); color: var(--text);
    padding: 8px 12px; border-radius: 6px; width: 100%; max-width: 320px; margin-bottom: 12px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--text-dim); cursor: pointer; user-select: none; font-weight: 600; }}
  th:hover {{ color: var(--text); }}
  .badge {{ padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }}
  .badge-merged {{ background: rgba(74,222,128,0.15); color: var(--good); }}
  .badge-backlog {{ background: rgba(248,113,113,0.15); color: var(--warn); }}
  .badge-closed {{ background: rgba(154,163,184,0.15); color: var(--text-dim); }}
  @media (max-width: 600px) {{ body {{ padding: 12px; }} table {{ font-size: 0.8rem; }} }}
</style>
</head>
<body>
  <h1>Pipeline Pulse</h1>
  <p class="subtitle">Nightly build pipeline health — {summary["total"]} builds tracked</p>

  <div class="hero">
    <div class="stat-tile"><div class="value">{summary["total"]}</div><div class="label">Total builds</div></div>
    <div class="stat-tile good"><div class="value">{summary["merged_count"]}</div><div class="label">Merged ({_fmt_pct(summary["merged_pct"])})</div></div>
    <div class="stat-tile warn"><div class="value">{summary["backlog_count"]}</div><div class="label">Backlog ({_fmt_pct(summary["backlog_pct"])})</div></div>
    <div class="stat-tile warn"><div class="value">{oldest_stat}</div><div class="label">Oldest unmerged</div></div>
    <div class="stat-tile"><div class="value">{avg_rating_stat}</div><div class="label">Avg rating</div></div>
    <div class="stat-tile"><div class="value">{_fmt_pct(summary["rating_coverage_pct"])}</div><div class="label">Rating coverage</div></div>
  </div>

  <div class="brief"><strong>What needs attention:</strong> {escape(brief)}</div>

  <div class="charts">
    <div class="chart-card"><h3>Merged vs. Backlog</h3><canvas id="chart-merged"></canvas></div>
    <div class="chart-card"><h3>Rating trend over time</h3><canvas id="chart-rating"></canvas></div>
    <div class="chart-card"><h3>Builds by category</h3><canvas id="chart-category"></canvas></div>
    <div class="chart-card"><h3>Builds by complexity</h3><canvas id="chart-complexity"></canvas></div>
  </div>

  <div class="panels">
    <div class="panel">
      <h3>Needs attention (oldest backlog first)</h3>
      {attention_html}
    </div>
    <div class="panel">
      <h3>All builds</h3>
      <input type="text" id="search" placeholder="Search title, category, status...">
      <table id="build-table">
        <thead><tr>
          <th data-key="date">Date</th><th data-key="category">Cat</th><th data-key="complexity">Complexity</th>
          <th data-key="title">Title</th><th data-key="status">Status</th><th data-key="merged">Merged</th><th data-key="rating">Rating</th>
        </tr></thead>
        <tbody>{"".join(rows_html)}</tbody>
      </table>
    </div>
  </div>

<script>
// Table search/sort are wired up first and independently of Chart.js so a
// blocked or slow CDN never takes down the table's interactivity with it.
document.getElementById('search').addEventListener('input', (e) => {{
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('#build-table tbody tr').forEach((row) => {{
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}});

let sortState = {{ key: null, dir: 1 }};
document.querySelectorAll('#build-table th').forEach((th) => {{
  th.addEventListener('click', () => {{
    const key = th.dataset.key;
    const tbody = document.querySelector('#build-table tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    sortState.dir = sortState.key === key ? -sortState.dir : 1;
    sortState.key = key;
    rows.sort((a, b) => {{
      const av = a.querySelector(`[data-col="${{key}}"]`).textContent.trim();
      const bv = b.querySelector(`[data-col="${{key}}"]`).textContent.trim();
      return av.localeCompare(bv, undefined, {{ numeric: true }}) * sortState.dir;
    }});
    rows.forEach((row) => tbody.appendChild(row));
  }});
}});

// Charts degrade gracefully: if the Chart.js CDN is blocked or slow, each
// card shows a text fallback instead of a blank canvas, and one chart
// failing never prevents the others (or the table above) from working.
function renderChartOrFallback(canvasId, build) {{
  const canvas = document.getElementById(canvasId);
  if (typeof Chart === 'undefined') {{
    canvas.replaceWith(Object.assign(document.createElement('p'), {{
      className: 'empty-state', textContent: 'Chart unavailable (chart.js failed to load).'
    }}));
    return;
  }}
  try {{
    build(canvas);
  }} catch (err) {{
    canvas.replaceWith(Object.assign(document.createElement('p'), {{
      className: 'empty-state', textContent: 'Chart failed to render.'
    }}));
  }}
}}

const CHART_DATA = {json.dumps(chart_data)};
const palette = {{ accent: '#6ea8fe', good: '#4ade80', warn: '#f87171', gold: '#ffd166', grid: '#262c3d', text: '#9aa3b8' }};
const baseOptions = {{
  responsive: true,
  plugins: {{ legend: {{ labels: {{ color: palette.text }} }} }},
  scales: {{
    x: {{ ticks: {{ color: palette.text }}, grid: {{ color: palette.grid }} }},
    y: {{ ticks: {{ color: palette.text }}, grid: {{ color: palette.grid }}, beginAtZero: true }}
  }}
}};

renderChartOrFallback('chart-merged', (canvas) => new Chart(canvas, {{
  type: 'doughnut',
  data: {{ labels: CHART_DATA.mergedVsBacklog.labels, datasets: [{{
    data: CHART_DATA.mergedVsBacklog.data, backgroundColor: [palette.good, palette.warn]
  }}]}},
  options: {{ plugins: {{ legend: {{ labels: {{ color: palette.text }} }} }} }}
}}));

renderChartOrFallback('chart-rating', (canvas) => new Chart(canvas, {{
  type: 'line',
  data: {{ labels: CHART_DATA.ratingTrend.labels, datasets: [{{
    label: 'Rating', data: CHART_DATA.ratingTrend.data, borderColor: palette.accent,
    backgroundColor: 'transparent', tension: 0.25, pointRadius: 3
  }}]}},
  options: {{ ...baseOptions, scales: {{ ...baseOptions.scales, y: {{ ...baseOptions.scales.y, max: 10 }} }} }}
}}));

renderChartOrFallback('chart-category', (canvas) => new Chart(canvas, {{
  type: 'bar',
  data: {{ labels: CHART_DATA.category.labels, datasets: [{{
    label: 'Builds', data: CHART_DATA.category.data, backgroundColor: palette.accent
  }}]}},
  options: {{ ...baseOptions, plugins: {{ legend: {{ display: false }} }}, indexAxis: 'y' }}
}}));

renderChartOrFallback('chart-complexity', (canvas) => new Chart(canvas, {{
  type: 'bar',
  data: {{ labels: CHART_DATA.complexity.labels, datasets: [{{
    label: 'Builds', data: CHART_DATA.complexity.data, backgroundColor: palette.gold
  }}]}},
  options: {{ ...baseOptions, plugins: {{ legend: {{ display: false }} }} }}
}}));
</script>
</body>
</html>
"""
