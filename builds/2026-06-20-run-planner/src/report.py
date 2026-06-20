"""Generate a self-contained HTML dashboard for the run log."""

import json
from datetime import datetime
from typing import List


def _esc(value: object) -> str:
    """HTML-escape a value for safe insertion into HTML content."""
    s = str(value)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    return s


def _run_rows(runs: List[dict]) -> str:
    rows = ""
    for r in sorted(runs, key=lambda x: x["date"], reverse=True)[:30]:
        effort = r.get("effort", "moderate")
        rows += (
            f"<tr>"
            f"<td>{_esc(r['date'])}</td>"
            f"<td>{_esc(r.get('distance_km', ''))}</td>"
            f"<td>{_esc(r.get('pace', ''))}</td>"
            f"<td class='effort-{_esc(effort)}'>{_esc(effort)}</td>"
            f"<td>{_esc(r.get('notes', ''))}</td>"
            f"</tr>"
        )
    return rows


def _window_rows(windows: List[dict]) -> str:
    rows = ""
    for w in windows:
        try:
            dt = datetime.fromisoformat(w["time"])
            time_str = dt.strftime("%a %b %d, %-I%p")
        except (ValueError, KeyError):
            time_str = _esc(w.get("time", ""))
        label = w.get("label", "")
        rows += (
            f"<tr>"
            f"<td>{_esc(time_str)}</td>"
            f"<td>{_esc(w.get('apparent_temp_c', ''))}°C</td>"
            f"<td>{_esc(w.get('wind_speed_kmh', ''))} km/h</td>"
            f"<td>{_esc(w.get('precip_probability', ''))}%</td>"
            f"<td>{_esc(w.get('score', ''))}</td>"
            f"<td class='label-{label.lower()}'>{_esc(label)}</td>"
            f"</tr>"
        )
    return rows


def render_html(
    runs: List[dict],
    weekly_data: List[dict],
    best_windows: List[dict],
    summary: dict,
) -> str:
    """Render a self-contained HTML report string."""
    chart_labels = json.dumps([f"Wk {d['week']}" for d in weekly_data[-12:]])
    chart_data = json.dumps([d["km"] for d in weekly_data[-12:]])
    total_km_all = round(sum(r.get("distance_km", 0) for r in runs), 1)

    run_section = (
        f"<table><thead><tr>"
        f"<th>Date</th><th>Distance (km)</th><th>Pace (min/km)</th>"
        f"<th>Effort</th><th>Notes</th>"
        f"</tr></thead><tbody>{_run_rows(runs)}</tbody></table>"
        if runs
        else "<p class='empty'>No runs logged yet. Use <code>python src/main.py log</code> to add your first run.</p>"
    )

    window_section = (
        f"<table><thead><tr>"
        f"<th>Time</th><th>Feels Like</th><th>Wind</th><th>Rain %</th>"
        f"<th>Score</th><th>Rating</th>"
        f"</tr></thead><tbody>{_window_rows(best_windows)}</tbody></table>"
        if best_windows
        else "<p class='empty'>No forecast data — run with <code>python src/main.py report</code> (without --no-weather) to fetch the 7-day forecast.</p>"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Run Planner — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg: #0f0f0f;
  --surface: #1a1a1a;
  --border: #2a2a2a;
  --text: #e0e0e0;
  --dim: #888;
  --green: #4ade80;
  --blue: #60a5fa;
  --orange: #fb923c;
  --red: #f87171;
  --radius: 8px;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; padding: 1.5rem; max-width: 960px; margin: 0 auto; }}
