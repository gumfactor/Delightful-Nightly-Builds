"""Self-contained dark-mode HTML dashboard generation.

All company/anomaly data is delivered to the page as a single JSON blob
inside a <script type="application/json"> tag (with "</" escaped so a
company/ticker string can never prematurely close the tag), then read via
JSON.parse() and rendered exclusively through createElement/textContent --
never innerHTML from data -- so no field (ticker, company name, anomaly
detail, AI narrative) can execute as markup.
"""

from __future__ import annotations

import json
from typing import Any

DATA_PLACEHOLDER = "__EDGAR_LENS_DATA_JSON__"

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EDGAR Lens</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0f1115;
    --panel: #171a21;
    --panel-border: #262b36;
    --text: #e6e9ef;
    --muted: #93a0b4;
    --accent: #5eb3ff;
    --good: #4fd18b;
    --warn: #f2c14e;
    --bad: #f2665e;
    --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
  }
  header {
    padding: 24px 20px 12px;
    border-bottom: 1px solid var(--panel-border);
  }
  header h1 { margin: 0 0 4px; font-size: 1.5rem; }
  header p { margin: 0; color: var(--muted); font-size: 0.9rem; }
  main {
    max-width: 1100px;
    margin: 0 auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }
  section.panel {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 10px;
    padding: 16px;
  }
  section.panel h2 { margin: 0 0 12px; font-size: 1.05rem; }
  .hero-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
  }
  .stat {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--panel-border);
    border-radius: 8px;
    padding: 12px;
  }
  .stat .label { color: var(--muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em; }
  .stat .value { font-size: 1.4rem; font-weight: 600; margin-top: 4px; font-family: var(--mono); }
  table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--panel-border); }
  th { color: var(--muted); font-weight: 500; font-size: 0.75rem; text-transform: uppercase; }
  td.num { font-family: var(--mono); text-align: right; }
  th.num { text-align: right; }
  .pos { color: var(--good); }
  .neg { color: var(--bad); }
  select {
    background: var(--panel);
    color: var(--text);
    border: 1px solid var(--panel-border);
    border-radius: 6px;
    padding: 6px 10px;
    margin-bottom: 12px;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  canvas { max-height: 320px; }
  .anomaly-list { display: flex; flex-direction: column; gap: 10px; }
  .anomaly-item {
    border: 1px solid var(--panel-border);
    border-radius: 8px;
    padding: 10px 12px;
    background: rgba(255,255,255,0.02);
  }
  .anomaly-item .head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 4px;
  }
  .anomaly-item .ticker { font-weight: 600; font-family: var(--mono); }
  .badge {
    display: inline-block;
    font-size: 0.72rem;
    padding: 2px 8px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .badge-revenue_decline, .badge-swing_to_loss { background: rgba(242,102,94,0.18); color: var(--bad); }
  .badge-margin_compression, .badge-leverage_spike { background: rgba(242,193,78,0.18); color: var(--warn); }
  .badge-negative_equity { background: rgba(242,102,94,0.28); color: var(--bad); }
  .narrative { color: var(--muted); font-size: 0.85rem; margin-top: 4px; }
  .empty-state { color: var(--muted); font-size: 0.9rem; padding: 12px 0; }
  footer { text-align: center; color: var(--muted); font-size: 0.78rem; padding: 20px; }
  @media (max-width: 640px) {
    table { display: block; overflow-x: auto; white-space: nowrap; }
  }
</style>
</head>
<body>
<header>
  <h1>EDGAR Lens</h1>
  <p>Multi-year financial statement trends and anomaly flags, sourced from SEC EDGAR XBRL filings.</p>
</header>
<main>
  <section class="panel">
    <h2>Watchlist Overview</h2>
    <div id="hero-stats" class="hero-stats"></div>
  </section>

  <section class="panel">
    <h2>Latest Fiscal Year Comparison</h2>
    <div id="comparison-table-wrap"></div>
  </section>

  <section class="panel">
    <h2>Company Trend</h2>
    <select id="company-select"></select>
    <canvas id="trend-chart"></canvas>
    <div id="trend-fallback"></div>
  </section>

  <section class="panel">
    <h2>Anomalies</h2>
    <div id="anomaly-list" class="anomaly-list"></div>
  </section>
</main>
<footer>Generated by EDGAR Lens. Data source: SEC EDGAR (data.sec.gov). Not investment advice.</footer>

<script type="application/json" id="edgar-lens-data">__EDGAR_LENS_DATA_JSON__</script>
<script>
(function () {
  var DATA = JSON.parse(document.getElementById("edgar-lens-data").textContent);
  var companies = DATA.companies;

  function fmtMoney(v) {
    if (v === null || v === undefined) return "—";
    var abs = Math.abs(v);
    var sign = v < 0 ? "-" : "";
    if (abs >= 1e9) return sign + "$" + (abs / 1e9).toFixed(2) + "B";
    if (abs >= 1e6) return sign + "$" + (abs / 1e6).toFixed(1) + "M";
    return sign + "$" + abs.toFixed(0);
  }
  function fmtPct(v) {
    if (v === null || v === undefined) return "—";
    return (v * 100).toFixed(1) + "%";
  }
  function pctClass(v) {
    if (v === null || v === undefined) return "";
    return v >= 0 ? "pos" : "neg";
  }
  function el(tag, opts) {
    var node = document.createElement(tag);
    opts = opts || {};
    if (opts.text !== undefined) node.textContent = opts.text;
    if (opts.className) node.className = opts.className;
    if (opts.attrs) {
      Object.keys(opts.attrs).forEach(function (k) { node.setAttribute(k, opts.attrs[k]); });
    }
    return node;
  }

  function renderHeroStats() {
    var wrap = document.getElementById("hero-stats");
    var totalCompanies = companies.length;
    var totalAnomalies = companies.reduce(function (sum, c) { return sum + c.anomalies.length; }, 0);
    var totalYears = companies.reduce(function (sum, c) { return sum + c.rows.length; }, 0);
    var stats = [
      ["Companies Tracked", String(totalCompanies)],
      ["Fiscal Years Synced", String(totalYears)],
      ["Anomalies Flagged", String(totalAnomalies)]
    ];
    stats.forEach(function (pair) {
      var stat = el("div", { className: "stat" });
      stat.appendChild(el("div", { className: "label", text: pair[0] }));
      stat.appendChild(el("div", { className: "value", text: pair[1] }));
      wrap.appendChild(stat);
    });
  }

  function latestRow(company) {
    if (!company.rows.length) return null;
    return company.rows[company.rows.length - 1];
  }

  function renderComparisonTable() {
    var wrap = document.getElementById("comparison-table-wrap");
    if (!companies.length) {
      wrap.appendChild(el("div", { className: "empty-state", text: "No companies synced yet. Run: python main.py sync --tickers AAPL,MSFT" }));
      return;
    }
    var table = el("table");
    var thead = el("thead");
    var headRow = el("tr");
    ["Ticker", "Company", "FY", "Revenue", "Rev YoY", "Net Margin", "Debt/Equity", "Flags"].forEach(function (h, i) {
      headRow.appendChild(el("th", { text: h, className: i >= 3 ? "num" : "" }));
    });
    thead.appendChild(headRow);
    table.appendChild(thead);
    var tbody = el("tbody");
    companies.forEach(function (company) {
      var row = latestRow(company);
      if (!row) return;
      var tr = el("tr");
      tr.appendChild(el("td", { text: company.ticker }));
      tr.appendChild(el("td", { text: company.company_name }));
      tr.appendChild(el("td", { text: String(row.fiscal_year) }));
      tr.appendChild(el("td", { text: fmtMoney(row.revenue), className: "num" }));
      tr.appendChild(el("td", { text: fmtPct(row.revenue_yoy), className: "num " + pctClass(row.revenue_yoy) }));
      tr.appendChild(el("td", { text: fmtPct(row.net_margin), className: "num" }));
      tr.appendChild(el("td", { text: row.debt_to_equity === null ? "—" : row.debt_to_equity.toFixed(2) + "x", className: "num" }));
      tr.appendChild(el("td", { text: String(company.anomalies.length), className: "num" }));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
  }

  var chartInstance = null;
  function renderTrendChart(ticker) {
    var company = companies.filter(function (c) { return c.ticker === ticker; })[0];
    var fallback = document.getElementById("trend-fallback");
    fallback.textContent = "";
    if (!company || !company.rows.length) return;

    var labels = company.rows.map(function (r) { return String(r.fiscal_year); });
    var revenue = company.rows.map(function (r) { return r.revenue; });
    var netIncome = company.rows.map(function (r) { return r.net_income; });

    if (typeof Chart === "undefined") {
      var table = el("table");
      var thead = el("thead");
      var headRow = el("tr");
      ["FY", "Revenue", "Net Income"].forEach(function (h) { headRow.appendChild(el("th", { text: h })); });
      thead.appendChild(headRow);
      table.appendChild(thead);
      var tbody = el("tbody");
      company.rows.forEach(function (r) {
        var tr = el("tr");
        tr.appendChild(el("td", { text: String(r.fiscal_year) }));
        tr.appendChild(el("td", { text: fmtMoney(r.revenue), className: "num" }));
        tr.appendChild(el("td", { text: fmtMoney(r.net_income), className: "num" }));
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      fallback.appendChild(el("div", { className: "empty-state", text: "Chart.js unavailable (CDN blocked) -- showing raw data:" }));
      fallback.appendChild(table);
      return;
    }

    var ctx = document.getElementById("trend-chart").getContext("2d");
    if (chartInstance) chartInstance.destroy();
    chartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          { label: "Revenue", data: revenue, borderColor: "#5eb3ff", backgroundColor: "rgba(94,179,255,0.1)", tension: 0.2 },
          { label: "Net Income", data: netIncome, borderColor: "#4fd18b", backgroundColor: "rgba(79,209,139,0.1)", tension: 0.2 }
        ]
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: "#e6e9ef" } } },
        scales: {
          x: { ticks: { color: "#93a0b4" }, grid: { color: "#262b36" } },
          y: { ticks: { color: "#93a0b4" }, grid: { color: "#262b36" } }
        }
      }
    });
  }

  function renderCompanySelect() {
    var select = document.getElementById("company-select");
    companies.forEach(function (company) {
      var opt = el("option", { text: company.ticker + " -- " + company.company_name });
      opt.value = company.ticker;
      select.appendChild(opt);
    });
    select.addEventListener("change", function () { renderTrendChart(select.value); });
    if (companies.length) renderTrendChart(companies[0].ticker);
  }

  function renderAnomalies() {
    var wrap = document.getElementById("anomaly-list");
    var all = [];
    companies.forEach(function (company) {
      company.anomalies.forEach(function (a) {
        all.push({ ticker: company.ticker, anomaly: a, narrative: a.narrative });
      });
    });
    if (!all.length) {
      wrap.appendChild(el("div", { className: "empty-state", text: "No anomalies flagged in the synced data." }));
      return;
    }
    all.sort(function (a, b) { return b.anomaly.fiscal_year - a.anomaly.fiscal_year; });
    all.forEach(function (item) {
      var box = el("div", { className: "anomaly-item" });
      var head = el("div", { className: "head" });
      var left = el("span");
      left.appendChild(el("span", { className: "ticker", text: item.ticker + " " }));
      left.appendChild(el("span", { text: "FY" + item.anomaly.fiscal_year }));
      head.appendChild(left);
      head.appendChild(el("span", { className: "badge badge-" + item.anomaly.type, text: item.anomaly.type.replace(/_/g, " ") }));
      box.appendChild(head);
      box.appendChild(el("div", { text: item.anomaly.detail }));
      if (item.narrative) box.appendChild(el("div", { className: "narrative", text: item.narrative }));
      wrap.appendChild(box);
    });
  }

  renderHeroStats();
  renderComparisonTable();
  renderCompanySelect();
  renderAnomalies();
})();
</script>
</body>
</html>
"""


def _escape_for_script_tag(json_text: str) -> str:
    """Prevent a value like '</script>' inside data from closing the tag early."""
    return json_text.replace("</", "<\\/")


def build_dashboard_html(companies: list[dict[str, Any]]) -> str:
    """companies: list of {ticker, company_name, rows, anomalies} dicts.

    Each anomaly dict may carry an optional "narrative" string (already
    resolved by the caller via ai_narrative, deterministic or AI-derived).
    """
    payload = {"companies": companies}
    json_text = _escape_for_script_tag(json.dumps(payload))
    return _HTML_TEMPLATE.replace(DATA_PLACEHOLDER, json_text)


def render_dashboard(companies: list[dict[str, Any]], out_path: str) -> str:
    html = build_dashboard_html(companies)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html
