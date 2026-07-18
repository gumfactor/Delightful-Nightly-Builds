"""Renders the self-contained dark-mode HTML dashboard."""
from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Tuple

from src.deltas import DeltaSummary
from src.indicators import Indicator

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


@dataclass(frozen=True)
class IndicatorSnapshot:
    indicator: Indicator
    history: List[Tuple[date, float]]
    deltas: Optional[DeltaSummary]
    last_fetched_at: Optional[str]


def render_dashboard(
    snapshots: List[IndicatorSnapshot],
    briefing_text: str,
    briefing_source: str,
    generated_at: datetime,
) -> str:
    panels_html = "\n".join(_render_panel(index, snap) for index, snap in enumerate(snapshots))
    chart_payload = _safe_json_for_script(
        {
            f"chart-{index}": {
                "labels": [d.isoformat() for d, _ in snap.history],
                "values": [v for _, v in snap.history],
                "label": snap.indicator.label,
            }
            for index, snap in enumerate(snapshots)
            if snap.history
        }
    )
    briefing_badge = "AI-generated" if briefing_source == "ai" else "Template-generated"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CanEcon Pulse</title>
<style>
  :root {{
    --bg: #0f1115;
    --panel: #171a21;
    --border: #2a2f3a;
    --text: #e7e9ee;
    --text-dim: #9aa2b1;
    --accent-up: #4fb3ff;
    --accent-down: #ff9f5a;
    --accent-neutral: #7c8393;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 24px;
  }}
  header {{ margin-bottom: 24px; }}
  h1 {{ margin: 0 0 4px 0; font-size: 1.6rem; }}
  .subtitle {{ color: var(--text-dim); font-size: 0.9rem; }}
  .briefing {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 24px;
  }}
  .briefing .badge {{
    display: inline-block;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-dim);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 2px 8px;
    margin-bottom: 8px;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 16px;
  }}
  .panel {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
  }}
  .panel h2 {{ margin: 0 0 4px 0; font-size: 1.05rem; }}
  .panel .unit {{ color: var(--text-dim); font-size: 0.8rem; margin-bottom: 10px; }}
  .latest {{ font-size: 1.8rem; font-weight: 600; margin-bottom: 6px; }}
  .deltas {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }}
  .delta-badge {{
    font-size: 0.75rem;
    border-radius: 6px;
    padding: 3px 8px;
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border);
  }}
  .delta-up {{ color: var(--accent-up); }}
  .delta-down {{ color: var(--accent-down); }}
  .empty-state {{ color: var(--text-dim); font-size: 0.85rem; padding: 24px 0; text-align: center; }}
  .freshness {{ color: var(--text-dim); font-size: 0.72rem; margin-top: 8px; }}
  canvas {{ max-height: 180px; }}
  #fallback-note {{ display: none; color: var(--accent-down); font-size: 0.8rem; margin-bottom: 16px; }}
</style>
</head>
<body>
<header>
  <h1>CanEcon Pulse</h1>
  <div class="subtitle">Live Canadian economic indicators — generated {html.escape(generated_at.strftime('%Y-%m-%d %H:%M UTC'))}</div>
</header>

<div id="fallback-note">Chart.js could not be loaded from the CDN — showing indicator data as text only.</div>

<div class="briefing">
  <span class="badge">{html.escape(briefing_badge)}</span>
  <div>{html.escape(briefing_text)}</div>
</div>

<div class="grid">
{panels_html}
</div>

<script src="{CHART_JS_CDN}" onerror="window.__chartJsFailed = true;"></script>
<script>
  const CHART_DATA = {chart_payload};

  function renderFallbackTables() {{
    document.getElementById('fallback-note').style.display = 'block';
    Object.keys(CHART_DATA).forEach(function (key) {{
      const canvas = document.getElementById(key);
      if (!canvas) return;
      const data = CHART_DATA[key];
      const wrapper = document.createElement('div');
      wrapper.style.fontSize = '0.75rem';
      wrapper.style.color = 'var(--text-dim)';
      const rows = data.labels.map(function (d, i) {{
        return d + ': ' + data.values[i];
      }});
      wrapper.textContent = rows.slice(-8).join(' | ');
      canvas.replaceWith(wrapper);
    }});
  }}

  function renderCharts() {{
    Object.keys(CHART_DATA).forEach(function (key) {{
      const canvas = document.getElementById(key);
      if (!canvas) return;
      const data = CHART_DATA[key];
      new Chart(canvas, {{
        type: 'line',
        data: {{
          labels: data.labels,
          datasets: [{{
            label: data.label,
            data: data.values,
            borderColor: '#4fb3ff',
            backgroundColor: 'rgba(79,179,255,0.12)',
            tension: 0.25,
            pointRadius: 2,
            fill: true,
          }}],
        }},
        options: {{
          responsive: true,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9aa2b1', maxTicksLimit: 6 }}, grid: {{ color: '#2a2f3a' }} }},
            y: {{ ticks: {{ color: '#9aa2b1' }}, grid: {{ color: '#2a2f3a' }} }},
          }},
        }},
      }});
    }});
  }}

  window.addEventListener('DOMContentLoaded', function () {{
    if (window.__chartJsFailed || typeof Chart === 'undefined') {{
      renderFallbackTables();
    }} else {{
      renderCharts();
    }}
  }});
</script>
</body>
</html>
"""


def _render_panel(index: int, snap: IndicatorSnapshot) -> str:
    label = html.escape(snap.indicator.label)
    unit = html.escape(snap.indicator.unit)
    source = html.escape(snap.indicator.source)

    if not snap.history or snap.deltas is None:
        return f"""<div class="panel">
  <h2>{label}</h2>
  <div class="unit">{unit} &middot; {source}</div>
  <div class="empty-state">No data yet — run <code>sync</code> to fetch history.</div>
</div>"""

    deltas = snap.deltas
    latest_display = html.escape(f"{deltas.latest_value:g}")
    badges = "".join(
        _render_delta_badge(period_label, deltas)
        for period_label in ("day", "week", "month")
    )
    freshness = (
        html.escape(snap.last_fetched_at) if snap.last_fetched_at else "unknown"
    )

    return f"""<div class="panel">
  <h2>{label}</h2>
  <div class="unit">{unit} &middot; {source}</div>
  <div class="latest">{latest_display}</div>
  <div class="deltas">{badges}</div>
  <canvas id="chart-{index}"></canvas>
  <div class="freshness">Last synced: {freshness} &middot; as of {html.escape(deltas.latest_date.isoformat())}</div>
</div>"""


def _render_delta_badge(period_label: str, deltas: DeltaSummary) -> str:
    period = getattr(deltas, period_label)
    if period is None:
        return f'<span class="delta-badge">{period_label}: n/a</span>'
    direction_class = "delta-up" if period.change >= 0 else "delta-down"
    arrow = "&uarr;" if period.change >= 0 else "&darr;"
    pct_text = f"{abs(period.pct_change):.2f}%" if period.pct_change is not None else "n/a"
    return (
        f'<span class="delta-badge {direction_class}">{period_label}: {arrow} {pct_text}</span>'
    )


def _safe_json_for_script(data: dict) -> str:
    """JSON-encode for embedding inside a <script> tag, escaping '</' to
    prevent premature script-tag closure."""
    return json.dumps(data).replace("</", "<\\/")
