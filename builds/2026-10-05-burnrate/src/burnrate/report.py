"""Render analysis results as text, JSON and a self-contained HTML dashboard."""
from __future__ import annotations

import json

CHART_JS = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


def _tokens(value: int) -> str:
    return f"{value / 1_000_000:.2f}M" if value >= 1_000_000 else f"{value / 1000:.1f}k" if value >= 1000 else str(value)


def text_summary(result: dict) -> str:
    t = result["totals"]
    lines = [
        f"Burnrate — {t['sessions']} sessions, {t['turns']} turns, est. ${t['cost']:.2f}",
        f"Tokens: in {_tokens(t['input'])}  out {_tokens(t['output'])}  cache-write {_tokens(t['cache_write'])}  cache-read {_tokens(t['cache_read'])}",
        f"Cache hit {t['cache_hit']:.0%}, saved ~${t['saved_by_cache']:.2f}; subagent share {t['sidechain_share']:.0%}; active {t['active_min']:.0f} min",
        "",
        "Top projects:",
    ]
    lines += [f"  {r['project'][:30]:<30} ${r['cost']:>8.2f}  {r['turns']} turns" for r in result["by_project"][:5]] or ["  (none)"]
    lines += ["", "By model:"]
    lines += [f"  {r['model'][:30]:<30} ${r['cost']:>8.2f}" for r in result["by_model"]] or ["  (none)"]
    lines += ["", f"Findings ({len(result['findings'])}):"]
    lines += [f"  [{f['severity']}] {f['kind']}: {f['message']}" for f in result["findings"][:15]] or ["  none"]
    if result["unpriced_models"]:
        lines.append(f"\nUnpriced models excluded from cost: {', '.join(result['unpriced_models'])}")
    lines.append("Costs are estimates from pricing.json, not invoices.")
    return "\n".join(lines)


def to_json(result: dict) -> str:
    return json.dumps(result, indent=2, default=str)


def embed_json(result: dict) -> str:
    """JSON safe to place inside a <script> element."""
    return json.dumps(result, default=str).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def html_report(result: dict) -> str:
    return _TEMPLATE.replace("__CHART_JS__", CHART_JS).replace("__DATA__", embed_json(result))


