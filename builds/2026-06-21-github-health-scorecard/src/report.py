import html as html_lib
import json
from typing import Optional

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"

_CSS = """
:root {
    --bg: #0d1117;
    --bg-card: #161b22;
    --bg-input: #21262d;
    --border: #30363d;
    --text: #e6edf3;
    --text-muted: #8b949e;
    --healthy: #3fb950;
    --good: #58a6ff;
    --fair: #d29922;
    --attention: #f0883e;
    --stale: #f85149;
    --healthy-bg: rgba(63,185,80,0.12);
    --good-bg: rgba(88,166,255,0.12);
    --fair-bg: rgba(210,153,34,0.12);
    --attention-bg: rgba(240,136,62,0.12);
    --stale-bg: rgba(248,81,73,0.12);
    --radius: 6px;
    --spacing: 16px;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    font-size: 14px;
    line-height: 1.5;
    padding: var(--spacing);
}
header {
    padding: 24px 0 16px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}
header h1 { font-size: 24px; font-weight: 600; margin-bottom: 4px; }
header p { color: var(--text-muted); font-size: 13px; }
.stats-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 24px;
}
.stat-card {
    flex: 1;
    min-width: 120px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    text-align: center;
}
.stat-card .count { font-size: 28px; font-weight: 700; }
.stat-card .label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.stat-card.s-healthy .count { color: var(--healthy); }
.stat-card.s-good .count { color: var(--good); }
.stat-card.s-fair .count { color: var(--fair); }
.stat-card.s-attention .count { color: var(--attention); }
.stat-card.s-stale .count { color: var(--stale); }
.ai-panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--spacing);
    margin-bottom: 24px;
}
.ai-panel h2 { font-size: 15px; font-weight: 600; margin-bottom: 10px; color: var(--text); }
.ai-panel ul { list-style: none; }
.ai-panel li { padding: 4px 0; color: var(--text-muted); font-size: 13px; }
.ai-panel li::before { content: ""; }
.chart-row {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
    align-items: center;
    justify-content: center;
}
.chart-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--spacing);
    max-width: 320px;
    width: 100%;
}
.chart-container h3 { font-size: 13px; color: var(--text-muted); margin-bottom: 12px; }
.controls {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
    align-items: center;
}
.controls input[type=text] {
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text);
    font-size: 13px;
    padding: 6px 10px;
    flex: 1;
    min-width: 160px;
    outline: none;
}
.controls input[type=text]::placeholder { color: var(--text-muted); }
.filter-btns { display: flex; flex-wrap: wrap; gap: 4px; }
.filter-btns button {
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-muted);
    cursor: pointer;
    font-size: 12px;
    padding: 4px 10px;
    transition: border-color 0.15s, color 0.15s;
}
.filter-btns button.active,
.filter-btns button:hover { border-color: var(--good); color: var(--text); }
.table-wrap {
    overflow-x: auto;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
}
table { width: 100%; border-collapse: collapse; }
thead tr { border-bottom: 1px solid var(--border); }
th {
    padding: 10px 12px;
    text-align: left;
    font-size: 12px;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    white-space: nowrap;
    user-select: none;
}
th.sortable { cursor: pointer; }
th.sortable:hover { color: var(--text); }
td { padding: 10px 12px; vertical-align: middle; border-bottom: 1px solid var(--border); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(255,255,255,0.03); }
.repo-link { color: var(--good); text-decoration: none; font-weight: 500; }
.repo-link:hover { text-decoration: underline; }
.badge {
    display: inline-block;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    white-space: nowrap;
}
.badge.healthy  { background: var(--healthy-bg); color: var(--healthy); }
.badge.good     { background: var(--good-bg);    color: var(--good); }
.badge.fair     { background: var(--fair-bg);    color: var(--fair); }
.badge.attention { background: var(--attention-bg); color: var(--attention); }
.badge.stale    { background: var(--stale-bg);   color: var(--stale); }
.ci-dot {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
}
.ci-dot::before {
    content: "";
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}
.ci-dot.passing::before  { background: var(--healthy); }
.ci-dot.failing::before  { background: var(--stale); }
.ci-dot.running::before  { background: var(--fair); }
.ci-dot.no-ci::before    { background: var(--border); }
.score-bar-wrap { display: flex; align-items: center; gap: 6px; }
.score-bar {
    width: 60px;
    height: 6px;
    background: var(--bg-input);
    border-radius: 3px;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s;
}
.score-num { font-size: 12px; color: var(--text-muted); min-width: 26px; }
.lang-pill {
    font-size: 11px;
    color: var(--text-muted);
    background: var(--bg-input);
    border-radius: 3px;
    padding: 1px 5px;
}
.empty-state { padding: 32px; text-align: center; color: var(--text-muted); }
@media (max-width: 600px) {
    .stats-grid { flex-direction: column; }
    td, th { padding: 8px; }
}
"""

