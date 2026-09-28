"""Renders the self-contained Outdoor Ops HTML dashboard.

No bundler, no build step — opens directly via file://. Chart.js is loaded
from a pinned-version CDN URL. All user/API-derived text is escaped before
interpolation.
"""

from __future__ import annotations

import html
import json
from typing import List, Mapping, Optional

CHART_JS_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"

WEATHERCODE_LABELS = {
    0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Freezing fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Heavy showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Severe thunderstorm w/ hail",
}


def _weather_label(code: Optional[int]) -> str:
    if code is None:
        return "Unknown"
    return WEATHERCODE_LABELS.get(int(code), "Unknown")


def _safe_json(obj) -> str:
    """json.dumps that is safe to embed inside an inline <script> block.

    A JSON string value containing the literal substring "</script>" would
    otherwise close the surrounding <script> tag early (the HTML parser
    scans for that substring regardless of JS string-literal context),
    letting an attacker-controlled forecast date break out and inject
    markup/script. Escaping "/" as "\\/" is valid, semantically-unchanged
    JSON/JS and removes every occurrence of "</" from the output.
    """
    return json.dumps(obj).replace("</", "<\\/")


def _score_class(score: float) -> str:
    if score >= 75:
        return "score-good"
    if score >= 50:
        return "score-ok"
    return "score-poor"


def _score_card(label: str, day: Optional[str], score: Optional[float]) -> str:
    if day is None or score is None:
        return f"""
        <div class="card">
          <div class="card-label">{html.escape(label)}</div>
          <div class="card-value">--</div>
          <div class="card-sub">No data yet</div>
        </div>"""
    return f"""
        <div class="card">
          <div class="card-label">{html.escape(label)}</div>
          <div class="card-value {_score_class(score)}">{score:.0f}</div>
          <div class="card-sub">{html.escape(day)}</div>
        </div>"""


def render_dashboard(
    location_name: str,
    days: List[Mapping],
    summary: dict,
    coach_note: str,
    sync_count: int,
    last_sync_time: Optional[str],
) -> str:
    today = days[0] if days else None
    location_safe = html.escape(location_name)
    coach_note_safe = html.escape(coach_note)
    last_sync_safe = html.escape(last_sync_time) if last_sync_time else "never"

    hero_cards = "".join([
        _score_card("Today's Running Score", today["forecast_date"] if today else None,
                    today["running_score"] if today else None),
        _score_card("Today's Golf Score", today["forecast_date"] if today else None,
                    today["golf_score"] if today else None),
        _score_card("Best Day to Run", summary.get("best_running_day"), summary.get("best_running_score")),
        _score_card("Best Day to Golf", summary.get("best_golf_day"), summary.get("best_golf_score")),
    ])

    table_rows = "".join(f"""
        <tr>
          <td>{html.escape(d['forecast_date'])}</td>
          <td>{html.escape(_weather_label(d.get('weathercode')))}</td>
          <td>{d['temp_min']:.0f}&ndash;{d['temp_max']:.0f}&deg;C</td>
          <td>{d['precip_prob_max']:.0f}%</td>
          <td>{d['wind_max']:.0f} km/h</td>
          <td>{d['aqi_max']:.0f}</td>
          <td class="{_score_class(d['running_score'])}">{d['running_score']:.0f}</td>
          <td class="{_score_class(d['golf_score'])}">{d['golf_score']:.0f}</td>
        </tr>""" for d in days)

    chart_labels = _safe_json([d["forecast_date"] for d in days])
    temp_max_data = _safe_json([d["temp_max"] for d in days])
    temp_min_data = _safe_json([d["temp_min"] for d in days])
    precip_data = _safe_json([d["precip_prob_max"] for d in days])
    wind_data = _safe_json([d["wind_max"] for d in days])
    aqi_data = _safe_json([d["aqi_max"] for d in days])
    running_data = _safe_json([d["running_score"] for d in days])
    golf_data = _safe_json([d["golf_score"] for d in days])

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Outdoor Ops — {location_safe}</title>
<script src="{CHART_JS_URL}"></script>
<style>
  :root {{
    --bg: #0b0f14; --bg-card: #131a22; --text: #e8edf2; --text-dim: #93a1af;
    --border: #223040; --good: #37d67a; --ok: #f5c451; --poor: #f5726b;
    --accent: #4fb2f5;
  }}
  @media (prefers-color-scheme: light) {{
    :root:not([data-theme="dark"]) {{
      --bg: #f4f7fa; --bg-card: #ffffff; --text: #1a2430; --text-dim: #56646f;
      --border: #dde5ec;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 16px; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  h1 {{ font-size: 1.4rem; margin: 0 0 4px; }}
  .meta {{ color: var(--text-dim); font-size: 0.85rem; margin-bottom: 20px; }}
  .cards {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px; margin-bottom: 20px;
  }}
  .card {{
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px;
    padding: 14px;
  }}
  .card-label {{ color: var(--text-dim); font-size: 0.78rem; margin-bottom: 6px; }}
  .card-value {{ font-size: 1.9rem; font-weight: 700; }}
  .card-sub {{ color: var(--text-dim); font-size: 0.78rem; margin-top: 4px; }}
  .score-good {{ color: var(--good); }}
  .score-ok {{ color: var(--ok); }}
  .score-poor {{ color: var(--poor); }}
  .note {{
    background: var(--bg-card); border: 1px solid var(--border); border-left: 3px solid var(--accent);
    border-radius: 8px; padding: 14px; margin-bottom: 20px; font-size: 0.92rem;
  }}
  .charts {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px; margin-bottom: 20px;
  }}
  .chart-box {{
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px;
  }}
  .chart-fallback {{ color: var(--text-dim); font-size: 0.85rem; margin: 0; }}
  table {{ width: 100%; border-collapse: collapse; background: var(--bg-card); border-radius: 10px; overflow: hidden; }}
  th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.85rem; }}
  th {{ color: var(--text-dim); font-weight: 600; }}
  .table-wrap {{ overflow-x: auto; }}
