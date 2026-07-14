"""Renders the self-contained GrantScope HTML dashboard.

All project-sourced text (titles, abstracts, org/PI names) originates from the
public NIH RePORTER API but is treated as untrusted for rendering purposes:
it is embedded as JSON inside a <script type="application/json"> block and
written into the DOM exclusively via textContent on the client side, never
via innerHTML, so no script-injection payload in a title or abstract can
execute. Chart.js is loaded from a pinned CDN URL; if it fails to load
(offline use), the dashboard falls back to a plain-text summary instead of
breaking.
"""

import html
import json
from typing import Any, Dict, List

CHART_JS_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


def _json_script(data: Any) -> str:
    """Serialize data as JSON safe to embed inside a <script> tag."""
    return json.dumps(data, default=str).replace("</", "<\\/")


def _aggregate_overview(topics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    all_projects: List[Dict[str, Any]] = []
    for topic in topics_data:
        all_projects.extend(topic["projects"])

    funding_by_year: Dict[str, Dict[str, int]] = {}
    for topic in topics_data:
        for year, info in topic["funding_by_year"].items():
            key = str(year)
            bucket = funding_by_year.setdefault(key, {"total_amount": 0, "count": 0})
            bucket["total_amount"] += info["total_amount"]
            bucket["count"] += info["count"]

    institutes: Dict[str, Dict[str, int]] = {}
    for topic in topics_data:
        for name, info in topic["top_institutes"]:
            bucket = institutes.setdefault(name, {"total_amount": 0, "count": 0})
            bucket["total_amount"] += info["total_amount"]
            bucket["count"] += info["count"]
    top_institutes_overall = sorted(institutes.items(), key=lambda kv: kv[1]["total_amount"], reverse=True)[:10]

    mechanisms: Dict[str, int] = {}
    for topic in topics_data:
        for code, count in topic["mechanisms"].items():
            mechanisms[code] = mechanisms.get(code, 0) + count

    return {
        "project_count": len(all_projects),
        "total_amount": sum((p.get("award_amount") or 0) for p in all_projects),
        "funding_by_year": funding_by_year,
        "top_institutes": top_institutes_overall,
        "mechanisms": dict(sorted(mechanisms.items(), key=lambda kv: kv[1], reverse=True)),
    }


def render_dashboard(topics_data: List[Dict[str, Any]], generated_at: str) -> str:
    """Render the full self-contained dashboard HTML.

    topics_data: list of dicts with keys:
        key, label, projects (list of plain dicts), funding_by_year, top_institutes,
        top_organizations, mechanisms, keywords, stats, briefing ({"text","source"})
    """
    overview = _aggregate_overview(topics_data)

    payload = {
        "generated_at": generated_at,
        "overview": overview,
        "topics": topics_data,
    }

    tab_buttons = ['<button class="tab-btn active" data-tab="overview">Overview</button>']
    for topic in topics_data:
        safe_label = html.escape(topic["label"])
        tab_buttons.append(
            f'<button class="tab-btn" data-tab="{html.escape(topic["key"])}">{safe_label}</button>'
        )

    topic_sections = []
    for topic in topics_data:
        key = html.escape(topic["key"])
        label = html.escape(topic["label"])
        briefing_source = html.escape(topic["briefing"].get("source", "template"))
        topic_sections.append(f"""
        <section class="tab-panel" id="panel-{key}" hidden>
            <h2>{label}</h2>
            <div class="stat-row" id="stats-{key}"></div>
            <p class="briefing" data-source="{briefing_source}"><span class="briefing-label">Landscape briefing ({briefing_source}):</span> <span id="briefing-text-{key}"></span></p>
            <div class="chart-grid">
                <div class="chart-card"><h3>Funding by Fiscal Year</h3><canvas id="chart-year-{key}"></canvas><div class="chart-fallback" id="fallback-year-{key}" hidden></div></div>
                <div class="chart-card"><h3>Top Funding Institutes/Centers</h3><canvas id="chart-inst-{key}"></canvas><div class="chart-fallback" id="fallback-inst-{key}" hidden></div></div>
                <div class="chart-card"><h3>Funding Mechanism Breakdown</h3><canvas id="chart-mech-{key}"></canvas><div class="chart-fallback" id="fallback-mech-{key}" hidden></div></div>
            </div>
            <div class="table-controls">
                <input type="text" class="search-box" id="search-{key}" placeholder="Search projects by title, org, or PI...">
            </div>
            <table class="project-table" id="table-{key}">
                <thead><tr><th>Title</th><th>PI</th><th>Organization</th><th>Institute</th><th>Mechanism</th><th>FY</th><th>Award</th></tr></thead>
                <tbody></tbody>
            </table>
        </section>""")

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GrantScope — NIH Funding Landscape</title>
<script src="{CHART_JS_URL}"></script>
<style>
:root {{
    --bg: #0f1420;
    --bg-card: #161d2e;
    --border: #2a3348;
    --text: #e6e9f0;
    --text-dim: #9aa3b8;
    --accent: #5fb0ff;
    --accent-2: #8ee6b0;
    --warn: #f0b45c;
}}
@media (prefers-color-scheme: light) {{
    :root:not([data-theme="dark"]) {{
        --bg: #f5f6fa; --bg-card: #ffffff; --border: #dde1ea; --text: #1b2130; --text-dim: #5a6377;
    }}
}}
* {{ box-sizing: border-box; }}
body {{
    margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg); color: var(--text); padding: 1.5rem; line-height: 1.5;
}}
header {{ margin-bottom: 1.5rem; }}
h1 {{ margin: 0 0 0.25rem 0; font-size: 1.6rem; }}
.meta {{ color: var(--text-dim); font-size: 0.85rem; }}
.tabs {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 1.25rem 0; }}
.tab-btn {{
    background: var(--bg-card); color: var(--text); border: 1px solid var(--border);
    padding: 0.5rem 0.9rem; border-radius: 999px; cursor: pointer; font-size: 0.85rem;
}}
.tab-btn.active {{ background: var(--accent); color: #06121f; border-color: var(--accent); font-weight: 600; }}
.tab-panel {{ animation: fade 0.15s ease-in; }}
@keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
.stat-row {{ display: flex; flex-wrap: wrap; gap: 0.75rem; margin: 1rem 0; }}
.stat-tile {{
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px;
    padding: 0.75rem 1rem; min-width: 140px; flex: 1 1 140px;
}}
.stat-tile .val {{ font-size: 1.4rem; font-weight: 700; }}
.stat-tile .label {{ color: var(--text-dim); font-size: 0.78rem; }}
.briefing {{
    background: var(--bg-card); border: 1px solid var(--border); border-left: 3px solid var(--accent-2);
    border-radius: 8px; padding: 0.8rem 1rem; font-size: 0.92rem; margin: 1rem 0;
}}
.briefing-label {{ color: var(--accent-2); font-weight: 600; }}
.chart-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin: 1rem 0; }}
.chart-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 0.9rem; }}
.chart-card h3 {{ margin: 0 0 0.6rem 0; font-size: 0.9rem; color: var(--text-dim); }}
.chart-card canvas {{ max-height: 220px; }}
.chart-fallback {{ color: var(--text-dim); font-size: 0.85rem; white-space: pre-line; }}
.table-controls {{ margin: 1rem 0 0.5rem 0; }}
.search-box {{
    width: 100%; max-width: 420px; padding: 0.55rem 0.8rem; border-radius: 8px;
    border: 1px solid var(--border); background: var(--bg-card); color: var(--text); font-size: 0.9rem;
}}
table.project-table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; font-size: 0.85rem; }}
.project-table th, .project-table td {{
    text-align: left; padding: 0.5rem 0.6rem; border-bottom: 1px solid var(--border); vertical-align: top;
}}
.project-table th {{ color: var(--text-dim); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; }}
.no-data {{ color: var(--text-dim); font-style: italic; padding: 1rem 0; }}
@media (max-width: 600px) {{
    body {{ padding: 0.9rem; }}
    .project-table {{ font-size: 0.78rem; }}
}}
</style>
</head>
<body>
<header>
    <h1>GrantScope — NIH Funding Landscape</h1>
    <div class="meta">Generated {html.escape(generated_at)} · Data source: NIH RePORTER (public, no auth)</div>