_JS = """
const REPOS = {repos_json};

let sortField = 'health_score';
let sortAsc = true;
let filterLabel = 'all';
let searchTerm = '';

const scoreColors = {
  healthy:   '#3fb950',
  good:      '#58a6ff',
  fair:      '#d29922',
  attention: '#f0883e',
  stale:     '#f85149',
};

function ciLabel(status) {
  const map = {passing: 'Passing', failing: 'Failing', running: 'Running', 'no-ci': 'No CI'};
  return map[status] || status;
}

function renderTable() {
  let data = REPOS.filter(r => {
    if (filterLabel !== 'all' && r.health_css !== filterLabel) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      return r.name.toLowerCase().includes(q) ||
             (r.language && r.language.toLowerCase().includes(q)) ||
             (r.description && r.description.toLowerCase().includes(q));
    }
    return true;
  });

  data.sort((a, b) => {
    let av = a[sortField], bv = b[sortField];
    if (typeof av === 'string') av = av.toLowerCase();
    if (typeof bv === 'string') bv = bv.toLowerCase();
    if (av < bv) return sortAsc ? -1 : 1;
    if (av > bv) return sortAsc ? 1 : -1;
    return 0;
  });

  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = '';

  if (data.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 7;
    td.className = 'empty-state';
    td.textContent = 'No repositories match the current filter.';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  data.forEach(r => {
    const tr = document.createElement('tr');
    tr.dataset.label = r.health_css;

    // Repo name
    const tdName = document.createElement('td');
    const a = document.createElement('a');
    a.className = 'repo-link';
    a.href = 'https://github.com/' + r.full_name;
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = r.name;
    if (r.private) {
      const lock = document.createElement('span');
      lock.textContent = ' 🔒';
      lock.title = 'Private';
      a.appendChild(lock);
    }
    tdName.appendChild(a);
    if (r.description) {
      const desc = document.createElement('div');
      desc.style.color = 'var(--text-muted)';
      desc.style.fontSize = '11px';
      desc.style.marginTop = '2px';
      desc.textContent = r.description.slice(0, 80) + (r.description.length > 80 ? '…' : '');
      tdName.appendChild(desc);
    }
    tr.appendChild(tdName);

    // Language
    const tdLang = document.createElement('td');
    const pill = document.createElement('span');
    pill.className = 'lang-pill';
    pill.textContent = r.language || '—';
    tdLang.appendChild(pill);
    tr.appendChild(tdLang);

    // Score
    const tdScore = document.createElement('td');
    const wrap = document.createElement('div');
    wrap.className = 'score-bar-wrap';
    const bar = document.createElement('div');
    bar.className = 'score-bar';
    const fill = document.createElement('div');
    fill.className = 'score-bar-fill';
    fill.style.width = r.health_score + '%';
    fill.style.background = scoreColors[r.health_css] || '#8b949e';
    bar.appendChild(fill);
    const num = document.createElement('span');
    num.className = 'score-num';
    num.textContent = r.health_score;
    wrap.appendChild(bar);
    wrap.appendChild(num);
    tdScore.appendChild(wrap);
    tr.appendChild(tdScore);

    // Health badge
    const tdHealth = document.createElement('td');
    const badge = document.createElement('span');
    badge.className = 'badge ' + r.health_css;
    badge.textContent = r.health_label;
    tdHealth.appendChild(badge);
    tr.appendChild(tdHealth);

    // Last push
    const tdPush = document.createElement('td');
    const days = r.days_since_push;
    tdPush.textContent = days === 0 ? 'Today' : days === 1 ? 'Yesterday' :
      days < 30 ? days + 'd ago' :
      days < 365 ? Math.floor(days / 30) + 'mo ago' :
      Math.floor(days / 365) + 'yr ago';
    tdPush.style.color = days > 90 ? 'var(--stale)' : days > 30 ? 'var(--attention)' : 'var(--text)';
    tr.appendChild(tdPush);

    // Issues
    const tdIssues = document.createElement('td');
    tdIssues.textContent = r.open_issues;
    tdIssues.style.color = r.open_issues > 20 ? 'var(--stale)' : r.open_issues > 5 ? 'var(--attention)' : 'var(--text)';
    tr.appendChild(tdIssues);

    // CI status
    const tdCi = document.createElement('td');
    const dot = document.createElement('span');
    dot.className = 'ci-dot ' + r.ci_status;
    dot.textContent = ciLabel(r.ci_status);
    tdCi.appendChild(dot);
    tr.appendChild(tdCi);

    tbody.appendChild(tr);
  });
}

function sortBy(field) {
  if (sortField === field) {
    sortAsc = !sortAsc;
  } else {
    sortField = field;
    sortAsc = field === 'health_score';
  }
  renderTable();
}

function filterBy(label) {
  filterLabel = label;
  document.querySelectorAll('.filter-btns button').forEach(b => {
    b.classList.toggle('active', b.dataset.filter === label);
  });
  renderTable();
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('searchBox').addEventListener('input', e => {
    searchTerm = e.target.value;
    renderTable();
  });

  // Build Chart.js doughnut
  const counts = {healthy: 0, good: 0, fair: 0, attention: 0, stale: 0};
  REPOS.forEach(r => { counts[r.health_css] = (counts[r.health_css] || 0) + 1; });
  const ctx = document.getElementById('healthChart').getContext('2d');
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Healthy', 'Good', 'Fair', 'Needs Attention', 'Stale'],
      datasets: [{
        data: [counts.healthy, counts.good, counts.fair, counts.attention, counts.stale],
        backgroundColor: ['#3fb950','#58a6ff','#d29922','#f0883e','#f85149'],
        borderColor: '#161b22',
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#8b949e', font: { size: 11 }, padding: 8 }
        },
        tooltip: {
          callbacks: {
            label: ctx => ' ' + ctx.label + ': ' + ctx.parsed
          }
        }
      },
      cutout: '60%',
    }
  });

  filterBy('all');
});
"""


