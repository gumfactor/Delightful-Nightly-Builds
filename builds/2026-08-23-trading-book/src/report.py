"""Renders the self-contained dark-mode HTML dashboard.

All dynamic data is delivered to the browser as a single escaped JSON blob
read via ``textContent`` (never interpolated into markup), and every DOM
node the client script builds from that data uses ``createElement``/
``textContent`` only — never ``innerHTML`` from user- or account-derived
strings. This keeps a malicious position symbol (or an AI-generated note)
from ever being interpreted as HTML.
"""

from __future__ import annotations

import json
from typing import Any

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


def build_report_payload(snapshots: list[dict[str, Any]], ai_note: str | None) -> dict[str, Any]:
    """Turn the raw snapshot/position rows from storage.py into the compact
    shape the dashboard's client-side script expects."""
    trend = [
        {
            "date": s["snapshot_date"],
            "net_liquidation": s["net_liquidation"],
            "unrealized_pnl": s["unrealized_pnl"],
        }
        for s in snapshots
    ]

    latest = snapshots[-1] if snapshots else None
    latest_payload = None
    if latest is not None:
        allocation: dict[str, float] = {}
        for position in latest["positions"]:
            allocation[position["sec_type"]] = allocation.get(position["sec_type"], 0.0) + position["market_value"]

        previous = snapshots[-2] if len(snapshots) > 1 else None
        day_change_pct = 0.0
        if previous and previous["net_liquidation"]:
            day_change_pct = (
                (latest["net_liquidation"] - previous["net_liquidation"]) / abs(previous["net_liquidation"]) * 100
            )

        latest_payload = {
            "snapshot_date": latest["snapshot_date"],
            "net_liquidation": latest["net_liquidation"],
            "total_cash": latest["total_cash"],
            "unrealized_pnl": latest["unrealized_pnl"],
            "realized_pnl": latest["realized_pnl"],
            "day_change_pct": day_change_pct,
            "allocation": allocation,
            "positions": latest["positions"],
        }

    return {
        "trend": trend,
        "latest": latest_payload,
        "ai_note": ai_note,
    }


