"""Self-contained dark-mode HTML dashboard generator for TripKit trips."""

from __future__ import annotations

import html
import json

CHARTJS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"

MODE_LABELS = {
    "forecast": "Live forecast",
    "climate_normal": "Historical average (not a live forecast)",
}


def _safe_json_for_script(data) -> str:
    """json.dumps that's safe to embed inside a <script> block."""
    return json.dumps(data).replace("</", "<\\/")


def _render_packing_category(category: str, items: list[str], trip_id: int) -> str:
    rows = []
    for index, item in enumerate(items):
        checkbox_id = f"pack-{trip_id}-{category}-{index}".replace(" ", "_")
        safe_item = html.escape(item)
        rows.append(
            f'<label class="pack-item"><input type="checkbox" class="pack-checkbox" '
            f'data-key="{html.escape(checkbox_id)}"> <span>{safe_item}</span></label>'
        )
    items_html = "\n".join(rows)
    return f'<div class="pack-category"><h4>{html.escape(category)}</h4>{items_html}</div>'


def _render_trip_card(trip: dict) -> str:
    trip_id = trip["id"]
    name = html.escape(trip["name"])
    resolved_name = html.escape(trip["resolved_name"])
    start_date = html.escape(trip["start_date"])
    end_date = html.escape(trip["end_date"])
    tags = html.escape(", ".join(trip["activity_tags"]))
    mode_label = html.escape(MODE_LABELS.get(trip["mode"], trip["mode"]))
    briefing = html.escape(trip["briefing"])

    categories_html = "\n".join(
        _render_packing_category(category, items, trip_id) for category, items in trip["packing_list"].items()
    )

    daily_labels = [d["day_date"] for d in trip["daily"]]
    daily_highs = [d["temp_max_c"] for d in trip["daily"]]
    daily_lows = [d["temp_min_c"] for d in trip["daily"]]
    daily_precip = [d["precip_mm"] for d in trip["daily"]]

    chart_data = {
        "labels": daily_labels,
        "highs": daily_highs,
        "lows": daily_lows,
        "precip": daily_precip,
    }

    return f"""
    <section class="trip-card" data-testid="trip-card" data-trip-id="{trip_id}">
      <div class="trip-header">
        <h2>{name}</h2>
        <span class="mode-badge mode-{html.escape(trip["mode"])}">{mode_label}</span>
      </div>
      <p class="trip-meta">{resolved_name} &middot; {start_date} to {end_date} &middot; {tags}</p>
      <canvas id="chart-{trip_id}" height="120" data-testid="trip-chart"></canvas>
      <p class="briefing">{briefing}</p>
      <div class="packing-list">{categories_html}</div>
    </section>
    <script>
      (function() {{
        var ctx = document.getElementById('chart-{trip_id}');
        var data = {_safe_json_for_script(chart_data)};
        if (ctx && window.Chart) {{
          new Chart(ctx, {{
            type: 'line',
            data: {{
              labels: data.labels,
              datasets: [
                {{ label: 'High (C)', data: data.highs, borderColor: '#7dd3fc', tension: 0.3 }},
                {{ label: 'Low (C)', data: data.lows, borderColor: '#38bdf8', tension: 0.3 }},
                {{ label: 'Precip (mm)', data: data.precip, borderColor: '#a78bfa', yAxisID: 'y1', tension: 0.3 }}
              ]
            }},
            options: {{
              responsive: true,
              scales: {{
                y: {{ ticks: {{ color: '#cbd5e1' }} }},
                y1: {{ position: 'right', ticks: {{ color: '#cbd5e1' }}, grid: {{ drawOnChartArea: false }} }},
                x: {{ ticks: {{ color: '#cbd5e1' }} }}
              }},
              plugins: {{ legend: {{ labels: {{ color: '#cbd5e1' }} }} }}
            }}
          }});
        }}
        document.querySelectorAll('[data-trip-id="{trip_id}"] .pack-checkbox').forEach(function(box) {{
          var storeKey = 'tripkit-check-' + box.dataset.key;
          box.checked = localStorage.getItem(storeKey) === '1';
          box.addEventListener('change', function() {{
            localStorage.setItem(storeKey, box.checked ? '1' : '0');
          }});
        }});
      }})();
    </script>
    """


def generate_dashboard_html(trips: list[dict]) -> str:
    """trips: list of dicts with keys id, name, resolved_name, start_date, end_date,
    activity_tags, mode, briefing, daily (list of daily weather dicts), packing_list.
    """
    if trips:
        cards_html = "\n".join(_render_trip_card(trip) for trip in trips)
        empty_state = ""
    else:
        cards_html = ""
        empty_state = '<p class="empty-state" data-testid="empty-state">No trips yet. Add one with `tripkit add`.</p>'

    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TripKit &mdash; Trip Prep Dashboard</title>
<script src="{CHARTJS_CDN}"></script>
<style>
  :root {{
    --bg: #0f172a;
    --card-bg: #1e293b;
    --text: #e2e8f0;
    --muted: #94a3b8;
    --accent: #38bdf8;
    --border: #334155;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 1.5rem;
  }}
  h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
  .subtitle {{ color: var(--muted); margin-top: 0; margin-bottom: 1.5rem; }}
  .trip-card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1.5rem;
    max-width: 900px;
  }}
  .trip-header {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; }}
  .trip-header h2 {{ margin: 0; font-size: 1.15rem; }}
  .mode-badge {{
    font-size: 0.75rem;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    background: #0369a1;
    color: #e0f2fe;
    white-space: nowrap;
  }}
  .mode-badge.mode-climate_normal {{ background: #78350f; color: #fef3c7; }}
  .trip-meta {{ color: var(--muted); font-size: 0.9rem; }}
  .briefing {{ line-height: 1.5; background: #0f172a; border-left: 3px solid var(--accent); padding: 0.75rem 1rem; border-radius: 6px; }}
  .packing-list {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem; }}
  .pack-category h4 {{ margin: 0 0 0.5rem 0; color: var(--accent); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.04em; }}
  .pack-item {{ display: flex; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.35rem; font-size: 0.92rem; cursor: pointer; }}
  canvas {{ max-width: 100%; }}
  .empty-state {{ color: var(--muted); }}
  @media (max-width: 480px) {{
    body {{ padding: 1rem; }}
    .trip-card {{ padding: 1rem; }}
  }}
</style>
</head>
<body>
  <h1>TripKit</h1>
  <p class="subtitle">Weather-aware trip prep, generated locally.</p>
  {cards_html}
  {empty_state}
</body>
</html>
"""