</header>

<nav class="tabs" id="tabs">
{''.join(tab_buttons)}
</nav>

<section class="tab-panel" id="panel-overview">
    <h2>Overview — All Topics</h2>
    <div class="stat-row" id="stats-overview"></div>
    <div class="chart-grid">
        <div class="chart-card"><h3>Total Funding by Fiscal Year</h3><canvas id="chart-year-overview"></canvas><div class="chart-fallback" id="fallback-year-overview" hidden></div></div>
        <div class="chart-card"><h3>Top Funding Institutes/Centers (All Topics)</h3><canvas id="chart-inst-overview"></canvas><div class="chart-fallback" id="fallback-inst-overview" hidden></div></div>
        <div class="chart-card"><h3>Funding Mechanism Breakdown (All Topics)</h3><canvas id="chart-mech-overview"></canvas><div class="chart-fallback" id="fallback-mech-overview" hidden></div></div>
    </div>
</section>
{''.join(topic_sections)}

<script type="application/json" id="grantscope-data">{_json_script(payload)}</script>
<script>
(function () {{
    var data = JSON.parse(document.getElementById('grantscope-data').textContent);
    var chartsAvailable = typeof Chart !== 'undefined';

    function fmtMoney(n) {{
        return '$' + Number(n || 0).toLocaleString('en-US');
    }}

    function renderStats(containerId, stats) {{
        var el = document.getElementById(containerId);
        if (!el) return;
        var tiles = [
            ['Projects', stats.project_count],
            ['Total Funding', fmtMoney(stats.total_amount)],
        ];
        tiles.forEach(function (pair) {{
            var tile = document.createElement('div');
            tile.className = 'stat-tile';
            var val = document.createElement('div');
            val.className = 'val';
            val.textContent = pair[1];
            var label = document.createElement('div');
            label.className = 'label';
            label.textContent = pair[0];
            tile.appendChild(val);
            tile.appendChild(label);
            el.appendChild(tile);
        }});
    }}

    function fallbackText(pairs, formatValue) {{
        if (!pairs.length) return 'No data available.';
        return pairs.map(function (p) {{ return p[0] + ': ' + formatValue(p[1]); }}).join('\\n');
    }}

    function drawLineChart(canvasId, fallbackId, yearMap) {{
        var years = Object.keys(yearMap).sort();
        var amounts = years.map(function (y) {{ return yearMap[y].total_amount; }});
        if (!chartsAvailable) {{
            document.getElementById(fallbackId).hidden = false;
            document.getElementById(fallbackId).textContent = fallbackText(
                years.map(function (y) {{ return [y, yearMap[y].total_amount]; }}), fmtMoney
            );
            return;
        }}
        var ctx = document.getElementById(canvasId).getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{ labels: years, datasets: [{{ label: 'Total Award $', data: amounts, borderColor: '#5fb0ff', backgroundColor: 'rgba(95,176,255,0.15)', fill: true, tension: 0.25 }}] }},
            options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true }} }} }}
        }});
    }}

    function drawBarChart(canvasId, fallbackId, pairs) {{
        if (!chartsAvailable) {{
            document.getElementById(fallbackId).hidden = false;
            document.getElementById(fallbackId).textContent = fallbackText(
                pairs.map(function (p) {{ return [p[0], p[1].total_amount]; }}), fmtMoney
            );
            return;
        }}
        var ctx = document.getElementById(canvasId).getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: pairs.map(function (p) {{ return p[0]; }}),
                datasets: [{{ label: 'Total Award $', data: pairs.map(function (p) {{ return p[1].total_amount; }}), backgroundColor: '#8ee6b0' }}]
            }},
            options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ beginAtZero: true }} }} }}
        }});
    }}

    function drawDoughnutChart(canvasId, fallbackId, mechanismMap) {{
        var labels = Object.keys(mechanismMap);
        var counts = labels.map(function (l) {{ return mechanismMap[l]; }});
        if (!chartsAvailable) {{
            document.getElementById(fallbackId).hidden = false;
            document.getElementById(fallbackId).textContent = fallbackText(
                labels.map(function (l) {{ return [l, mechanismMap[l]]; }}), function (v) {{ return v + ' project(s)'; }}
            );
            return;
        }}
        var ctx = document.getElementById(canvasId).getContext('2d');
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{ labels: labels, datasets: [{{ data: counts, backgroundColor: ['#5fb0ff', '#8ee6b0', '#f0b45c', '#e08fd8', '#ff8f7a', '#7ad1ff', '#c2e88e', '#ffd27a'] }}] }},
            options: {{ plugins: {{ legend: {{ position: 'bottom', labels: {{ color: getComputedStyle(document.body).getPropertyValue('--text') }} }} }} }}
        }});
    }}

    function renderTable(tableId, projects, emptyMessage) {{
        var tbody = document.getElementById(tableId).querySelector('tbody');
        if (!projects.length) {{
            var tr = document.createElement('tr');
            var td = document.createElement('td');
            td.colSpan = 7;
            td.className = 'no-data';
            td.textContent = emptyMessage || 'No projects stored yet. Run "sync" to fetch data from NIH RePORTER.';
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }}
        projects.forEach(function (p) {{
            var tr = document.createElement('tr');
            [p.title, p.pi_name || '—', p.org_name || '—', p.ic_admin || '—', p.activity_code || '—', p.fiscal_year || '—', fmtMoney(p.award_amount)].forEach(function (val) {{
                var td = document.createElement('td');
                td.textContent = val;
                tr.appendChild(td);
            }});
            tbody.appendChild(tr);
        }});
    }}

    function attachSearch(inputId, tableId, projects) {{
        var input = document.getElementById(inputId);
        if (!input) return;
        input.addEventListener('input', function () {{
            var q = input.value.toLowerCase();
            var filtered = projects.filter(function (p) {{
                return (p.title || '').toLowerCase().indexOf(q) !== -1 ||
                    (p.org_name || '').toLowerCase().indexOf(q) !== -1 ||
                    (p.pi_name || '').toLowerCase().indexOf(q) !== -1;
            }});
            var tbody = document.getElementById(tableId).querySelector('tbody');
            tbody.innerHTML = '';
            var emptyMessage = projects.length ? 'No projects match your search.' : undefined;
            renderTable(tableId, filtered, emptyMessage);
        }});
    }}

    // Overview
    renderStats('stats-overview', data.overview);
    drawLineChart('chart-year-overview', 'fallback-year-overview', data.overview.funding_by_year);
    drawBarChart('chart-inst-overview', 'fallback-inst-overview', data.overview.top_institutes);
    drawDoughnutChart('chart-mech-overview', 'fallback-mech-overview', data.overview.mechanisms);

    // Per-topic
    data.topics.forEach(function (topic) {{
        var key = topic.key;
        renderStats('stats-' + key, topic.stats);
        var briefingEl = document.getElementById('briefing-text-' + key);
        if (briefingEl) briefingEl.textContent = topic.briefing.text;
        var yearMap = {{}};
        Object.keys(topic.funding_by_year).forEach(function (y) {{ yearMap[y] = topic.funding_by_year[y]; }});
        drawLineChart('chart-year-' + key, 'fallback-year-' + key, yearMap);
        drawBarChart('chart-inst-' + key, 'fallback-inst-' + key, topic.top_institutes);
        var mechMap = {{}};
        Object.keys(topic.mechanisms).forEach(function (m) {{ mechMap[m] = topic.mechanisms[m]; }});
        drawDoughnutChart('chart-mech-' + key, 'fallback-mech-' + key, mechMap);
        renderTable('table-' + key, topic.projects);
        attachSearch('search-' + key, 'table-' + key, topic.projects);
    }});

    // Tabs
    var buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(function (btn) {{
        btn.addEventListener('click', function () {{
            var target = btn.getAttribute('data-tab');
            document.querySelectorAll('.tab-panel').forEach(function (panel) {{
                panel.hidden = panel.id !== 'panel-' + target;
            }});
            buttons.forEach(function (b) {{ b.classList.toggle('active', b === btn); }});
        }});
    }});
}})();
</script>
</body>
</html>
"""
    return html_doc
