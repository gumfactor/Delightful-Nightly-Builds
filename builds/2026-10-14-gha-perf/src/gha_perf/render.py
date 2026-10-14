"""Render the analysis dict as a single self-contained HTML page (Chart.js from pinned CDN)."""
from __future__ import annotations

import json
from html import escape

CHART_JS = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--text:#1b1f24;--muted:#5b6672;--line:#dde1e6;--accent:#2f6fed;--high:#c62828;--medium:#b26a00;--ok:#2e7d32}
@media (prefers-color-scheme:dark){:root{--bg:#0f1318;--card:#171c23;--text:#e6e9ee;--muted:#9aa5b1;--line:#2a323c;--accent:#6ea0ff;--high:#ff6b6b;--medium:#ffb454;--ok:#6fcf7c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}h1{font-size:1.4rem;margin:.2rem 0}h2{font-size:1.1rem;margin:1.6rem 0 .6rem}
.muted{color:var(--muted);font-size:.85rem}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}.card b{display:block;font-size:1.5rem}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.88rem}th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}
th{cursor:pointer;color:var(--muted)}td.num,th.num{text-align:right}.sev-high{color:var(--high);font-weight:600}.sev-medium{color:var(--medium);font-weight:600}
.finding{padding:8px 0;border-bottom:1px solid var(--line)}.finding:last-child{border:0}.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px}
.ai{white-space:pre-wrap;border-left:3px solid var(--accent);padding-left:10px}.err{color:var(--high)}
canvas{max-height:260px}
"""

JS = """
document.querySelectorAll('table.sortable').forEach(function(table){
  table.querySelectorAll('th').forEach(function(th, index){
    th.addEventListener('click', function(){
      var body = table.tBodies[0], dir = th.dataset.dir === 'asc' ? -1 : 1;
      th.dataset.dir = dir === 1 ? 'asc' : 'desc';
      Array.from(body.rows).sort(function(a, b){
        var x = a.cells[index].dataset.v, y = b.cells[index].dataset.v;
        var nx = parseFloat(x), ny = parseFloat(y);
        return (isNaN(nx) || isNaN(ny) ? x.localeCompare(y) : nx - ny) * dir;
      }).forEach(function(row){ body.appendChild(row); });
    });
  });
});
var data = JSON.parse(document.getElementById('report-data').textContent);
if (window.Chart) {
  var t = data.trend, ink = getComputedStyle(document.body).color;
  Chart.defaults.color = ink;
  new Chart(document.getElementById('trendMinutes'), {type:'bar', data:{labels:t.map(function(w){return w.week_start}),
    datasets:[{label:'Billable min (est.)', data:t.map(function(w){return w.minutes}), backgroundColor:'#2f6fed'}]}});
  new Chart(document.getElementById('trendFail'), {type:'line', data:{labels:t.map(function(w){return w.week_start}),
    datasets:[{label:'Failure rate %', data:t.map(function(w){return Math.round(w.fail_rate*100)}), borderColor:'#c62828', tension:.3}]}});
  var repos = data.repos.slice(0, 10);
  new Chart(document.getElementById('repoMinutes'), {type:'bar', data:{labels:repos.map(function(r){return r.repo}),
    datasets:[{label:'Useful min', data:repos.map(function(r){return Math.round(r.billable_min - r.wasted_min)}), backgroundColor:'#2e7d32'},
              {label:'Wasted min', data:repos.map(function(r){return Math.round(r.wasted_min)}), backgroundColor:'#c62828'}]},
    options:{indexAxis:'y', scales:{x:{stacked:true}, y:{stacked:true}}}});
}
"""


def _fmt_dur(seconds: float) -> str:
    return f"{int(seconds // 60)}m{int(seconds % 60):02d}s" if seconds >= 60 else f"{seconds:.0f}s"


def _cell(value: object, text: str | None = None, numeric: bool = False) -> str:
    shown = escape(str(value) if text is None else text)
    return f'<td class="{"num" if numeric else ""}" data-v="{escape(str(value))}">{shown}</td>'


def _table(headers: list[tuple[str, bool]], rows: list[list[str]], empty: str) -> str:
    if not rows:
        return f'<p class="muted">{escape(empty)}</p>'
    head = "".join(f'<th class="{"num" if num else ""}">{escape(name)}</th>' for name, num in headers)
    body = "".join(f"<tr>{''.join(row)}</tr>" for row in rows)
    return f'<div class="panel"><table class="sortable"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def render_html(report: dict, ai_summary: str | None = None) -> str:
    summary = report["summary"]
    cards = [
        ("Runs analysed", f"{summary['runs']}"), ("Repos / workflows", f"{summary['repos']} / {summary['workflows']}"),
        ("Billable min (est.)", f"{summary['billable_min']:.0f}"),
        ("Wasted min", f"{summary['wasted_min']:.0f} ({summary['wasted_pct']:.0%})"),
        ("Failure rate", f"{summary['fail_rate']:.0%}"),
    ]
    cards_html = "".join(f'<div class="card"><span class="muted">{escape(k)}</span><b>{escape(v)}</b></div>' for k, v in cards)

    findings_html = "".join(
        f'<div class="finding"><span class="sev-{escape(f["severity"])}">{escape(f["severity"].upper())}</span> '
        f'<b>{escape(f["repo"])}</b> / {escape(f["workflow"])}: {escape(f["title"])}<br>'
        f'<span class="muted">{escape(f["advice"])}</span></div>'
        for f in report["findings"]
    ) or '<p class="muted">No issues crossed the thresholds.</p>'

    workflow_rows = [[
        _cell(w["repo"]), _cell(w["workflow"]), _cell(w["runs"], numeric=True),
        _cell(w["fail_rate"], f"{w['fail_rate']:.0%}", True), _cell(w["cancel_rate"], f"{w['cancel_rate']:.0%}", True),
        _cell(w["p50_s"], _fmt_dur(w["p50_s"]), True), _cell(w["p95_s"], _fmt_dur(w["p95_s"]), True),
        _cell(w["billable_min"], f"{w['billable_min']:.0f}", True), _cell(w["wasted_min"], f"{w['wasted_min']:.0f}", True),
        _cell(w["flaky_incidents"], numeric=True),
    ] for w in report["workflows"]]
    step_rows = [[
        _cell(s["repo"]), _cell(s["workflow"]), _cell(s["job"]), _cell(s["step"]), _cell(s["count"], numeric=True),
        _cell(s["mean_s"], _fmt_dur(s["mean_s"]), True), _cell(s["max_s"], _fmt_dur(s["max_s"]), True),
        _cell(s["total_s"], f"{s['total_s'] / 60:.1f} min", True),
    ] for s in report["steps"]]

    errors = summary["errors"]
    errors_html = "".join(f'<li class="err">{escape(repo)}: {escape(msg)}</li>' for repo, msg in errors.items())
    ai_html = f'<h2>AI briefing</h2><div class="panel ai">{escape(ai_summary)}</div>' if ai_summary else ""
    data_json = json.dumps({"trend": report["trend"], "repos": report["repos"]}).replace("</", "<\\/")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>gha-perf report</title><style>{CSS}</style></head><body><main>
<h1>GitHub Actions performance</h1>
<p class="muted">Last {summary['days']} days. Generated {escape(report['generated'])}. Billable minutes are estimates: exact for runs with job detail, workflow average otherwise.</p>
<div class="cards">{cards_html}</div>
{'<h2>Collection problems</h2><ul>' + errors_html + '</ul>' if errors else ''}
{ai_html}
<h2>Findings</h2><div class="panel">{findings_html}</div>
<h2>Trends</h2><div class="charts"><div class="panel"><canvas id="trendMinutes"></canvas></div>
<div class="panel"><canvas id="trendFail"></canvas></div><div class="panel"><canvas id="repoMinutes"></canvas></div></div>
<h2>Workflows</h2>{_table([("Repo", False), ("Workflow", False), ("Runs", True), ("Fail", True), ("Cancel", True), ("p50", True), ("p95", True), ("Bill min", True), ("Wasted min", True), ("Flaky", True)], workflow_rows, "No workflow runs in this window.")}
<h2>Slowest steps (by total time)</h2>{_table([("Repo", False), ("Workflow", False), ("Job", False), ("Step", False), ("Runs", True), ("Mean", True), ("Max", True), ("Total", True)], step_rows, "No job detail was fetched.")}
</main>
<script id="report-data" type="application/json">{data_json}</script>
<script src="{CHART_JS}"></script>
<script>{JS}</script></body></html>
"""
