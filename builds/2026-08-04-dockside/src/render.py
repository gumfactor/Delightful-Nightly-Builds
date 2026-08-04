"""Self-contained dark-mode HTML dashboard for Dockside.

No network calls happen at render time - this module works entirely off
data already synced into the database. Every piece of user-supplied text
(site names, task names) is passed through html.escape before it touches
the output string.
"""
from __future__ import annotations

import html
import json
from datetime import date
from typing import Optional

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"

STATUS_LABELS = {
    "ready_now": ("Ready Now", "#2ecc71"),
    "ready_soon": ("Ready Soon", "#f1c40f"),
    "not_ready": ("Not Ready", "#e74c3c"),
    "overdue": ("Overdue", "#c0392b"),
    "off_season": ("Off Season", "#7f8c8d"),
    "done_this_season": ("Done This Season", "#3498db"),
}

CONSTRAINT_LABELS = {
    "wind": "Max wind",
    "frost_free": "Frost-free",
    "water_temp": "Water temp",
    "dry_streak": "Dry-day streak",
}

CONSTRAINT_SYMBOLS = {"pass": "✓", "fail": "✗", "unknown": "?"}


def _safe_json_for_script(obj) -> str:
    """Embeds a Python object as JSON inside a <script> block without risk
    of the literal string "</script>" breaking out of the tag."""
    return json.dumps(obj).replace("</", "<\\/")


def _task_card_html(task_row, status: str, best_day: Optional[date], constraints_for_best) -> str:
    label, color = STATUS_LABELS.get(status, (status, "#999999"))
    name = html.escape(str(task_row["name"]))
    category = html.escape(str(task_row["category"]))
    best_day_str = best_day.isoformat() if best_day else "—"

    rows = ""
    if constraints_for_best:
        for key, result in constraints_for_best.items():
            if result == "n/a":
                continue
            label_text = html.escape(CONSTRAINT_LABELS.get(key, key))
            symbol = CONSTRAINT_SYMBOLS.get(result, "?")
            rows += (
                f'<div class="constraint-row constraint-{html.escape(result)}">'
                f"<span>{label_text}</span><span>{symbol}</span></div>"
            )

    return f"""
    <div class="task-card">
      <div class="task-card-header">
        <span class="task-name">{name}</span>
        <span class="status-badge" style="background:{color}">{html.escape(label)}</span>
      </div>
      <div class="task-category">{category}</div>
      <div class="best-day">Best day this week: <strong>{html.escape(best_day_str)}</strong></div>
      <div class="constraints">{rows}</div>
    </div>
    """


