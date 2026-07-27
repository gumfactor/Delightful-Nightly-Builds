"""Self-contained dark-mode HTML dashboard renderer for SiliconWatch.

All ticker/name/subsector strings originate from a potentially user-supplied
--config JSON file, so every one is HTML-escaped before insertion. Chart.js is
loaded from a pinned CDN version with a plain-table fallback if it fails to load.
"""
import html
import json
from typing import Dict, List, Optional, Tuple

CHARTJS_VERSION = "4.4.4"
CHARTJS_URL = f"https://cdn.jsdelivr.net/npm/chart.js@{CHARTJS_VERSION}/dist/chart.umd.min.js"

SUBSECTOR_COLORS = {
    "GPU / AI Accelerators": "#7c9cff",
    "Custom Silicon / Networking": "#5fd0c0",
    "Foundry / IDM": "#f2a65a",
    "Equipment / EDA": "#e07bc0",
    "Memory": "#c9d15a",
    "IP / Architecture & Analog": "#9d8cf1",
}
DEFAULT_COLOR = "#9aa4b2"


def _color_for(subsector: str) -> str:
    return SUBSECTOR_COLORS.get(subsector, DEFAULT_COLOR)


def _fmt_money(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value >= 1e12:
        return f"${value / 1e12:.2f}T"
    if value >= 1e9:
        return f"${value / 1e9:.1f}B"
    if value >= 1e6:
        return f"${value / 1e6:.1f}M"
    return f"${value:,.2f}"


def _fmt_num(value: Optional[float], suffix: str = "", digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}{suffix}"


def _fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "—"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}%"


def _json_for_script(data) -> str:
    """json.dumps but safe to embed inside a <script> tag (no </script> breakout)."""
    return json.dumps(data, default=str).replace("</", "<\\/")


def render_dashboard(
    enriched_snapshots: List[Dict],
    price_history_by_ticker: Dict[str, List[Tuple[str, float]]],
    sector_pe_trend: List[Tuple[str, Optional[float]]],
    aggregates: Dict,
    narrative: str,
    narrative_source: str,
    generated_at: str,
) -> str:
    subsectors = sorted({s["subsector"] for s in enriched_snapshots})
    filter_chips = "".join(
        f'<button class="chip" data-subsector="{html.escape(sub)}">{html.escape(sub)}</button>'
        for sub in subsectors
    )

    table_rows = []
    for s in enriched_snapshots:
        table_rows.append(
            "<tr data-subsector=\"{sub}\">"
            "<td>{ticker}</td><td>{name}</td><td>{sub_label}</td>"
            "<td>{price}</td><td class=\"{d1cls}\">{d1}</td><td class=\"{d1ycls}\">{d1y}</td>"
            "<td>{pe}</td><td>{peg}</td><td>{upside}</td></tr>".format(
                sub=html.escape(s["subsector"]),
                ticker=html.escape(s["ticker"]),
                name=html.escape(s["name"]),
                sub_label=html.escape(s["subsector"]),
                price=_fmt_num(s.get("price"), digits=2),
                d1cls="pos" if (s.get("since_prev_pct") or 0) >= 0 else "neg",
                d1=_fmt_pct(s.get("since_prev_pct")),
                d1ycls="pos" if (s.get("since_1y_pct") or 0) >= 0 else "neg",
                d1y=_fmt_pct(s.get("since_1y_pct")) if s.get("since_1y_reliable") else "—",
                pe=_fmt_num(s.get("pe_trailing"), digits=1),
                peg=_fmt_num(s.get("peg_ratio"), digits=2),
                upside=_fmt_pct(
                    ((s["target_mean_price"] - s["price"]) / s["price"] * 100)
                    if s.get("target_mean_price") and s.get("price")
                    else None
                ),
            )
        )

    market_cap_fallback_rows = "".join(
        f"<tr><td>{html.escape(s['ticker'])}</td><td>{_fmt_money(s.get('market_cap'))}</td></tr>"
        for s in enriched_snapshots
    )
    margin_fallback_rows = "".join(
        f"<tr><td>{html.escape(s['ticker'])}</td>"
        f"<td>{_fmt_pct(s['profit_margin'] * 100) if s.get('profit_margin') is not None else '—'}</td></tr>"
        for s in enriched_snapshots
    )

    ticker_options = "".join(
        f'<option value="{html.escape(s["ticker"])}">{html.escape(s["ticker"])} — {html.escape(s["name"])}</option>'
        for s in enriched_snapshots
    )

    pe_trend_note = (
        ""
        if len(sector_pe_trend) >= 2
        else '<p class="muted">Sector P/E trend appears after a second `sync` on a different day.</p>'
    )

    kpi_cards = f"""
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-label">Total Market Cap</div><div class="kpi-value">{_fmt_money(aggregates.get('total_market_cap'))}</div></div>
      <div class="kpi-card"><div class="kpi-label">Avg Trailing P/E</div><div class="kpi-value">{_fmt_num(aggregates.get('avg_pe_trailing'), digits=1)}</div></div>
      <div class="kpi-card"><div class="kpi-label">Avg Profit Margin</div><div class="kpi-value">{_fmt_pct(aggregates['avg_profit_margin'] * 100) if aggregates.get('avg_profit_margin') is not None else '—'}</div></div>
      <div class="kpi-card"><div class="kpi-label">Companies Tracked</div><div class="kpi-value">{aggregates.get('companies_tracked', 0)}</div></div>
    </div>
    """

    data_blob = {
        "snapshots": enriched_snapshots,
        "priceHistory": price_history_by_ticker,
        "sectorPeTrend": sector_pe_trend,
    }

    html_doc = _TEMPLATE
    html_doc = html_doc.replace("__CHARTJS_URL__", CHARTJS_URL)
    html_doc = html_doc.replace("__GENERATED_AT__", html.escape(generated_at))
    html_doc = html_doc.replace("__FILTER_CHIPS__", filter_chips)
    html_doc = html_doc.replace("__KPI_CARDS__", kpi_cards)
    html_doc = html_doc.replace("__TABLE_ROWS__", "".join(table_rows))
    html_doc = html_doc.replace("__MARKET_CAP_FALLBACK_ROWS__", market_cap_fallback_rows)
    html_doc = html_doc.replace("__MARGIN_FALLBACK_ROWS__", margin_fallback_rows)
    html_doc = html_doc.replace("__TICKER_OPTIONS__", ticker_options)
    html_doc = html_doc.replace("__PE_TREND_NOTE__", pe_trend_note)
    html_doc = html_doc.replace(
        "__NARRATIVE_LABEL__",
        "AI-generated sector narrative (Claude Haiku)" if narrative_source == "ai" else "Deterministic sector summary",
    )
    html_doc = html_doc.replace("__NARRATIVE_TEXT__", html.escape(narrative))
    html_doc = html_doc.replace("__DATA_JSON__", _json_for_script(data_blob))
    html_doc = html_doc.replace(
        "__SUBSECTOR_COLORS_JSON__", _json_for_script(SUBSECTOR_COLORS)
    )
    return html_doc