</style>
</head>
<body>
  <h1>Outdoor Ops — {location_safe}</h1>
  <div class="meta">{sync_count} sync{'es' if sync_count != 1 else ''} recorded &middot; last synced {last_sync_safe}</div>

  <div class="cards">{hero_cards}</div>

  <div class="note"><strong>Coach's note:</strong> {coach_note_safe}</div>

  <div class="charts">
    <div class="chart-box"><canvas id="tempChart" data-testid="temp-chart"></canvas></div>
    <div class="chart-box"><canvas id="windAqiChart" data-testid="wind-aqi-chart"></canvas></div>
    <div class="chart-box"><canvas id="scoreChart" data-testid="score-chart"></canvas></div>
  </div>

  <div class="table-wrap">
    <table data-testid="score-table">
      <thead>
        <tr><th>Date</th><th>Weather</th><th>Temp</th><th>Rain%</th><th>Wind</th><th>AQI</th><th>Run</th><th>Golf</th></tr>
      </thead>
      <tbody>{table_rows}</tbody>
    </table>
  </div>

<script>
  const labels = {chart_labels};
  if (typeof Chart === 'undefined') {{
    document.querySelectorAll('.chart-box').forEach(function (box) {{
      box.innerHTML = '<p class="chart-fallback">Chart.js could not load from the CDN '
        + '(offline, or the network blocked cdn.jsdelivr.net). The score table below has the same data.</p>';
    }});
  }} else {{
    new Chart(document.getElementById('tempChart'), {{
      type: 'line',
      data: {{
        labels,
        datasets: [
          {{ label: 'Temp Max (C)', data: {temp_max_data}, borderColor: '#f5726b', tension: 0.3 }},
          {{ label: 'Temp Min (C)', data: {temp_min_data}, borderColor: '#4fb2f5', tension: 0.3 }},
          {{ label: 'Rain %', data: {precip_data}, borderColor: '#f5c451', yAxisID: 'y1', tension: 0.3 }}
        ]
      }},
      options: {{
        responsive: true,
        scales: {{ y1: {{ position: 'right', min: 0, max: 100, grid: {{ drawOnChartArea: false }} }} }}
      }}
    }});
    new Chart(document.getElementById('windAqiChart'), {{
      type: 'bar',
      data: {{
        labels,
        datasets: [
          {{ label: 'Wind Max (km/h)', data: {wind_data}, backgroundColor: '#4fb2f5' }},
          {{ label: 'AQI Max', data: {aqi_data}, backgroundColor: '#f5c451' }}
        ]
      }},
      options: {{ responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
    }});
    new Chart(document.getElementById('scoreChart'), {{
      type: 'line',
      data: {{
        labels,
        datasets: [
          {{ label: 'Running Score', data: {running_data}, borderColor: '#37d67a', tension: 0.3 }},
          {{ label: 'Golf Score', data: {golf_data}, borderColor: '#f5c451', tension: 0.3 }}
        ]
      }},
      options: {{ responsive: true, scales: {{ y: {{ min: 0, max: 100 }} }} }}
    }});
  }}
</script>
</body>
</html>
"""