def render_dashboard(site_row, task_cards_data: list, observations: list,
                      boating_scores: list, briefing_text: Optional[str],
                      briefing_source: Optional[str], generated_at: str) -> str:
    site_name = html.escape(str(site_row["name"]))
    place_name = html.escape(str(site_row["place_name"] or ""))
    marine_available = bool(site_row["marine_available"])

    cards_html = "".join(
        _task_card_html(c["task_row"], c["status"], c["best_day"], c["constraints_for_best"])
        for c in task_cards_data
    )
    if not cards_html:
        cards_html = '<p class="muted">No active tasks configured. Add one with <code>add-task</code>.</p>'

    dates = [o["obs_date"] for o in observations]
    temps_max = [o["temp_max_c"] for o in observations]
    temps_min = [o["temp_min_c"] for o in observations]
    precip = [o["precip_mm"] for o in observations]
    wind = [o["wind_speed_max_kmh"] for o in observations]
    comfort_dates = [b["obs_date"] for b in boating_scores]
    comfort_values = [b["score"] for b in boating_scores]

    if briefing_text:
        source_label = "AI-generated" if briefing_source == "ai" else "Template"
        briefing_html = f"""
        <section class="briefing">
          <h2>Season Briefing <span class="source-tag">{html.escape(source_label)}</span></h2>
          <p>{html.escape(briefing_text)}</p>
        </section>
        """
    else:
        briefing_html = """
        <section class="briefing">
          <h2>Season Briefing</h2>
          <p class="muted">Run <code>dockside brief</code> to generate a season readiness briefing.</p>
        </section>
        """

    marine_note = "" if marine_available else (
        '<p class="muted">Marine data unavailable for this site — '
        "water-temp/wave constraints show as “data unavailable.”</p>"
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dockside — {site_name}</title>
<script src="{CHART_JS_CDN}" onerror="window.__chartLoadFailed = true"></script>
<style>
{_CSS}
</style>
</head>
<body>
<header>
  <h1>Dockside</h1>
  <div class="site-sub">{site_name}{f' &middot; {place_name}' if place_name else ''}</div>
  <div class="generated">Generated {html.escape(generated_at)}</div>
</header>
<main>
  {marine_note}
  <section class="charts">
    <div class="chart-box">
      <h2>This Week's Boating Outlook</h2>
      <canvas id="comfortChart" height="200"></canvas>
      <div id="comfortFallback" class="fallback-table" hidden></div>
    </div>
    <div class="chart-box">
      <h2>Weather Trend</h2>
      <canvas id="weatherChart" height="200"></canvas>
      <div id="weatherFallback" class="fallback-table" hidden></div>
    </div>
  </section>
  {briefing_html}
  <section class="tasks">
    <h2>Season Task Readiness</h2>
    <div class="task-grid">
      {cards_html}
    </div>
  </section>
</main>
<script>
const comfortDates = {_safe_json_for_script(comfort_dates)};
const comfortValues = {_safe_json_for_script(comfort_values)};
const weatherDates = {_safe_json_for_script(dates)};
const tempsMax = {_safe_json_for_script(temps_max)};
const tempsMin = {_safe_json_for_script(temps_min)};
const precipValues = {_safe_json_for_script(precip)};
const windValues = {_safe_json_for_script(wind)};

function renderFallbackTable(containerId, headers, rows) {{
  const el = document.getElementById(containerId);
  if (!el) return;
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const headRow = document.createElement('tr');
  headers.forEach(function(h) {{
    const th = document.createElement('th');
    th.textContent = h;
    headRow.appendChild(th);
  }});
  thead.appendChild(headRow);
  table.appendChild(thead);
  const tbody = document.createElement('tbody');
  rows.forEach(function(row) {{
    const tr = document.createElement('tr');
    row.forEach(function(cell) {{
      const td = document.createElement('td');
      td.textContent = (cell === null || cell === undefined) ? '–' : cell;
      tr.appendChild(td);
    }});
    tbody.appendChild(tr);
  }});
  table.appendChild(tbody);
  el.replaceChildren(table);
  el.hidden = false;
}}

function initCharts() {{
  const comfortCanvas = document.getElementById('comfortChart');
  const weatherCanvas = document.getElementById('weatherChart');
  if (window.__chartLoadFailed || typeof Chart === 'undefined') {{
    comfortCanvas.hidden = true;
    weatherCanvas.hidden = true;
    renderFallbackTable('comfortFallback', ['Date', 'Comfort Score'],
      comfortDates.map(function(d, i) {{ return [d, comfortValues[i]]; }}));
    renderFallbackTable('weatherFallback', ['Date', 'Max °C', 'Min °C', 'Precip mm', 'Wind km/h'],
      weatherDates.map(function(d, i) {{ return [d, tempsMax[i], tempsMin[i], precipValues[i], windValues[i]]; }}));
    return;
  }}
  new Chart(comfortCanvas, {{
    type: 'bar',
    data: {{ labels: comfortDates, datasets: [{{ label: 'Comfort Score', data: comfortValues, backgroundColor: '#3498db' }}] }},
    options: {{ scales: {{ y: {{ min: 0, max: 100 }} }} }}
  }});
  new Chart(weatherCanvas, {{
    type: 'line',
    data: {{
      labels: weatherDates,
      datasets: [
        {{ label: 'Max °C', data: tempsMax, borderColor: '#e67e22', fill: false }},
        {{ label: 'Min °C', data: tempsMin, borderColor: '#3498db', fill: false }},
        {{ label: 'Wind km/h', data: windValues, borderColor: '#9b59b6', fill: false }}
      ]
    }},
    options: {{ interaction: {{ mode: 'index' }} }}
  }});
}}

window.addEventListener('DOMContentLoaded', function() {{
  setTimeout(initCharts, 50);
}});
</script>
</body>
</html>
"""


_CSS = """
:root {
  --bg: #0f1115;
  --card-bg: #1a1d24;
  --text: #e8eaed;
  --muted: #9aa0a6;
  --border: #2a2e37;
}
* { box-sizing: border-box; }
body {
  background: var(--bg); color: var(--text); font-family: -apple-system, system-ui, sans-serif;
  margin: 0; padding: 0 1rem 3rem;
}
header { padding: 2rem 0 1rem; }
h1 { margin: 0; font-size: 1.8rem; }
.site-sub { color: var(--muted); margin-top: 0.25rem; }
.generated { color: var(--muted); font-size: 0.8rem; margin-top: 0.25rem; }
main { max-width: 960px; margin: 0 auto; }
.muted { color: var(--muted); }
section { margin-bottom: 2rem; }
.charts { display: grid; grid-template-columns: 1fr; gap: 1.5rem; }
@media (min-width: 720px) { .charts { grid-template-columns: 1fr 1fr; } }
.chart-box { background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; overflow-x: auto; }
.chart-box canvas { max-width: 100%; }
.fallback-table table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.fallback-table th, .fallback-table td { border-bottom: 1px solid var(--border); padding: 0.3rem 0.5rem; text-align: left; }
.briefing { background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: 1rem 1.25rem; }
.source-tag { font-size: 0.7rem; color: var(--muted); font-weight: normal; }
.task-grid { display: grid; grid-template-columns: 1fr; gap: 1rem; }
@media (min-width: 720px) { .task-grid { grid-template-columns: 1fr 1fr; } }
.task-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; }
.task-card-header { display: flex; justify-content: space-between; align-items: center; }
.task-name { font-weight: 600; }
.status-badge { color: #0f1115; font-size: 0.75rem; font-weight: 600; padding: 0.15rem 0.5rem; border-radius: 999px; }
.task-category { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; margin-top: 0.25rem; }
.best-day { margin-top: 0.5rem; font-size: 0.9rem; }
.constraints { margin-top: 0.5rem; }
.constraint-row { display: flex; justify-content: space-between; font-size: 0.85rem; padding: 0.15rem 0; border-top: 1px solid var(--border); }
.constraint-pass span:last-child { color: #2ecc71; }
.constraint-fail span:last-child { color: #e74c3c; }
.constraint-unknown span:last-child { color: #f1c40f; }
code { background: #000; padding: 0.1rem 0.3rem; border-radius: 4px; }
"""
