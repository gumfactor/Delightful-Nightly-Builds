"""
Render a self-contained HTML dashboard from stats + insights.
Chart.js 4.4.4 is loaded from CDN; all data is embedded as inline JSON.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .analyzer import DAY_NAMES, HOUR_LABELS


def _hour_label(h: int) -> str:
    return HOUR_LABELS[h]


def _day_label(d: int) -> str:
    return DAY_NAMES[d]


_CSS = """
:root {
    --bg: #0d1117;
    --surface: #161b22;
    --border: #30363d;
    --accent: #58a6ff;
    --accent2: #3fb950;
    --accent3: #f78166;
    --accent4: #d2a8ff;
    --text: #e6edf3;
    --muted: #8b949e;
    --card-radius: 10px;
    --gap: 20px;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    padding: 24px 20px 40px;
    max-width: 1100px;
    margin: 0 auto;
}
header {
    border-bottom: 1px solid var(--border);
    padding-bottom: 16px;
    margin-bottom: 24px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
}
header h1 { font-size: 1.4rem; font-weight: 600; }
header h1 span { color: var(--accent); }
.meta { color: var(--muted); font-size: 12px; }
.stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: var(--gap);
    margin-bottom: var(--gap);
}
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--card-radius);
    padding: 16px 20px;
}
.card .label {
    color: var(--muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .05em;
    margin-bottom: 6px;
}
.card .value {
    font-size: 1.9rem;
    font-weight: 700;
    line-height: 1.1;
}
.card .sub { color: var(--muted); font-size: 12px; margin-top: 4px; }
.card.blue .value { color: var(--accent); }
.card.green .value { color: var(--accent2); }
.card.red .value { color: var(--accent3); }
.card.purple .value { color: var(--accent4); }

.charts-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(440px, 1fr));
    gap: var(--gap);
    margin-bottom: var(--gap);
}
.chart-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--card-radius);
    padding: 20px;
}
.chart-card h2 {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-bottom: 16px;
}
.chart-card canvas { width: 100% !important; }
.chart-wide {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--card-radius);
    padding: 20px;
    margin-bottom: var(--gap);
}
.chart-wide h2 {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-bottom: 16px;
}
.insights-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent4);
    border-radius: var(--card-radius);
    padding: 20px 24px;
    margin-bottom: var(--gap);
}
.insights-card h2 {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--accent4);
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-bottom: 12px;
}
.insights-card p {
    color: var(--text);
    line-height: 1.7;
    font-size: 0.9rem;
    white-space: pre-wrap;
}
footer {
    border-top: 1px solid var(--border);
    padding-top: 12px;
    color: var(--muted);
    font-size: 11px;
    text-align: center;
}
@media (max-width: 600px) {
    .charts-row { grid-template-columns: 1fr; }
    .stats-row { grid-template-columns: 1fr 1fr; }
}
"""

_CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"

_CHART_DEFAULTS = """
Chart.defaults.color = '#8b949e';
Chart.defaults.borderColor = '#30363d';
Chart.defaults.plugins.legend.display = false;
"""


def _bar_chart_js(canvas_id: str, labels: list, data: list, color: str) -> str:
    return f"""
new Chart(document.getElementById('{canvas_id}'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(labels)},
        datasets: [{{
            data: {json.dumps(data)},
            backgroundColor: '{color}',
            borderRadius: 3,
            borderSkipped: false,
        }}]
    }},
    options: {{
        responsive: true,
        scales: {{
            x: {{ grid: {{ display: false }} }},
            y: {{ grid: {{ color: '#21262d' }}, beginAtZero: true, ticks: {{ precision: 0 }} }}
        }},
        plugins: {{ tooltip: {{ callbacks: {{
            title: ctx => ctx[0].label,
            label: ctx => ctx.raw + ' commits'
        }} }} }}
    }}
}});"""


def _line_chart_js(canvas_id: str, labels: list, data: list, color: str) -> str:
    return f"""
new Chart(document.getElementById('{canvas_id}'), {{
    type: 'line',
    data: {{
        labels: {json.dumps(labels)},
        datasets: [{{
            data: {json.dumps(data)},
            borderColor: '{color}',
            backgroundColor: '{color}22',
            fill: true,
            tension: 0.3,
            pointRadius: 2,
            pointHoverRadius: 5,
        }}]
    }},
    options: {{
        responsive: true,
        scales: {{
            x: {{
                grid: {{ display: false }},
                ticks: {{ maxTicksLimit: 13, maxRotation: 0 }}
            }},
            y: {{ grid: {{ color: '#21262d' }}, beginAtZero: true, ticks: {{ precision: 0 }} }}
        }},
        plugins: {{ tooltip: {{ callbacks: {{
            title: ctx => ctx[0].label,
            label: ctx => ctx.raw + ' commits'
        }} }} }}
    }}
}});"""


def _horizontal_bar_js(canvas_id: str, labels: list, data: list, color: str) -> str:
    return f"""