_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SiliconWatch — AI Infrastructure &amp; Semiconductor Sector Dashboard</title>
<style>
  :root {
    --bg: #0b0e14; --panel: #141924; --border: #262d3d; --text: #e8ecf4;
    --muted: #8b93a7; --accent: #7c9cff; --pos: #5fd0a0; --neg: #f2748c;
  }
  @media (prefers-color-scheme: light) {
    :root { --bg: #f5f6fa; --panel: #ffffff; --border: #dde1ea; --text: #1a1f2b; --muted: #626a7d; }
  }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: var(--bg); color: var(--text); padding: 1.5rem; }
  h1 { font-size: 1.4rem; margin: 0 0 0.25rem; }
  .subtitle { color: var(--muted); font-size: 0.9rem; margin-bottom: 1.25rem; }
  .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; margin-bottom: 1.5rem; }
  .kpi-card { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; }
  .kpi-label { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }
  .kpi-value { font-size: 1.5rem; font-weight: 600; margin-top: 0.25rem; }
  .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; margin-bottom: 1.5rem; }
  .panel h2 { margin-top: 0; font-size: 1.05rem; }
  .charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  @media (max-width: 720px) { .charts-row { grid-template-columns: 1fr; } }
  .chip-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.75rem; }
  .chip { background: transparent; border: 1px solid var(--border); color: var(--text); border-radius: 999px;
          padding: 0.3rem 0.8rem; font-size: 0.8rem; cursor: pointer; }
  .chip.active { background: var(--accent); border-color: var(--accent); color: #fff; }
  input[type="search"] { width: 100%; padding: 0.5rem 0.75rem; margin-bottom: 0.75rem; border-radius: 8px;
         border: 1px solid var(--border); background: var(--bg); color: var(--text); }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th, td { text-align: left; padding: 0.5rem 0.6rem; border-bottom: 1px solid var(--border); }
  th { cursor: pointer; color: var(--muted); user-select: none; white-space: nowrap; }
  .pos { color: var(--pos); }
  .neg { color: var(--neg); }
  .muted { color: var(--muted); font-size: 0.85rem; }
  select { padding: 0.4rem 0.6rem; border-radius: 8px; border: 1px solid var(--border); background: var(--bg); color: var(--text); margin-bottom: 0.75rem; }
  .fallback-table { display: none; }
  footer { color: var(--muted); font-size: 0.78rem; margin-top: 1.5rem; }
  .table-scroll { overflow-x: auto; }
</style>
</head>
<body>
<h1>SiliconWatch</h1>
<div class="subtitle">AI infrastructure &amp; semiconductor sector dashboard — generated __GENERATED_AT__</div>

__KPI_CARDS__

<div class="panel">
  <h2>__NARRATIVE_LABEL__</h2>
  <p>__NARRATIVE_TEXT__</p>
</div>

<div class="panel">
  <h2>Sector Comparison</h2>
  <div class="charts-row">
    <div>
      <canvas id="marketCapChart" height="220"></canvas>
      <table class="fallback-table" id="marketCapFallback"><thead><tr><th>Ticker</th><th>Market Cap</th></tr></thead>
        <tbody>__MARKET_CAP_FALLBACK_ROWS__</tbody></table>
    </div>
    <div>
      <canvas id="marginChart" height="220"></canvas>
      <table class="fallback-table" id="marginFallback"><thead><tr><th>Ticker</th><th>Profit Margin</th></tr></thead>
        <tbody>__MARGIN_FALLBACK_ROWS__</tbody></table>
    </div>
  </div>
</div>

<div class="panel">
  <h2>Companies</h2>
  <div class="chip-row">__FILTER_CHIPS__</div>
  <input type="search" id="searchBox" placeholder="Search ticker or name…">
  <div class="table-scroll">
  <table id="companyTable">
    <thead><tr>
      <th data-key="ticker">Ticker</th><th data-key="name">Name</th><th data-key="sub_label">Sub-sector</th>
      <th data-key="price">Price</th><th data-key="d1">1D %</th><th data-key="d1y">1Y %</th>
      <th data-key="pe">P/E</th><th data-key="peg">PEG</th><th data-key="upside">Analyst Upside</th>
    </tr></thead>
    <tbody>__TABLE_ROWS__</tbody>
  </table>
  </div>
</div>

<div class="panel">
  <h2>Price History</h2>
  <select id="tickerSelect">__TICKER_OPTIONS__</select>
  <canvas id="priceChart" height="180"></canvas>
  <table class="fallback-table" id="priceFallback"><thead><tr><th>Date</th><th>Close</th></tr></thead><tbody></tbody></table>
</div>

<div class="panel">
  <h2>Sector P/E Over Time</h2>
  __PE_TREND_NOTE__
  <canvas id="peTrendChart" height="160"></canvas>
  <table class="fallback-table" id="peTrendFallback"><thead><tr><th>Sync Date</th><th>Avg P/E</th></tr></thead><tbody></tbody></table>
</div>

<footer>
  Data: Yahoo Finance via yfinance. Not investment advice — for personal research reference only.
</footer>

<script id="sw-data" type="application/json">__DATA_JSON__</script>
<script id="sw-colors" type="application/json">__SUBSECTOR_COLORS_JSON__</script>
<script src="__CHARTJS_URL__"></script>
<script>
(function () {
  var DATA = JSON.parse(document.getElementById('sw-data').textContent);
  var COLORS = JSON.parse(document.getElementById('sw-colors').textContent);
  var DEFAULT_COLOR = '#9aa4b2';

  function colorFor(sub) { return COLORS[sub] || DEFAULT_COLOR; }
  function chartsAvailable() { return typeof window.Chart !== 'undefined'; }

  function showFallback(id) {
    var el = document.getElementById(id);
    if (el) el.style.display = 'table';
    var canvas = el ? el.previousElementSibling : null;
    if (canvas && canvas.tagName === 'CANVAS') canvas.style.display = 'none';
  }

  function renderMarketCapChart() {
    if (!chartsAvailable()) { showFallback('marketCapFallback'); return; }
    var labels = DATA.snapshots.map(function (s) { return s.ticker; });
    var values = DATA.snapshots.map(function (s) { return s.market_cap || 0; });
    var colors = DATA.snapshots.map(function (s) { return colorFor(s.subsector); });
    new Chart(document.getElementById('marketCapChart'), {
      type: 'bar',
      data: { labels: labels, datasets: [{ label: 'Market Cap (USD)', data: values, backgroundColor: colors }] },
      options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
  }

  function renderMarginChart() {
    if (!chartsAvailable()) { showFallback('marginFallback'); return; }
    var labels = DATA.snapshots.map(function (s) { return s.ticker; });
    var values = DATA.snapshots.map(function (s) { return s.profit_margin != null ? s.profit_margin * 100 : 0; });
    var colors = DATA.snapshots.map(function (s) { return colorFor(s.subsector); });
    new Chart(document.getElementById('marginChart'), {
      type: 'bar',
      data: { labels: labels, datasets: [{ label: 'Profit Margin %', data: values, backgroundColor: colors }] },
      options: { plugins: { legend: { display: false } } }
    });
  }

  var priceChartInstance = null;
  function renderPriceChart(ticker) {
    var series = DATA.priceHistory[ticker] || [];
    if (!chartsAvailable()) {
      var tbody = document.querySelector('#priceFallback tbody');
      tbody.innerHTML = '';
      series.forEach(function (row) {
        var tr = document.createElement('tr');
        var d = document.createElement('td'); d.textContent = row[0];
        var c = document.createElement('td'); c.textContent = row[1];
        tr.appendChild(d); tr.appendChild(c); tbody.appendChild(tr);
      });
      showFallback('priceFallback');
      return;
    }
    var labels = series.map(function (r) { return r[0]; });
    var values = series.map(function (r) { return r[1]; });
    if (priceChartInstance) priceChartInstance.destroy();
    priceChartInstance = new Chart(document.getElementById('priceChart'), {
      type: 'line',
      data: { labels: labels, datasets: [{ label: ticker, data: values, borderColor: '#7c9cff', pointRadius: 0 }] },
      options: { plugins: { legend: { display: false } }, scales: { x: { display: false } } }
    });
  }

  function renderPeTrendChart() {
    var trend = DATA.sectorPeTrend || [];
    if (trend.length < 2) return;
    if (!chartsAvailable()) {
      var tbody = document.querySelector('#peTrendFallback tbody');
      tbody.innerHTML = '';
      trend.forEach(function (row) {
        var tr = document.createElement('tr');
        var d = document.createElement('td'); d.textContent = row[0];
        var v = document.createElement('td'); v.textContent = row[1] != null ? row[1].toFixed(1) : '—';
        tr.appendChild(d); tr.appendChild(v); tbody.appendChild(tr);
      });
      showFallback('peTrendFallback');
      return;
    }
    new Chart(document.getElementById('peTrendChart'), {
      type: 'line',
      data: {
        labels: trend.map(function (r) { return r[0]; }),
        datasets: [{ label: 'Avg Trailing P/E', data: trend.map(function (r) { return r[1]; }), borderColor: '#f2a65a', pointRadius: 3 }]
      },
      options: { plugins: { legend: { display: false } } }
    });
  }

  function setupTickerSelect() {
    var select = document.getElementById('tickerSelect');
    select.addEventListener('change', function () { renderPriceChart(select.value); });
    if (select.options.length > 0) renderPriceChart(select.value);
  }

  function setupFilterChips() {
    var chips = document.querySelectorAll('.chip');
    var rows = document.querySelectorAll('#companyTable tbody tr');
    var active = null;
    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        var sub = chip.getAttribute('data-subsector');
        if (active === sub) {
          active = null;
          chip.classList.remove('active');
        } else {
          chips.forEach(function (c) { c.classList.remove('active'); });
          chip.classList.add('active');
          active = sub;
        }
        rows.forEach(function (row) {
          row.style.display = (!active || row.getAttribute('data-subsector') === active) ? '' : 'none';
        });
      });
    });
  }

  function setupSearch() {
    var box = document.getElementById('searchBox');
    var rows = document.querySelectorAll('#companyTable tbody tr');
    box.addEventListener('input', function () {
      var q = box.value.trim().toLowerCase();
      rows.forEach(function (row) {
        row.style.display = row.textContent.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
      });
    });
  }

  function setupSort() {
    var headers = document.querySelectorAll('#companyTable th');
    var tbody = document.querySelector('#companyTable tbody');
    var dir = {};
    headers.forEach(function (th, colIndex) {
      th.addEventListener('click', function () {
        var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
        dir[colIndex] = !dir[colIndex];
        rows.sort(function (a, b) {
          var av = a.children[colIndex].textContent.trim();
          var bv = b.children[colIndex].textContent.trim();
          var an = parseFloat(av.replace(/[^0-9.-]/g, ''));
          var bn = parseFloat(bv.replace(/[^0-9.-]/g, ''));
          var cmp = (!isNaN(an) && !isNaN(bn)) ? (an - bn) : av.localeCompare(bv);
          return dir[colIndex] ? cmp : -cmp;
        });
        rows.forEach(function (row) { tbody.appendChild(row); });
      });
    });
  }

  renderMarketCapChart();
  renderMarginChart();
  renderPeTrendChart();
  setupTickerSelect();
  setupFilterChips();
  setupSearch();
  setupSort();
})();
</script>
</body>
</html>
"""
