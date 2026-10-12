"""Self-contained HTML comparison report."""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone

from .concepts import MULTIPLE_METRICS, PER_SHARE_METRICS, RATIO_METRICS, STATEMENT_GROUPS, label
from .exports import value_of
from .metrics import summarize

CHART_JS = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"
PALETTE = ["#2f7fd1", "#e0802b", "#2fa37a", "#b8559f", "#8a8f1f", "#d1495b", "#5b6ee1", "#7a5c3e"]
CHART_METRICS = ["revenue", "net_income", "free_cash_flow", "gross_margin", "operating_margin",
                 "net_margin", "roe", "debt_to_equity", "revenue_growth", "eps_diluted"]


def fmt(metric: str, value: float | None) -> str:
    if value is None:
        return "–"
    if metric in RATIO_METRICS:
        return f"{value * 100:.1f}%"
    if metric in MULTIPLE_METRICS:
        return f"{value:.2f}×"
    if metric in PER_SHARE_METRICS:
        return f"${value:.2f}"
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    for threshold, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if magnitude >= threshold:
            return f"{sign}${magnitude / threshold:.2f}{suffix}"
    return f"{sign}${magnitude:,.0f}"


def json_for_script(data: object) -> str:
    """JSON safe to embed inside <script>: no '<' so '</script>' cannot appear."""
    return (json.dumps(data).replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def _summary_table(companies: list[dict]) -> str:
    columns = [("revenue", "Revenue"), ("revenue_cagr", "Rev CAGR"), ("net_income", "Net income"),
               ("net_income_cagr", "NI CAGR"), ("gross_margin", "Gross m."),
               ("operating_margin", "Op. m."), ("net_margin", "Net m."), ("free_cash_flow", "FCF"),
               ("roe", "ROE"), ("debt_to_equity", "Debt/Eq")]
    metric_for_fmt = {"revenue_cagr": "revenue_growth", "net_income_cagr": "revenue_growth"}
    head = "".join(f'<th scope="col" data-col="{i + 1}" tabindex="0">{html.escape(t)}</th>'
                   for i, (_, t) in enumerate(columns))
    rows = []
    for company in companies:
        s = summarize(company)
        cells = []
        for key, _ in columns:
            value = s[key]
            sort_value = "" if value is None else repr(float(value))
            cells.append(f'<td data-sort="{sort_value}">{fmt(metric_for_fmt.get(key, key), value)}</td>')
        rows.append(f'<tr><th scope="row" data-sort="{html.escape(s["ticker"])}">'
                    f'<a href="#co-{html.escape(s["ticker"])}">{html.escape(s["ticker"])}</a>'
                    f'<span class="sub">{html.escape(s["name"])} · FY{s["latest_year"]}</span></th>'
                    f'{"".join(cells)}</tr>')
    return (f'<div class="scroll"><table id="summary" data-testid="summary-table"><thead><tr>'
            f'<th scope="col" data-col="0" tabindex="0">Company</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def _statement_table(company: dict) -> str:
    years = company["years"]
    out = []
    for group, metrics in STATEMENT_GROUPS:
        rows = []
        for metric in metrics:
            values = [value_of(company, metric, y) for y in years]
            if all(v is None for v in values):
                continue
            cells = "".join(f"<td>{fmt(metric, v)}</td>" for v in values)
            rows.append(f'<tr><th scope="row">{html.escape(label(metric))}</th>{cells}</tr>')
        if rows:
            out.append(f'<tr class="group"><th colspan="{len(years) + 1}">{html.escape(group)}</th></tr>'
                       + "".join(rows))
    head = "".join(f'<th scope="col">FY{y}</th>' for y in years)
    return (f'<div class="scroll"><table class="stmt"><thead><tr><th scope="col">USD</th>{head}</tr></thead>'
            f'<tbody>{"".join(out)}</tbody></table></div>')


def _chart_data(companies: list[dict]) -> dict:
    years = sorted({y for c in companies for y in c["years"]})
    series: dict[str, dict[str, list[float | None]]] = {}
    for metric in CHART_METRICS:
        series[metric] = {c["ticker"]: [value_of(c, metric, y) for y in years] for c in companies}
    kinds = {m: ("pct" if m in RATIO_METRICS else "x" if m in MULTIPLE_METRICS
                 else "eps" if m in PER_SHARE_METRICS else "usd") for m in CHART_METRICS}
    return {"years": years, "series": series, "labels": {m: label(m) for m in CHART_METRICS},
            "kinds": kinds, "palette": PALETTE}


def render(companies: list[dict], commentary: str | None = None, ai_note: str | None = None,
           demo: bool = False, errors: list[str] | None = None) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    banner = ('<p class="banner" role="note">Demo mode: synthetic data for fictional companies, '
              'not real SEC filings.</p>' if demo else "")
    error_block = ""
    if errors:
        items = "".join(f"<li>{html.escape(e)}</li>" for e in errors)
        error_block = f'<section class="warn" data-testid="errors"><h2>Skipped</h2><ul>{items}</ul></section>'
    ai_block = ""
    if commentary:
        paragraphs = "".join(f"<p>{html.escape(p)}</p>" for p in commentary.split("\n\n") if p.strip())
        ai_block = (f'<section data-testid="ai"><h2>AI commentary</h2>{paragraphs}'
                    f'<p class="sub">Generated from the figures below only. Check against the filings.</p></section>')
    elif ai_note:
        ai_block = f'<section data-testid="ai"><h2>AI commentary</h2><p class="sub">{html.escape(ai_note)}</p></section>'
    details = "".join(
        f'<details id="co-{html.escape(c["ticker"])}" open><summary>{html.escape(c["ticker"])} · '
        f'{html.escape(c["name"])}</summary>{_statement_table(c)}'
        f'<p class="sub">CIK {c["cik"]:010d}</p></details>' for c in companies)
    options = "".join(f'<option value="{m}">{html.escape(label(m))}</option>' for m in CHART_METRICS)
    data = json_for_script(_chart_data(companies))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EDGAR Financials</title>
<style>
:root {{ --bg:#f6f7f9; --card:#fff; --text:#1b1f24; --muted:#5d6670; --line:#dde1e6; --accent:#2f7fd1; --warn:#fff4d6; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#14171b; --card:#1d2227; --text:#e8ebee; --muted:#9aa4ae; --line:#323941; --accent:#6aaef0; --warn:#3a3217; }} }}
:root[data-theme="dark"] {{ --bg:#14171b; --card:#1d2227; --text:#e8ebee; --muted:#9aa4ae; --line:#323941; --accent:#6aaef0; --warn:#3a3217; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif; }}
main {{ max-width:1100px; margin:0 auto; padding:16px; }}
h1 {{ font-size:1.5rem; margin:8px 0 2px; }} h2 {{ font-size:1.1rem; margin:0 0 8px; }}
section, details {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px; margin:14px 0; }}
.sub {{ display:block; color:var(--muted); font-size:.82rem; font-weight:400; }}
.scroll {{ overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; font-variant-numeric:tabular-nums; }}
th, td {{ padding:6px 10px; border-bottom:1px solid var(--line); text-align:right; white-space:nowrap; }}
th[scope=row], thead th:first-child {{ text-align:left; }}
#summary thead th {{ cursor:pointer; user-select:none; }} #summary thead th:hover {{ color:var(--accent); }}
tr.group th {{ text-align:left; background:var(--bg); color:var(--muted); font-size:.8rem; text-transform:uppercase; letter-spacing:.04em; }}
summary {{ cursor:pointer; font-weight:600; }}
a {{ color:var(--accent); }}
.banner {{ background:var(--warn); padding:8px 12px; border-radius:8px; }}
.warn {{ background:var(--warn); }}
.chart-wrap {{ position:relative; height:320px; }}
select {{ font:inherit; padding:4px 8px; background:var(--card); color:var(--text); border:1px solid var(--line); border-radius:6px; }}
</style>
</head>
<body>
<main>
<h1>EDGAR Financials</h1>
<p class="sub">{len(companies)} companies · annual filings from SEC XBRL · generated {generated}</p>
{banner}{error_block}{ai_block}
<section>
<h2>Compare</h2>
<label for="metric">Metric </label><select id="metric" data-testid="metric-select">{options}</select>
<div class="chart-wrap"><canvas id="chart" role="img" aria-label="Comparison chart of the selected metric across companies"></canvas></div>
</section>
<section><h2>Summary (latest fiscal year, CAGR over the window)</h2>{_summary_table(companies)}</section>
{details}
</main>
<script src="{CHART_JS}"></script>
<script>
const DATA = {data};
function fmtValue(kind, v) {{
  if (v === null || v === undefined) return "–";
  if (kind === "pct") return (v * 100).toFixed(1) + "%";
  if (kind === "x") return v.toFixed(2) + "×";
  if (kind === "eps") return "$" + v.toFixed(2);
  const a = Math.abs(v), s = v < 0 ? "-" : "";
  if (a >= 1e12) return s + "$" + (a / 1e12).toFixed(2) + "T";
  if (a >= 1e9) return s + "$" + (a / 1e9).toFixed(2) + "B";
  if (a >= 1e6) return s + "$" + (a / 1e6).toFixed(2) + "M";
  return s + "$" + a.toFixed(0);
}}
let chart = null;
function draw(metric) {{
  const kind = DATA.kinds[metric];
  const css = getComputedStyle(document.documentElement);
  const text = css.getPropertyValue("--muted").trim(), grid = css.getPropertyValue("--line").trim();
  const datasets = Object.keys(DATA.series[metric]).map((ticker, i) => ({{
    label: ticker, data: DATA.series[metric][ticker], spanGaps: false, tension: 0.2,
    borderColor: DATA.palette[i % DATA.palette.length], backgroundColor: DATA.palette[i % DATA.palette.length],
  }}));
  if (chart) chart.destroy();
  if (typeof Chart === "undefined") return;
  chart = new Chart(document.getElementById("chart"), {{
    type: "line", data: {{ labels: DATA.years.map(y => "FY" + y), datasets }},
    options: {{ responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ labels: {{ color: text }} }},
        tooltip: {{ callbacks: {{ label: c => c.dataset.label + ": " + fmtValue(kind, c.parsed.y) }} }} }},
      scales: {{ x: {{ ticks: {{ color: text }}, grid: {{ color: grid }} }},
        y: {{ ticks: {{ color: text, callback: v => fmtValue(kind, v) }}, grid: {{ color: grid }} }} }} }},
  }});
}}
const select = document.getElementById("metric");
select.addEventListener("change", () => draw(select.value));
draw(select.value);

const table = document.getElementById("summary");
let sortState = {{ col: -1, asc: true }};
function sortBy(col) {{
  const body = table.tBodies[0];
  const rows = Array.from(body.rows);
  sortState.asc = sortState.col === col ? !sortState.asc : col === 0;
  sortState.col = col;
  const key = r => {{ const c = r.cells[col]; const raw = c.dataset.sort;
    return col === 0 ? raw : (raw === "" ? null : parseFloat(raw)); }};
  rows.sort((a, b) => {{ const x = key(a), y = key(b);
    if (x === null && y === null) return 0; if (x === null) return 1; if (y === null) return -1;
    const d = x < y ? -1 : x > y ? 1 : 0; return sortState.asc ? d : -d; }});
  rows.forEach(r => body.appendChild(r));
}}
table.tHead.addEventListener("click", e => {{ const th = e.target.closest("th"); if (th) sortBy(Number(th.dataset.col)); }});
table.tHead.addEventListener("keydown", e => {{ if (e.key === "Enter") {{ const th = e.target.closest("th"); if (th) sortBy(Number(th.dataset.col)); }} }});
</script>
</body>
</html>
"""