h1 {{ color: var(--green); font-size: 1.5rem; margin-bottom: 0.2rem; }}
.subtitle {{ color: var(--dim); font-size: 0.85rem; margin-bottom: 2rem; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
.card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem; }}
.card-label {{ font-size: 0.7rem; color: var(--dim); text-transform: uppercase; letter-spacing: 0.06em; }}
.card-value {{ font-size: 1.8rem; font-weight: 700; color: var(--green); line-height: 1.2; margin-top: 0.2rem; }}
.card-unit {{ font-size: 0.7rem; color: var(--dim); }}
section {{ margin-bottom: 2rem; }}
h2 {{ font-size: 0.8rem; color: var(--dim); text-transform: uppercase; letter-spacing: 0.08em; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 1rem; }}
.chart-wrap {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem; height: 220px; }}
table {{ width: 100%; border-collapse: collapse; background: var(--surface); border-radius: var(--radius); overflow: hidden; font-size: 0.875rem; }}
th {{ background: #222; color: var(--dim); font-size: 0.7rem; text-transform: uppercase; padding: 0.5rem 0.75rem; text-align: left; }}
td {{ padding: 0.5rem 0.75rem; border-top: 1px solid var(--border); }}
tr:hover td {{ background: #222; }}
.effort-easy {{ color: var(--green); }}
.effort-moderate {{ color: var(--blue); }}
.effort-hard {{ color: var(--orange); }}
.label-excellent {{ color: var(--green); font-weight: 600; }}
.label-good {{ color: var(--blue); }}
.label-fair {{ color: var(--orange); }}
.label-poor {{ color: var(--red); }}
.empty {{ color: var(--dim); font-size: 0.875rem; padding: 1rem; background: var(--surface); border-radius: var(--radius); border: 1px solid var(--border); }}
code {{ background: #2a2a2a; padding: 0.1em 0.4em; border-radius: 3px; font-size: 0.85em; }}
@media (max-width: 480px) {{ .cards {{ grid-template-columns: 1fr 1fr; }} body {{ padding: 1rem; }} }}
</style>
</head>
<body>
<h1>Run Planner</h1>
<p class="subtitle">Training log &amp; weather planning — Toronto</p>

<div class="cards">
  <div class="card">
    <div class="card-label">This Week</div>
    <div class="card-value">{_esc(summary.get('total_km', 0))}</div>
    <div class="card-unit">km</div>
  </div>
  <div class="card">
    <div class="card-label">Runs This Week</div>
    <div class="card-value">{_esc(summary.get('run_count', 0))}</div>
    <div class="card-unit">sessions</div>
  </div>
  <div class="card">
    <div class="card-label">Avg Pace</div>
    <div class="card-value">{_esc(summary.get('avg_pace', '--:--'))}</div>
    <div class="card-unit">min / km</div>
  </div>
  <div class="card">
    <div class="card-label">All-Time</div>
    <div class="card-value">{_esc(total_km_all)}</div>
    <div class="card-unit">km logged</div>
  </div>
</div>

<section>
  <h2>Weekly Mileage — Last 12 Weeks</h2>
  <div class="chart-wrap">
    <canvas id="mileageChart"></canvas>
  </div>
</section>

<section>
  <h2>Best Running Windows — Next 7 Days</h2>
  {window_section}
</section>

<section>
  <h2>Recent Runs</h2>
  {run_section}
</section>

<script>
const ctx = document.getElementById('mileageChart').getContext('2d');
new Chart(ctx, {{
  type: 'bar',
  data: {{
    labels: {chart_labels},
    datasets: [{{
      label: 'km',
      data: {chart_data},
      backgroundColor: 'rgba(74, 222, 128, 0.4)',
      borderColor: 'rgba(74, 222, 128, 0.9)',
      borderWidth: 1,
      borderRadius: 4,
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      y: {{
        beginAtZero: true,
        grid: {{ color: 'rgba(255,255,255,0.05)' }},
        ticks: {{ color: '#888', font: {{ size: 11 }} }}
      }},
      x: {{
        grid: {{ display: false }},
        ticks: {{ color: '#888', font: {{ size: 11 }} }}
      }}
    }}
  }}
}});
</script>
</body>
</html>"""