def _ai_panel_html(ai_insights: str) -> str:
    if not ai_insights:
        return ""
    lines = [l.strip() for l in ai_insights.split("\n") if l.strip()]
    lis = "\n".join(
        f"        <li>{html_lib.escape(line)}</li>" for line in lines
    )
    return f"""    <section class="ai-panel">
      <h2>🤖 AI Briefing</h2>
      <ul>
{lis}
      </ul>
    </section>
"""


def render_html(repos: list[dict], generated_at: str, ai_insights: str = "") -> str:
    """Render a self-contained HTML health scorecard."""
    counts: dict[str, int] = {
        "healthy": 0, "good": 0, "fair": 0, "attention": 0, "stale": 0
    }
    for r in repos:
        key = r.get("health_css", "stale")
        counts[key] = counts.get(key, 0) + 1

    total = len(repos)
    repos_json = (
        json.dumps(repos, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    js = _JS.replace("{repos_json}", repos_json)

    stats_html = "\n".join([
        f'    <div class="stat-card s-healthy"><div class="count">{counts["healthy"]}</div><div class="label">Healthy</div></div>',
        f'    <div class="stat-card s-good"><div class="count">{counts["good"]}</div><div class="label">Good</div></div>',
        f'    <div class="stat-card s-fair"><div class="count">{counts["fair"]}</div><div class="label">Fair</div></div>',
        f'    <div class="stat-card s-attention"><div class="count">{counts["attention"]}</div><div class="label">Needs Attention</div></div>',
        f'    <div class="stat-card s-stale"><div class="count">{counts["stale"]}</div><div class="label">Stale</div></div>',
    ])

    ai_html = _ai_panel_html(ai_insights)

    filter_buttons = "\n".join([
        '          <button class="active" data-filter="all" onclick="filterBy(\'all\')">All</button>',
        '          <button data-filter="healthy" onclick="filterBy(\'healthy\')">Healthy</button>',
        '          <button data-filter="good" onclick="filterBy(\'good\')">Good</button>',
        '          <button data-filter="fair" onclick="filterBy(\'fair\')">Fair</button>',
        '          <button data-filter="attention" onclick="filterBy(\'attention\')">Needs Attention</button>',
        '          <button data-filter="stale" onclick="filterBy(\'stale\')">Stale</button>',
    ])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GitHub Repository Health Scorecard</title>
  <script src="{CHART_JS_CDN}"></script>
  <style>
{_CSS}
  </style>
</head>
<body>
  <header>
    <h1>GitHub Repository Health Scorecard</h1>
    <p>Generated: {html_lib.escape(generated_at)} &nbsp;·&nbsp; {total} repositories analyzed</p>
  </header>

  <section class="stats-grid">
{stats_html}
  </section>

{ai_html}
  <section class="chart-row">
    <div class="chart-container">
      <h3>Health Distribution</h3>
      <canvas id="healthChart" height="240"></canvas>
    </div>
  </section>

  <section>
    <div class="controls">
      <input type="text" id="searchBox" placeholder="Filter by name, language, or description…">
      <div class="filter-btns">
{filter_buttons}
      </div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th class="sortable" onclick="sortBy('name')">Repository ↕</th>
            <th class="sortable" onclick="sortBy('language')">Language ↕</th>
            <th class="sortable" onclick="sortBy('health_score')">Score ↕</th>
            <th>Health</th>
            <th class="sortable" onclick="sortBy('days_since_push')">Last Push ↕</th>
            <th class="sortable" onclick="sortBy('open_issues')">Issues ↕</th>
            <th class="sortable" onclick="sortBy('ci_status')">CI ↕</th>
          </tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
  </section>

  <script>
{js}
  </script>
</body>
</html>"""
