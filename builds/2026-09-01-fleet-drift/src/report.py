"""Self-contained dark-mode HTML dashboard renderer.

All dynamic data (repo names, dependency names, versions, the optional AI
briefing) is delivered to the browser as a single JSON payload inside a
``<script type="application/json">`` tag, read back with ``.textContent`` and
``JSON.parse`` and built into the DOM exclusively with ``createElement`` /
``textContent`` — never ``innerHTML`` — so a malicious repo or dependency
name can never execute as markup. ``</`` inside the JSON payload is escaped
to ``<\\/`` so a value like ``</script><script>...`` can never prematurely
close the data tag.
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional

from .drift import DriftEntry, StalenessEntry

CHART_JS_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


def _escape_script_payload(payload: dict) -> str:
    return json.dumps(payload).replace("</", "<\\/")


def build_payload(
    generated_at: str,
    repos_scanned: int,
    drift_entries: List[DriftEntry],
    staleness_entries: List[StalenessEntry],
    repo_summary: Dict[str, dict],
    briefing: Optional[str],
) -> dict:
    unique_dependencies = {(e["ecosystem"], e["dependency"]) for e in staleness_entries}
    major_drift_count = sum(1 for e in drift_entries if e["severity"] == "major")

    drift_rows = [
        {
            "dependency": e["dependency"],
            "ecosystem": e["ecosystem"],
            "severity": e["severity"],
            "min_version": e["min_version"],
            "max_version": e["max_version"],
            "repo_versions": [
                {"repo": repo, "version": version} for repo, version in sorted(e["repo_versions"].items())
            ],
        }
        for e in drift_entries
    ]

    repo_rows = [
        {
            "repo": repo,
            "total": stats["total"],
            "behind_count": stats["behind_count"],
            "major_count": stats["major_count"],
        }
        for repo, stats in sorted(repo_summary.items(), key=lambda kv: -kv[1]["major_count"])
    ]

    chart_rows = [
        {"dependency": e["dependency"], "severity_rank": {"major": 3, "minor": 2, "patch": 1, "unknown": 0}.get(e["severity"], 0)}
        for e in drift_entries[:10]
    ]

    return {
        "generated_at": generated_at,
        "hero": {
            "repos_scanned": repos_scanned,
            "unique_dependencies": len(unique_dependencies),
            "drifted_count": len(drift_entries),
            "major_drift_count": major_drift_count,
        },
        "drift_rows": drift_rows,
        "repo_rows": repo_rows,
        "chart_rows": chart_rows,
        "briefing": briefing,
    }


_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fleet Drift</title>
<script src="__CHART_JS_URL__"></script>
<style>
  :root {
    --bg: #0f1117;
    --panel: #171a23;
    --panel-border: #262b38;
    --text: #e6e8ef;
    --muted: #9aa1b4;
    --accent: #6ea8fe;
    --major: #ef5350;
    --minor: #f0a848;
    --patch: #6ea8fe;
    --none: #4caf7d;
    --radius: 10px;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 24px;
  }
  h1 { margin: 0 0 4px 0; font-size: 1.6rem; }
  .subtitle { color: var(--muted); margin-bottom: 24px; font-size: 0.9rem; }
  .hero { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 24px; }
  .stat {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: var(--radius);
    padding: 16px;
  }
  .stat .value { font-size: 1.8rem; font-weight: 700; }
  .stat .label { color: var(--muted); font-size: 0.8rem; margin-top: 4px; }
  .panel {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: var(--radius);
    padding: 16px;
    margin-bottom: 24px;
  }
  .panel h2 { margin-top: 0; font-size: 1.1rem; }
  input[type="search"] {
    width: 100%;
    max-width: 320px;
    padding: 8px 10px;
    border-radius: 6px;
    border: 1px solid var(--panel-border);
    background: #0d0f15;
    color: var(--text);
    margin-bottom: 12px;
  }
  table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--panel-border); }
  th { color: var(--muted); cursor: pointer; user-select: none; font-weight: 600; }
  th:hover { color: var(--text); }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #0f1117;
  }
  .badge-major { background: var(--major); }
  .badge-minor { background: var(--minor); }
  .badge-patch { background: var(--patch); }
  .badge-unknown, .badge-none { background: var(--muted); }
  .repo-list { color: var(--muted); }
  #chart-fallback table { margin-top: 8px; }
  canvas { max-height: 320px; }
  .briefing { line-height: 1.5; }
  .empty { color: var(--muted); font-style: italic; }
  @media (max-width: 600px) {
    body { padding: 12px; }
    .hero { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>
<h1>Fleet Drift</h1>
<div class="subtitle" id="generated-at"></div>

<div class="hero" id="hero"></div>

<div class="panel" id="briefing-panel" hidden>
  <h2>What to fix first</h2>
  <p class="briefing" id="briefing-text"></p>
</div>

<div class="panel">
  <h2>Most drifted dependencies</h2>
  <canvas id="drift-chart" height="90"></canvas>
  <div id="chart-fallback" hidden></div>
</div>

<div class="panel">
  <h2>Drift matrix</h2>
  <input type="search" id="drift-search" placeholder="Filter by dependency name...">
  <table id="drift-table">
    <thead>
      <tr>
        <th data-key="dependency">Dependency</th>
        <th data-key="ecosystem">Ecosystem</th>
        <th data-key="severity">Severity</th>
        <th>Versions in use</th>
      </tr>
    </thead>
    <tbody id="drift-tbody"></tbody>
  </table>
  <p class="empty" id="drift-empty" hidden>No cross-repo dependency drift detected.</p>
</div>

<div class="panel">
  <h2>Per-repo staleness</h2>
  <table id="repo-table">
    <thead>
      <tr>
        <th data-key="repo">Repo</th>
        <th data-key="total">Dependencies tracked</th>
        <th data-key="behind_count">Behind latest</th>
        <th data-key="major_count">Major-behind</th>
      </tr>
    </thead>
    <tbody id="repo-tbody"></tbody>
  </table>
</div>

<script type="application/json" id="fleet-drift-data">__DATA_JSON__</script>
<script>
(function () {
  var raw = document.getElementById('fleet-drift-data').textContent;
  var data = JSON.parse(raw);

  document.getElementById('generated-at').textContent = 'Generated ' + data.generated_at;

  function el(tag, opts) {
    var node = document.createElement(tag);
    opts = opts || {};
    if (opts.text !== undefined) node.textContent = opts.text;
    if (opts.className) node.className = opts.className;
    return node;
  }

  function renderHero() {
    var hero = document.getElementById('hero');
    var stats = [
      { label: 'Repos scanned', value: data.hero.repos_scanned },
      { label: 'Unique dependencies', value: data.hero.unique_dependencies },
      { label: 'Drifted dependencies', value: data.hero.drifted_count },
      { label: 'Major-severity drift', value: data.hero.major_drift_count }
    ];
    stats.forEach(function (stat) {
      var card = el('div', { className: 'stat' });
      card.appendChild(el('div', { className: 'value', text: String(stat.value) }));
      card.appendChild(el('div', { className: 'label', text: stat.label }));
      hero.appendChild(card);
    });
  }

  function renderBriefing() {
    if (!data.briefing) return;
    document.getElementById('briefing-panel').hidden = false;
    document.getElementById('briefing-text').textContent = data.briefing;
  }

  function severityBadge(severity) {
    var span = el('span', { className: 'badge badge-' + severity, text: severity });
    return span;
  }

  function renderDriftRow(row) {
    var tr = document.createElement('tr');

    var tdName = document.createElement('td');
    tdName.textContent = row.dependency;
    tr.appendChild(tdName);

    var tdEco = document.createElement('td');
    tdEco.textContent = row.ecosystem;
    tr.appendChild(tdEco);

    var tdSev = document.createElement('td');
    tdSev.appendChild(severityBadge(row.severity));
    tr.appendChild(tdSev);

    var tdVersions = document.createElement('td');
    tdVersions.className = 'repo-list';
    var text = row.repo_versions.map(function (rv) { return rv.repo + ' @ ' + rv.version; }).join(', ');
    tdVersions.textContent = text;
    tr.appendChild(tdVersions);

    return tr;
  }

  var driftRows = data.drift_rows.slice();

  function renderDriftTable(rows) {
    var tbody = document.getElementById('drift-tbody');
    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
    rows.forEach(function (row) { tbody.appendChild(renderDriftRow(row)); });
    document.getElementById('drift-empty').hidden = rows.length > 0;
  }

  document.getElementById('drift-search').addEventListener('input', function (evt) {
    var term = evt.target.value.trim().toLowerCase();
    var filtered = driftRows.filter(function (row) {
      return row.dependency.toLowerCase().indexOf(term) !== -1;
    });
    renderDriftTable(filtered);
  });

  var driftSortState = { key: null, asc: true };
  document.querySelectorAll('#drift-table th[data-key]').forEach(function (th) {
    th.addEventListener('click', function () {
      var key = th.getAttribute('data-key');
      driftSortState.asc = driftSortState.key === key ? !driftSortState.asc : true;
      driftSortState.key = key;
      var sorted = driftRows.slice().sort(function (a, b) {
        if (a[key] < b[key]) return driftSortState.asc ? -1 : 1;
        if (a[key] > b[key]) return driftSortState.asc ? 1 : -1;
        return 0;
      });
      renderDriftTable(sorted);
    });
  });

  function renderRepoTable() {
    var tbody = document.getElementById('repo-tbody');
    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
    data.repo_rows.forEach(function (row) {
      var tr = document.createElement('tr');
      [row.repo, String(row.total), String(row.behind_count), String(row.major_count)].forEach(function (val) {
        var td = document.createElement('td');
        td.textContent = val;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }

  function renderChart() {
    var rows = data.chart_rows;
    if (typeof Chart === 'undefined') {
      var fallback = document.getElementById('chart-fallback');
      fallback.hidden = false;
      document.getElementById('drift-chart').hidden = true;
      var table = document.createElement('table');
      var tbody = document.createElement('tbody');
      rows.forEach(function (row) {
        var tr = document.createElement('tr');
        var tdName = document.createElement('td');
        tdName.textContent = row.dependency;
        var tdVal = document.createElement('td');
        tdVal.textContent = String(row.severity_rank);
        tr.appendChild(tdName);
        tr.appendChild(tdVal);
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      fallback.appendChild(table);
      return;
    }
    var ctx = document.getElementById('drift-chart').getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: rows.map(function (r) { return r.dependency; }),
        datasets: [{
          label: 'Drift severity',
          data: rows.map(function (r) { return r.severity_rank; }),
          backgroundColor: '#6ea8fe'
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 }, title: { display: true, text: 'Severity (1=patch, 2=minor, 3=major)' } }
        }
      }
    });
  }

  renderHero();
  renderBriefing();
  renderDriftTable(driftRows);
  renderRepoTable();
  renderChart();
})();
</script>
</body>
</html>
"""


def render(
    generated_at: str,
    repos_scanned: int,
    drift_entries: List[DriftEntry],
    staleness_entries: List[StalenessEntry],
    repo_summary: Dict[str, dict],
    briefing: Optional[str] = None,
) -> str:
    payload = build_payload(
        generated_at, repos_scanned, drift_entries, staleness_entries, repo_summary, briefing
    )
    html = _TEMPLATE.replace("__CHART_JS_URL__", CHART_JS_URL)
    html = html.replace("__DATA_JSON__", _escape_script_payload(payload))
    return html