_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Burnrate</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--fg:#1c2230;--mut:#667085;--line:#e2e5ea;--acc:#2f6fed;--warn:#b54708;--high:#c01048;--info:#475467}
@media (prefers-color-scheme:dark){:root{--bg:#10131a;--card:#181c26;--fg:#e6e9f0;--mut:#98a2b3;--line:#2a3040;--acc:#6b9bff;--warn:#f79009;--high:#f63d68;--info:#98a2b3}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;padding:16px;max-width:1100px;margin-inline:auto}
h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:0 0 10px}.sub{color:var(--mut);margin-bottom:16px;font-size:13px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:14px}
.tile,.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}.card{margin-bottom:14px}
.tile b{display:block;font-size:22px}.tile span{color:var(--mut);font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.chart{position:relative;height:240px}
.find{border-left:4px solid var(--info);padding:6px 10px;margin:6px 0;background:var(--bg);border-radius:4px}
.find.warn{border-color:var(--warn)}.find.high{border-color:var(--high)}.find small{color:var(--mut);display:block}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
th{cursor:pointer;color:var(--mut)}td.n,th.n{text-align:right}
</style></head><body>
<h1>Burnrate</h1><div class="sub" id="sub"></div>
<div class="tiles" id="tiles"></div>
<div class="card"><h2>Findings</h2><div id="findings" data-testid="findings"></div></div>
<div class="grid">
<div class="card"><h2>Estimated cost per day (USD)</h2><div class="chart"><canvas id="dayChart"></canvas></div></div>
<div class="card"><h2>Cost by model</h2><div class="chart"><canvas id="modelChart"></canvas></div></div>
</div>
<div class="grid">
<div class="card"><h2>Projects</h2><div class="scroll"><table id="projects"></table></div></div>
<div class="card"><h2>Tools</h2><div class="scroll"><table id="tools"></table></div></div>
</div>
<div class="card"><h2>Sessions (click a header to sort)</h2><div class="scroll"><table id="sessions" data-testid="sessions"></table></div></div>
<script id="data" type="application/json">__DATA__</script>
<script src="__CHART_JS__"></script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const el = (tag, text, cls) => { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; if (cls) e.className = cls; return e; };
const usd = v => '$' + v.toFixed(2);
const tok = v => v >= 1e6 ? (v/1e6).toFixed(2)+'M' : v >= 1e3 ? (v/1e3).toFixed(1)+'k' : String(v);
const T = D.totals;
document.getElementById('sub').textContent = `${T.sessions} sessions · ${T.turns} turns · timezone ${D.timezone} · estimates from pricing.json, not invoices`;
[[usd(T.cost),'estimated cost'],[Math.round(T.cache_hit*100)+'%','cache hit'],[usd(T.saved_by_cache),'saved by cache'],
 [tok(T.output),'output tokens'],[Math.round(T.sidechain_share*100)+'%','subagent share'],[Math.round(T.active_min)+' min','active time']]
 .forEach(([v,l]) => { const t = el('div', undefined, 'tile'); t.append(el('b', v), el('span', l)); document.getElementById('tiles').append(t); });
const F = document.getElementById('findings');
if (!D.findings.length) F.append(el('div', 'No findings. Sessions look healthy.'));
D.findings.forEach(f => { const d = el('div', f.message, 'find ' + f.severity); d.append(el('small', `${f.kind}${f.project ? ' · ' + f.project : ''}${f.session ? ' · ' + f.session.slice(0, 8) : ''}`)); F.append(d); });
function table(id, cols, rows) {
  const t = document.getElementById(id); let sorted = rows.slice();
  const draw = () => { t.replaceChildren(); const head = el('tr');
    cols.forEach(c => { const th = el('th', c.h, c.n ? 'n' : ''); th.onclick = () => { sorted.sort((a, b) => c.n ? b[c.k] - a[c.k] : String(a[c.k]).localeCompare(String(b[c.k]))); draw(); }; head.append(th); });
    t.append(head);
    sorted.forEach(r => { const tr = el('tr'); cols.forEach(c => tr.append(el('td', c.f ? c.f(r[c.k], r) : r[c.k], c.n ? 'n' : ''))); t.append(tr); }); };
  draw();
}
table('projects', [{h:'Project',k:'project'},{h:'Cost',k:'cost',n:1,f:usd},{h:'Turns',k:'turns',n:1}], D.by_project);
table('tools', [{h:'Tool',k:'tool'},{h:'Calls',k:'calls',n:1},{h:'Errors',k:'errors',n:1}], D.tools);
table('sessions', [{h:'Start',k:'start'},{h:'Project',k:'project'},{h:'Cost',k:'cost',n:1,f:usd},{h:'Active min',k:'active_min',n:1},
  {h:'Peak ctx',k:'peak_context',n:1,f:tok},{h:'Cache',k:'cache_hit',n:1,f:v => Math.round(v*100)+'%'},{h:'Turns',k:'turns',n:1}], D.sessions);
if (window.Chart) {
  const css = getComputedStyle(document.documentElement), fg = css.getPropertyValue('--mut'), acc = css.getPropertyValue('--acc');
  new Chart(document.getElementById('dayChart'), {type:'bar', data:{labels:D.by_day.map(d => d.day), datasets:[{data:D.by_day.map(d => +d.cost.toFixed(2)), backgroundColor:acc}]},
    options:{maintainAspectRatio:false, plugins:{legend:{display:false}}, scales:{x:{ticks:{color:fg}}, y:{ticks:{color:fg}, beginAtZero:true}}}});
  new Chart(document.getElementById('modelChart'), {type:'doughnut', data:{labels:D.by_model.map(m => m.model), datasets:[{data:D.by_model.map(m => +m.cost.toFixed(2))}]},
    options:{maintainAspectRatio:false, plugins:{legend:{position:'bottom', labels:{color:fg}}}}});
}
</script></body></html>
"""