new Chart(document.getElementById('{canvas_id}'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(labels)},
        datasets: [{{
            data: {json.dumps(data)},
            backgroundColor: '{color}',
            borderRadius: 3,
        }}]
    }},
    options: {{
        indexAxis: 'y',
        responsive: true,
        scales: {{
            x: {{ grid: {{ color: '#21262d' }}, beginAtZero: true, ticks: {{ precision: 0 }} }},
            y: {{ grid: {{ display: false }} }}
        }},
        plugins: {{ tooltip: {{ callbacks: {{
            title: ctx => ctx[0].label,
            label: ctx => ctx.raw + ' commits'
        }} }} }}
    }}
}});"""


def render_dashboard(stats: dict, insights: str, output_path: str) -> None:
    """Render the self-contained HTML dashboard and write it to output_path."""
    username = stats.get("username", "unknown")
    months = stats.get("months", 12)
    total = stats.get("total_commits", 0)
    active = stats.get("active_days", 0)
    cpd = stats.get("commits_per_active_day", 0.0)
    peak_h = stats.get("most_productive_hour", 0)
    peak_d = stats.get("most_productive_day", 0)
    current_streak = stats.get("current_streak", 0)
    longest_streak = stats.get("longest_streak", 0)
    top_repo = stats.get("top_repo", "—")
    top_repo_short = top_repo.split("/")[-1] if "/" in top_repo else top_repo

    hourly = stats.get("hourly_distribution", {})
    hourly_labels = [_hour_label(h) for h in range(24)]
    hourly_data = [hourly.get(h, 0) for h in range(24)]

    daily = stats.get("day_distribution", {})
    daily_labels = [_day_label(d) for d in range(7)]
    daily_data = [daily.get(d, 0) for d in range(7)]

    weekly = stats.get("weekly_series", [])
    weekly_labels = [w["week"] for w in weekly]
    weekly_data = [w["count"] for w in weekly]

    repos = stats.get("repo_breakdown", [])
    repo_labels = [r["repo"].split("/")[-1] for r in repos]
    repo_data = [r["count"] for r in repos]

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    hourly_chart = _bar_chart_js("chart-hourly", hourly_labels, hourly_data, "#58a6ff")
    dow_chart = _bar_chart_js("chart-dow", daily_labels, daily_data, "#3fb950")
    weekly_chart = _line_chart_js("chart-weekly", weekly_labels, weekly_data, "#f78166")
    repo_chart = _horizontal_bar_js("chart-repos", repo_labels, repo_data, "#d2a8ff")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GitHub Activity Explorer — {username}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>GitHub Activity Explorer &mdash; <span data-testid="username">{username}</span></h1>
  <span class="meta">Last {months} months &bull; {generated_at}</span>
</header>

<div class="stats-row">
  <div class="card blue">
    <div class="label">Total Commits</div>
    <div class="value" data-testid="total-commits">{total:,}</div>
    <div class="sub">{active} active days</div>
  </div>
  <div class="card green">
    <div class="label">Peak Hour</div>
    <div class="value" data-testid="peak-hour">{_hour_label(peak_h)}</div>
    <div class="sub">{cpd} commits / active day</div>
  </div>
  <div class="card red">
    <div class="label">Current Streak</div>
    <div class="value" data-testid="current-streak">{current_streak} days</div>
    <div class="sub">Longest: {longest_streak} days</div>
  </div>
  <div class="card purple">
    <div class="label">Top Repository</div>
    <div class="value" style="font-size:1.3rem" data-testid="top-repo">{top_repo_short}</div>
    <div class="sub">{stats.get('top_repo_count', 0):,} commits</div>
  </div>
</div>

<div class="charts-row">
  <div class="chart-card">
    <h2>Commits by Hour of Day (Eastern Time)</h2>
    <canvas id="chart-hourly" data-testid="chart-hourly"></canvas>
  </div>
  <div class="chart-card">
    <h2>Commits by Day of Week</h2>
    <canvas id="chart-dow" data-testid="chart-dow"></canvas>
  </div>
</div>

<div class="chart-wide">
  <h2>Weekly Commit Volume &mdash; Past {months} Months</h2>
  <canvas id="chart-weekly" data-testid="chart-weekly"></canvas>
</div>

<div class="chart-wide">
  <h2>Repository Focus &mdash; Top {len(repos)} by Commit Count</h2>
  <canvas id="chart-repos" data-testid="chart-repos"></canvas>
</div>

<div class="insights-card">
  <h2>&#x2728; AI Developer Profile</h2>
  <p data-testid="ai-insights">{insights}</p>
</div>

<footer>
  Generated by GitHub Activity Explorer &bull; {generated_at}
</footer>

<script src="{_CHART_JS_CDN}"></script>
<script>
{_CHART_DEFAULTS}
{hourly_chart}
{dow_chart}
{weekly_chart}
{repo_chart}
</script>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
