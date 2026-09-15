"""Self-contained HTML dashboard + CSV export generation.

Every dynamic string (ticker, quadrant, commentary, benchmark) is HTML-escaped.
The embedded data block is plain JSON inside a non-executable
<script type="application/json"> tag, with any literal "</script" sequence
neutralized so a hostile string can never terminate the tag early.
"""

from __future__ import annotations

import csv
import html
import io
import json

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


def _escape(value: str) -> str:
    return html.escape(str(value), quote=True)


def _safe_json_block(data: dict) -> str:
    raw = json.dumps(data)
    return raw.replace("</", "<\\/")


def build_csv(history_rows: list) -> str:
    """history_rows: list[(ticker, run_timestamp, rs_ratio, rs_momentum, quadrant)]."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["ticker", "run_timestamp", "rs_ratio", "rs_momentum", "quadrant"])
    for row in history_rows:
        writer.writerow(row)
    return buffer.getvalue()


def build_html(
    snapshots: dict,
    transitions: list,
    commentary: str,
    benchmark: str,
    generated_at: str,
    tail_length: int,
) -> str:
    transition_by_ticker = {t.ticker: t for t in transitions}

    table_rows = []
    for ticker in sorted(snapshots.keys()):
        result = snapshots[ticker]
        latest = result.latest
        prev = result.previous
        day_change = None if prev is None else latest.rs_ratio - prev.rs_ratio
        transition = transition_by_ticker.get(ticker)
        changed_badge = (
            f' <span class="badge changed">{_escape(transition.previous_quadrant)} &rarr; '
            f'{_escape(latest.quadrant)}</span>'
            if transition and transition.changed
            else ""
        )
        change_str = "—" if day_change is None else f"{day_change:+.2f}"
        table_rows.append(
            f"<tr><td>{_escape(ticker)}</td>"
            f"<td>{latest.rs_ratio:.2f}</td>"
            f"<td>{latest.rs_momentum:.2f}</td>"
            f"<td><span class=\"quad quad-{_escape(latest.quadrant.lower())}\">"
            f"{_escape(latest.quadrant)}</span>{changed_badge}</td>"
            f"<td>{change_str}</td></tr>"
        )

    chart_datasets = []
    for ticker in sorted(snapshots.keys()):
        result = snapshots[ticker]
        chart_datasets.append(
            {
                "ticker": _escape(ticker),
                "points": [{"x": p.rs_ratio, "y": p.rs_momentum, "date": p.date} for p in result.tail],
            }
        )

    commentary_js = json.dumps(commentary).replace("</", "<\\/")

    data_block = _safe_json_block(
        {
            "benchmark": benchmark,
            "generated_at": generated_at,
            "tail_length": tail_length,
            "datasets": chart_datasets,
        }
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rotation Radar</title>
<script src="{CHART_JS_CDN}"></script>
<style>
  :root {{
    --bg: #0f1117; --panel: #171a24; --border: #2a2f3d; --text: #e6e8ee;
    --muted: #9aa1b2; --leading: #35c47a; --improving: #4c8bf5;
    --weakening: #e0b83c; --lagging: #e0554c; --accent: #7c9cff;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 1.25rem; max-width: 1100px; margin-inline: auto;
  }}
  h1 {{ font-size: 1.4rem; margin-bottom: 0.1rem; }}
  .meta {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 1.25rem; }}
  .panel {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem; margin-bottom: 1.25rem;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th, td {{ text-align: left; padding: 0.5rem 0.6rem; border-bottom: 1px solid var(--border); }}
  th {{ cursor: pointer; color: var(--muted); user-select: none; }}
  th:hover {{ color: var(--text); }}
  .quad {{ padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }}
  .quad-leading {{ background: color-mix(in srgb, var(--leading) 25%, transparent); color: var(--leading); }}
  .quad-improving {{ background: color-mix(in srgb, var(--improving) 25%, transparent); color: var(--improving); }}
  .quad-weakening {{ background: color-mix(in srgb, var(--weakening) 25%, transparent); color: var(--weakening); }}
  .quad-lagging {{ background: color-mix(in srgb, var(--lagging) 25%, transparent); color: var(--lagging); }}
  .badge.changed {{ font-size: 0.75rem; color: var(--accent); margin-left: 0.35rem; }}
  #chart-wrap {{ position: relative; height: 420px; }}
  a.export {{ color: var(--accent); text-decoration: none; font-size: 0.85rem; }}
  @media (max-width: 480px) {{ body {{ padding: 0.75rem; }} th, td {{ padding: 0.4rem; }} }}
</style>
</head>
<body>
<h1>Rotation Radar</h1>
<div class="meta">Benchmark: {_escape(benchmark)} &middot; Generated {_escape(generated_at)}</div>

<div class="panel">
  <div id="chart-wrap"><canvas id="rrg-chart" role="img" aria-label="Relative Rotation Graph"></canvas></div>
</div>

<div class="panel">
  <h2 style="font-size:1.05rem;margin-top:0;">Commentary</h2>
  <p id="commentary-text" style="color: var(--muted); line-height: 1.5;"></p>
</div>

<div class="panel">
  <h2 style="font-size:1.05rem;margin-top:0;">Sectors</h2>
  <table id="sector-table">
    <thead><tr>
      <th data-key="ticker">Ticker</th><th data-key="rs_ratio">RS-Ratio</th>
      <th data-key="rs_momentum">RS-Momentum</th><th data-key="quadrant">Quadrant</th>
      <th data-key="change">Ratio &Delta; (1d)</th>
    </tr></thead>
    <tbody>
{"".join(table_rows)}
    </tbody>
  </table>
  <p><a class="export" id="csv-link" href="#" download="rotation_radar_history.csv">Export full history as CSV</a></p>
</div>

<script id="rr-data" type="application/json">{data_block}</script>
<script>
(function () {{
  var raw = document.getElementById('rr-data').textContent;
  var data = JSON.parse(raw);
  var commentary = {commentary_js};
  document.getElementById('commentary-text').textContent = commentary;

  var colors = {{'XLK':'#7c9cff','XLF':'#35c47a','XLE':'#e0554c','XLV':'#4c8bf5','XLI':'#e0b83c',
    'XLY':'#c47cff','XLP':'#4cc9f0','XLU':'#f28cb1','XLB':'#94d82d','XLRE':'#ff922b','XLC':'#63e6be'}};

  var datasets = data.datasets.map(function (d) {{
    var color = colors[d.ticker] || '#9aa1b2';
    return {{
      label: d.ticker,
      data: d.points,
      showLine: true,
      borderColor: color,
      backgroundColor: color,
      pointRadius: d.points.map(function (_, i) {{ return i === d.points.length - 1 ? 6 : 2; }}),
      pointStyle: d.points.map(function (_, i) {{ return i === d.points.length - 1 ? 'rectRot' : 'circle'; }}),
    }};
  }});

  var quadrantBg = {{
    id: 'quadrantBg',
    beforeDraw: function (chart) {{
      var ctx = chart.ctx, area = chart.chartArea;
      if (!area) return;
      var xScale = chart.scales.x, yScale = chart.scales.y;
      var midX = xScale.getPixelForValue(100), midY = yScale.getPixelForValue(100);
      ctx.save();
      ctx.fillStyle = 'rgba(76,139,245,0.06)';
      ctx.fillRect(area.left, area.top, midX - area.left, midY - area.top);
      ctx.fillStyle = 'rgba(53,196,122,0.06)';
      ctx.fillRect(midX, area.top, area.right - midX, midY - area.top);
      ctx.fillStyle = 'rgba(224,85,76,0.06)';
      ctx.fillRect(area.left, midY, midX - area.left, area.bottom - midY);
      ctx.fillStyle = 'rgba(224,184,60,0.06)';
      ctx.fillRect(midX, midY, area.right - midX, area.bottom - midY);
      ctx.strokeStyle = 'rgba(255,255,255,0.15)';
      ctx.beginPath(); ctx.moveTo(midX, area.top); ctx.lineTo(midX, area.bottom); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(area.left, midY); ctx.lineTo(area.right, midY); ctx.stroke();
      ctx.restore();
    }}
  }};

  if (window.Chart) {{
    new Chart(document.getElementById('rrg-chart'), {{
      type: 'scatter',
      data: {{ datasets: datasets }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        scales: {{
          x: {{ title: {{ display: true, text: 'RS-Ratio', color: '#9aa1b2' }}, grid: {{ color: '#2a2f3d' }}, ticks: {{ color: '#9aa1b2' }} }},
          y: {{ title: {{ display: true, text: 'RS-Momentum', color: '#9aa1b2' }}, grid: {{ color: '#2a2f3d' }}, ticks: {{ color: '#9aa1b2' }} }}
        }},
        plugins: {{ legend: {{ labels: {{ color: '#e6e8ee' }} }} }}
      }},
      plugins: [quadrantBg]
    }});
  }} else {{
    document.getElementById('chart-wrap').innerHTML =
      '<p style="color:var(--muted)">Chart.js failed to load (offline?) — see the Sectors table below for the same data.</p>';
  }}

  var sortState = {{ key: null, dir: 1 }};
  document.querySelectorAll('#sector-table th').forEach(function (th) {{
    th.addEventListener('click', function () {{
      var key = th.getAttribute('data-key');
      var tbody = document.querySelector('#sector-table tbody');
      var rows = Array.from(tbody.querySelectorAll('tr'));
      var keyIndex = {{ ticker: 0, rs_ratio: 1, rs_momentum: 2, quadrant: 3, change: 4 }}[key];
      sortState.dir = sortState.key === key ? -sortState.dir : 1;
      sortState.key = key;
      rows.sort(function (a, b) {{
        var av = a.children[keyIndex].textContent.trim();
        var bv = b.children[keyIndex].textContent.trim();
        var an = parseFloat(av), bn = parseFloat(bv);
        var cmp = (!isNaN(an) && !isNaN(bn)) ? (an - bn) : av.localeCompare(bv);
        return cmp * sortState.dir;
      }});
      rows.forEach(function (r) {{ tbody.appendChild(r); }});
    }});
  }});

  var csvRows = [['ticker', 'date', 'rs_ratio', 'rs_momentum', 'quadrant']];
  data.datasets.forEach(function (d) {{
    d.points.forEach(function (p) {{
      csvRows.push([d.ticker, p.date, p.x, p.y, '']);
    }});
  }});
  var csvText = csvRows.map(function (r) {{ return r.join(','); }}).join('\\n');
  var blob = new Blob([csvText], {{ type: 'text/csv' }});
  document.getElementById('csv-link').href = URL.createObjectURL(blob);
}})();
</script>
</body>
</html>
"""