def build_aggregate_summary(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the aggregate-only (no dollar figures, no account ID) summary
    handed to ai_briefing.build_briefing()."""
    if not snapshots:
        return {"day_change_pct": 0.0, "allocation_pct": {}, "top_movers": []}

    latest = snapshots[-1]
    previous = snapshots[-2] if len(snapshots) > 1 else None

    day_change_pct = 0.0
    if previous and previous["net_liquidation"]:
        day_change_pct = (
            (latest["net_liquidation"] - previous["net_liquidation"]) / abs(previous["net_liquidation"]) * 100
        )

    positions = latest["positions"]
    total_value = sum(abs(p["market_value"]) for p in positions) or 1.0
    allocation_totals: dict[str, float] = {}
    for position in positions:
        allocation_totals[position["sec_type"]] = allocation_totals.get(position["sec_type"], 0.0) + abs(
            position["market_value"]
        )
    allocation_pct = {k: (v / total_value) * 100 for k, v in allocation_totals.items()}

    movers = []
    for position in positions:
        if position["avg_cost"]:
            pct_change = (position["market_price"] - position["avg_cost"]) / abs(position["avg_cost"]) * 100
            movers.append({"symbol": position["symbol"], "pct_change": pct_change})
    movers.sort(key=lambda m: abs(m["pct_change"]), reverse=True)

    return {
        "day_change_pct": day_change_pct,
        "allocation_pct": allocation_pct,
        "top_movers": movers[:3],
    }


def render_dashboard(snapshots: list[dict[str, Any]], ai_note: str | None = None) -> str:
    payload = build_report_payload(snapshots, ai_note)
    json_payload = json.dumps(payload).replace("</", "<\\/")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trading Book</title>
<style>
  :root {{
    --bg: #0f1115; --panel: #171a21; --border: #262b36; --text: #e6e9f0;
    --muted: #8b93a7; --accent: #4f8cff; --green: #37c977; --red: #ff5c5c;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 24px; line-height: 1.4;
  }}
  h1 {{ font-size: 1.4rem; margin: 0 0 4px; }}
  .subtitle {{ color: var(--muted); margin: 0 0 24px; font-size: 0.9rem; }}
  .hero {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px; margin-bottom: 24px;
  }}
  .card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px;
  }}
  .stat-label {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }}
  .stat-value {{ font-size: 1.5rem; font-weight: 600; margin-top: 4px; }}
  .positive {{ color: var(--green); }}
  .negative {{ color: var(--red); }}
  .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px; margin-bottom: 24px; }}
  .panel h2 {{ margin: 0 0 12px; font-size: 1.05rem; }}
  .charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  canvas {{ max-height: 260px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 500; cursor: pointer; user-select: none; }}
  tr:hover td {{ background: #1c2029; }}
  input[type="search"] {{
    background: var(--bg); border: 1px solid var(--border); color: var(--text);
    padding: 8px 10px; border-radius: 6px; margin-bottom: 12px; width: 100%; max-width: 320px;
  }}
  .fallback-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  .empty-state {{ color: var(--muted); padding: 40px 0; text-align: center; }}
  .ai-note {{ color: var(--text); font-size: 0.92rem; }}
  @media (max-width: 480px) {{ body {{ padding: 14px; }} }}
</style>
</head>
<body>
<h1>Trading Book</h1>
<p class="subtitle">Live Interactive Brokers portfolio snapshot</p>

<div id="app"></div>

<script id="dashboard-data" type="application/json">{json_payload}</script>
<script src="{CHART_JS_CDN}"></script>
<script>
(function() {{
  var data = JSON.parse(document.getElementById('dashboard-data').textContent);
  var app = document.getElementById('app');

  function el(tag, attrs, children) {{
    var node = document.createElement(tag);
    if (attrs) {{
      Object.keys(attrs).forEach(function(k) {{
        if (k === 'class') node.className = attrs[k];
        else node.setAttribute(k, attrs[k]);
      }});
    }}
    (children || []).forEach(function(child) {{
      if (child == null) return;
      node.appendChild(typeof child === 'string' ? document.createTextNode(child) : child);
    }});
    return node;
  }}

  function fmtUsd(n) {{
    var sign = n < 0 ? '-' : '';
    return sign + '$' + Math.abs(n).toLocaleString(undefined, {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
  }}

  function fmtPct(n) {{
    return (n >= 0 ? '+' : '') + n.toFixed(2) + '%';
  }}

  function pnlClass(n) {{ return n >= 0 ? 'positive' : 'negative'; }}

  if (!data.latest) {{
    app.appendChild(el('div', {{class: 'panel'}}, [
      el('div', {{class: 'empty-state'}}, ['No snapshot yet. Run "python main.py sync" first, then "python main.py render" again.'])
    ]));
    return;
  }}

  var latest = data.latest;

  var hero = el('div', {{class: 'hero'}}, [
    el('div', {{class: 'card'}}, [
      el('div', {{class: 'stat-label'}}, ['Net Liquidation']),
      el('div', {{class: 'stat-value'}}, [fmtUsd(latest.net_liquidation)])
    ]),
    el('div', {{class: 'card'}}, [
      el('div', {{class: 'stat-label'}}, ['Total Cash']),
      el('div', {{class: 'stat-value'}}, [fmtUsd(latest.total_cash)])
    ]),
    el('div', {{class: 'card'}}, [
      el('div', {{class: 'stat-label'}}, ['Unrealized P&L']),
      el('div', {{class: 'stat-value ' + pnlClass(latest.unrealized_pnl)}}, [fmtUsd(latest.unrealized_pnl)])
    ]),
    el('div', {{class: 'card'}}, [
      el('div', {{class: 'stat-label'}}, ['Realized P&L']),
      el('div', {{class: 'stat-value ' + pnlClass(latest.realized_pnl)}}, [fmtUsd(latest.realized_pnl)])
    ]),
    el('div', {{class: 'card'}}, [
      el('div', {{class: 'stat-label'}}, ['Day Change']),
      el('div', {{class: 'stat-value ' + pnlClass(latest.day_change_pct)}}, [fmtPct(latest.day_change_pct)])
    ])
  ]);
  app.appendChild(hero);

  if (data.ai_note) {{
    app.appendChild(el('div', {{class: 'panel'}}, [
      el('h2', null, ['Portfolio Note']),
      el('p', {{class: 'ai-note'}}, [data.ai_note])
    ]));
  }}

  var chartsPanel = el('div', {{class: 'charts'}});
  var trendCard = el('div', {{class: 'panel'}}, [ el('h2', null, ['Net Liquidation Trend']) ]);
  var allocCard = el('div', {{class: 'panel'}}, [ el('h2', null, ['Allocation by Asset Class']) ]);
  chartsPanel.appendChild(trendCard);
  chartsPanel.appendChild(allocCard);
  app.appendChild(chartsPanel);

  var chartJsLoaded = typeof window.Chart !== 'undefined';

  if (chartJsLoaded && data.trend.length > 1) {{
    var trendCanvas = el('canvas', {{'data-testid': 'trend-chart'}});
    trendCard.appendChild(trendCanvas);
    new Chart(trendCanvas.getContext('2d'), {{
      type: 'line',
      data: {{
        labels: data.trend.map(function(t) {{ return t.date; }}),
        datasets: [{{
          label: 'Net Liquidation',
          data: data.trend.map(function(t) {{ return t.net_liquidation; }}),
          borderColor: '#4f8cff', backgroundColor: 'rgba(79,140,255,0.15)', fill: true, tension: 0.25
        }}]
      }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
    }});
  }} else {{
    trendCard.appendChild(buildFallbackTable(
      ['Date', 'Net Liquidation', 'Unrealized P&L'],
      data.trend.map(function(t) {{ return [t.date, fmtUsd(t.net_liquidation), fmtUsd(t.unrealized_pnl)]; }})
    ));
  }}

  var allocationEntries = Object.keys(latest.allocation).map(function(k) {{ return [k, latest.allocation[k]]; }});
  if (chartJsLoaded && allocationEntries.length > 0) {{
    var allocCanvas = el('canvas', {{'data-testid': 'allocation-chart'}});
    allocCard.appendChild(allocCanvas);
    new Chart(allocCanvas.getContext('2d'), {{
      type: 'doughnut',
      data: {{
        labels: allocationEntries.map(function(e) {{ return e[0]; }}),
        datasets: [{{
          data: allocationEntries.map(function(e) {{ return Math.abs(e[1]); }}),
          backgroundColor: ['#4f8cff', '#37c977', '#ffb545', '#ff5c5c', '#a06bff', '#41d6d1']
        }}]
      }},
      options: {{ responsive: true }}
    }});
  }} else {{
    allocCard.appendChild(buildFallbackTable(
      ['Asset Class', 'Market Value'],
      allocationEntries.map(function(e) {{ return [e[0], fmtUsd(e[1])]; }})
    ));
  }}

  function buildFallbackTable(headers, rows) {{
    var table = el('table', {{class: 'fallback-table'}});
    var thead = el('thead', null, [el('tr', null, headers.map(function(h) {{ return el('th', null, [h]); }}))]);
    var tbody = el('tbody', null, rows.map(function(row) {{
      return el('tr', null, row.map(function(cell) {{ return el('td', null, [String(cell)]); }}));
    }}));
    table.appendChild(thead);
    table.appendChild(tbody);
    return table;
  }}

  var positionsPanel = el('div', {{class: 'panel'}}, [
    el('h2', null, ['Positions']),
  ]);
  var searchBox = el('input', {{type: 'search', placeholder: 'Search positions...', 'data-testid': 'position-search'}});
  positionsPanel.appendChild(searchBox);

  var headers = ['Symbol', 'Type', 'Qty', 'Avg Cost', 'Mkt Price', 'Mkt Value', 'Unrealized P&L'];
  var sortKeys = ['symbol', 'sec_type', 'quantity', 'avg_cost', 'market_price', 'market_value', 'unrealized_pnl'];
  var table = el('table', {{'data-testid': 'positions-table'}});
  var thead = el('thead');
  var headRow = el('tr');
  var sortState = {{ key: 'market_value', dir: -1 }};

  headers.forEach(function(label, i) {{
    var th = el('th', null, [label]);
    th.addEventListener('click', function() {{
      var key = sortKeys[i];
      sortState.dir = (sortState.key === key) ? -sortState.dir : -1;
      sortState.key = key;
      renderRows();
    }});
    headRow.appendChild(th);
  }});
  thead.appendChild(headRow);
  table.appendChild(thead);
  var tbody = el('tbody');
  table.appendChild(tbody);
  positionsPanel.appendChild(table);
  app.appendChild(positionsPanel);

  function renderRows() {{
    var query = searchBox.value.trim().toLowerCase();
    var rows = latest.positions.filter(function(p) {{
      return !query || p.symbol.toLowerCase().indexOf(query) !== -1 || p.sec_type.toLowerCase().indexOf(query) !== -1;
    }});
    rows.sort(function(a, b) {{
      var av = a[sortState.key], bv = b[sortState.key];
      if (typeof av === 'string') return av.localeCompare(bv) * sortState.dir;
      return (av - bv) * sortState.dir;
    }});

    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);

    if (rows.length === 0) {{
      tbody.appendChild(el('tr', null, [el('td', {{colspan: '7'}}, ['No positions match.'])]));
      return;
    }}

    rows.forEach(function(p) {{
      tbody.appendChild(el('tr', null, [
        el('td', null, [p.symbol]),
        el('td', null, [p.sec_type]),
        el('td', null, [String(p.quantity)]),
        el('td', null, [fmtUsd(p.avg_cost)]),
        el('td', null, [fmtUsd(p.market_price)]),
        el('td', null, [fmtUsd(p.market_value)]),
        el('td', {{class: pnlClass(p.unrealized_pnl)}}, [fmtUsd(p.unrealized_pnl)])
      ]));
    }});
  }}

  searchBox.addEventListener('input', renderRows);
  renderRows();
}})();
</script>
</body>
</html>
"""
