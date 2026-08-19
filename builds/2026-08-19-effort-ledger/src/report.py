"""Renders the self-contained dark-mode HTML dashboard.

All dynamic data is JSON-serialized into a <script type="application/json">
tag and read client-side with JSON.parse — never string-interpolated into
an executable <script> block. All DOM insertion in the embedded JS uses
createElement/textContent, never innerHTML, on data-derived strings.
"""

from __future__ import annotations

import json

from src.models import EffortLine, Flag, GrantBudgetSummary, OvercommitmentWindow


def _effort_line_to_dict(el: EffortLine) -> dict:
    return {
        "person_name": el.person_name,
        "grant_id": el.grant_id,
        "grant_name": el.grant_name,
        "period_start": el.period_start.isoformat(),
        "period_end": el.period_end.isoformat(),
        "percent_effort": el.percent_effort,
    }


def render_html(
    summaries: list[GrantBudgetSummary],
    flags: list[Flag],
    windows: list[OvercommitmentWindow],
    effort_lines: list[EffortLine],
    ai_briefing: str,
) -> str:
    data = {
        "summaries": [s.to_dict() for s in summaries],
        "flags": [f.to_dict() for f in flags],
        "windows": [w.to_dict() for w in windows],
        "effort_lines": [_effort_line_to_dict(el) for el in effort_lines],
        "ai_briefing": ai_briefing,
    }
    # Escape '<' so a value containing a literal "</script>" can never prematurely
    # close this embedding <script> tag when the browser's HTML parser scans past
    # JSON.parse — < is decoded back to '<' by JSON.parse with no visible change.
    data_json = json.dumps(data).replace("<", "\\u003c")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Effort Ledger — Audit Report</title>
<style>
{_CSS}
</style>
</head>
<body>
<header>
  <h1>Effort Ledger</h1>
  <p class="subtitle">Grant budget and effort-commitment audit report</p>
</header>

<section id="hero-stats" class="stats-grid"></section>

<section id="ai-briefing-section" class="panel" hidden>
  <h2>AI Briefing</h2>
  <p id="ai-briefing-text"></p>
</section>

<section class="panel">
  <h2>Effort Timeline</h2>
  <p class="hint">Each row is one person; colored segments are grant commitments; red bands mark overcommitment windows.</p>
  <canvas id="timeline-canvas" width="1000" height="400"></canvas>
  <div id="timeline-legend" class="legend"></div>
</section>

<section class="panel">
  <h2>Budget Summary</h2>
  <input type="text" id="budget-search" class="search" placeholder="Search grants...">
  <div class="table-wrap">
    <table id="budget-table">
      <thead>
        <tr>
          <th data-key="grant_id">Grant ID</th>
          <th data-key="grant_name">Grant Name</th>
          <th data-key="fiscal_year">FY</th>
          <th data-key="direct_total">Direct</th>
          <th data-key="mtdc">MTDC</th>
          <th data-key="expected_indirect">Expected Indirect</th>
          <th data-key="stated_indirect">Stated Indirect</th>
          <th data-key="total">Total</th>
        </tr>
      </thead>
      <tbody id="budget-tbody"></tbody>
    </table>
  </div>
</section>

<section class="panel">
  <h2>Flags</h2>
  <input type="text" id="flags-search" class="search" placeholder="Search flags...">
  <div class="filter-chips" id="severity-filters"></div>
  <div class="table-wrap">
    <table id="flags-table">
      <thead>
        <tr>
          <th data-key="severity">Severity</th>
          <th data-key="code">Type</th>
          <th data-key="message">Message</th>
          <th data-key="grant_id">Grant</th>
          <th data-key="person_name">Person</th>
        </tr>
      </thead>
      <tbody id="flags-tbody"></tbody>
    </table>
  </div>
</section>

<script id="audit-data" type="application/json">{data_json}</script>
<script>
{_JS}
</script>
</body>
</html>
"""


_CSS = """
:root {
  --bg: #0f1115;
  --panel: #161a21;
  --border: #262c37;
  --text: #e6e9ef;
  --muted: #8b93a3;
  --accent: #5eb0ff;
  --error: #ff6b6b;
  --warning: #ffc857;
  --info: #6bcf9f;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 24px;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  line-height: 1.5;
}
header { margin-bottom: 24px; }
h1 { margin: 0 0 4px 0; font-size: 1.8rem; }
.subtitle { color: var(--muted); margin: 0; }
.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
}
.panel h2 { margin-top: 0; font-size: 1.2rem; }
.hint { color: var(--muted); font-size: 0.85rem; margin-top: -8px; }
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}
.stat-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}
.stat-value { font-size: 1.8rem; font-weight: 700; }
.stat-label { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }
.search {
  width: 100%;
  padding: 8px 12px;
  margin-bottom: 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  font-size: 0.9rem;
}
.filter-chips { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.chip {
  padding: 4px 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--muted);
  cursor: pointer;
  font-size: 0.8rem;
  user-select: none;
}
.chip.active { border-color: var(--accent); color: var(--text); }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; min-width: 480px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }
th { color: var(--muted); cursor: pointer; white-space: nowrap; font-weight: 600; }
th:hover { color: var(--text); }
tbody tr:hover { background: rgba(255,255,255,0.03); }
.badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
.badge-error { background: rgba(255,107,107,0.15); color: var(--error); }
.badge-warning { background: rgba(255,200,87,0.15); color: var(--warning); }
.badge-info { background: rgba(107,207,159,0.15); color: var(--info); }
canvas { width: 100%; height: auto; background: var(--bg); border-radius: 8px; border: 1px solid var(--border); }
.legend { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 12px; font-size: 0.8rem; color: var(--muted); }
.legend-swatch { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: middle; }
@media (max-width: 600px) {
  body { padding: 12px; }
  .stat-value { font-size: 1.4rem; }
}
"""

_JS = """
const data = JSON.parse(document.getElementById('audit-data').textContent);

function fmtMoney(n) {
  return '$' + Number(n).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

function renderHeroStats() {
  const el = document.getElementById('hero-stats');
  const errors = data.flags.filter(f => f.severity === 'error').length;
  const warnings = data.flags.filter(f => f.severity === 'warning').length;
  const infos = data.flags.filter(f => f.severity === 'info').length;
  const overcommitted = new Set(data.windows.map(w => w.person_name)).size;
  const stats = [
    ['Grants Audited', data.summaries.length],
    ['Total Flags', data.flags.length],
    ['Errors', errors],
    ['Warnings', warnings],
    ['Info', infos],
    ['People Overcommitted', overcommitted],
  ];
  stats.forEach(([label, value]) => {
    const card = document.createElement('div');
    card.className = 'stat-card';
    const v = document.createElement('div');
    v.className = 'stat-value';
    v.textContent = String(value);
    const l = document.createElement('div');
    l.className = 'stat-label';
    l.textContent = label;
    card.appendChild(v);
    card.appendChild(l);
    el.appendChild(card);
  });
}

function renderAiBriefing() {
  if (!data.ai_briefing) return;
  document.getElementById('ai-briefing-section').hidden = false;
  document.getElementById('ai-briefing-text').textContent = data.ai_briefing;
}

let budgetSort = {key: 'grant_id', dir: 1};
function renderBudgetTable() {
  const tbody = document.getElementById('budget-tbody');
  tbody.innerHTML = '';
  const query = document.getElementById('budget-search').value.toLowerCase();
  let rows = data.summaries.filter(r =>
    r.grant_id.toLowerCase().includes(query) || r.grant_name.toLowerCase().includes(query)
  );
  rows = rows.slice().sort((a, b) => {
    const av = a[budgetSort.key], bv = b[budgetSort.key];
    if (typeof av === 'number') return (av - bv) * budgetSort.dir;
    return String(av).localeCompare(String(bv)) * budgetSort.dir;
  });
  rows.forEach(r => {
    const tr = document.createElement('tr');
    [
      r.grant_id, r.grant_name, r.fiscal_year,
      fmtMoney(r.direct_total), fmtMoney(r.mtdc),
      fmtMoney(r.expected_indirect), fmtMoney(r.stated_indirect), fmtMoney(r.total),
    ].forEach(val => {
      const td = document.createElement('td');
      td.textContent = val;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

let activeSeverities = new Set(['error', 'warning', 'info']);
let flagsSort = {key: 'severity', dir: 1};
function renderSeverityFilters() {
  const el = document.getElementById('severity-filters');
  ['error', 'warning', 'info'].forEach(sev => {
    const chip = document.createElement('div');
    chip.className = 'chip active';
    chip.textContent = sev;
    chip.addEventListener('click', () => {
      if (activeSeverities.has(sev)) {
        activeSeverities.delete(sev);
        chip.classList.remove('active');
      } else {
        activeSeverities.add(sev);
        chip.classList.add('active');
      }
      renderFlagsTable();
    });
    el.appendChild(chip);
  });
}

function renderFlagsTable() {
  const tbody = document.getElementById('flags-tbody');
  tbody.innerHTML = '';
  const query = document.getElementById('flags-search').value.toLowerCase();
  let rows = data.flags.filter(f =>
    activeSeverities.has(f.severity) &&
    (f.message.toLowerCase().includes(query) ||
     f.grant_id.toLowerCase().includes(query) ||
     f.person_name.toLowerCase().includes(query) ||
     f.code.toLowerCase().includes(query))
  );
  rows = rows.slice().sort((a, b) => {
    const av = a[flagsSort.key], bv = b[flagsSort.key];
    return String(av).localeCompare(String(bv)) * flagsSort.dir;
  });
  rows.forEach(f => {
    const tr = document.createElement('tr');

    const sevTd = document.createElement('td');
    const badge = document.createElement('span');
    badge.className = 'badge badge-' + f.severity;
    badge.textContent = f.severity;
    sevTd.appendChild(badge);
    tr.appendChild(sevTd);

    [f.code, f.message, f.grant_id, f.person_name].forEach(val => {
      const td = document.createElement('td');
      td.textContent = val;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

function attachSortHandlers(tableId, sortState, renderFn) {
  document.querySelectorAll('#' + tableId + ' th[data-key]').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.key;
      if (sortState.key === key) {
        sortState.dir *= -1;
      } else {
        sortState.key = key;
        sortState.dir = 1;
      }
      renderFn();
    });
  });
}

const GRANT_COLORS = ['#5eb0ff', '#6bcf9f', '#ffc857', '#c792ea', '#ff8a65', '#4dd0e1'];
function colorForGrant(grantId, allGrantIds) {
  const idx = allGrantIds.indexOf(grantId) % GRANT_COLORS.length;
  return GRANT_COLORS[idx];
}

function renderTimeline() {
  const canvas = document.getElementById('timeline-canvas');
  const ctx = canvas.getContext('2d');
  const lines = data.effort_lines;
  const legend = document.getElementById('timeline-legend');

  if (lines.length === 0) {
    ctx.fillStyle = '#8b93a3';
    ctx.font = '14px sans-serif';
    ctx.fillText('No effort data to display', 20, 30);
    return;
  }

  const people = Array.from(new Set(lines.map(l => l.person_name)));
  const grantIds = Array.from(new Set(lines.map(l => l.grant_id)));

  const allDates = lines.flatMap(l => [new Date(l.period_start), new Date(l.period_end)]);
  const minDate = new Date(Math.min(...allDates));
  const maxDate = new Date(Math.max(...allDates));
  const spanMs = Math.max(1, maxDate - minDate);

  const marginLeft = 140, marginTop = 20, rowHeight = 50;
  const plotWidth = canvas.width - marginLeft - 20;
  canvas.height = marginTop + people.length * rowHeight + 30;

  function xForDate(d) {
    return marginLeft + ((d - minDate) / spanMs) * plotWidth;
  }

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#0f1115';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  people.forEach((person, i) => {
    const y = marginTop + i * rowHeight;
    ctx.fillStyle = '#e6e9ef';
    ctx.font = '13px sans-serif';
    ctx.fillText(person, 8, y + rowHeight / 2 + 4);

    ctx.strokeStyle = '#262c37';
    ctx.beginPath();
    ctx.moveTo(marginLeft, y + rowHeight / 2);
    ctx.lineTo(marginLeft + plotWidth, y + rowHeight / 2);
    ctx.stroke();

    const personLines = lines.filter(l => l.person_name === person);
    personLines.forEach((l, li) => {
      const x1 = xForDate(new Date(l.period_start));
      const x2 = xForDate(new Date(l.period_end));
      const barY = y + 6 + (li % 3) * 8;
      ctx.fillStyle = colorForGrant(l.grant_id, grantIds);
      ctx.fillRect(x1, barY, Math.max(2, x2 - x1), 6);
    });

    const personWindows = data.windows.filter(w => w.person_name === person);
    personWindows.forEach(w => {
      const x1 = xForDate(new Date(w.start));
      const x2 = xForDate(new Date(w.end));
      ctx.fillStyle = 'rgba(255,107,107,0.25)';
      ctx.fillRect(x1, y, Math.max(2, x2 - x1), rowHeight - 4);
      ctx.strokeStyle = '#ff6b6b';
      ctx.strokeRect(x1, y, Math.max(2, x2 - x1), rowHeight - 4);
    });
  });

  grantIds.forEach(gid => {
    const item = document.createElement('span');
    const swatch = document.createElement('span');
    swatch.className = 'legend-swatch';
    swatch.style.background = colorForGrant(gid, grantIds);
    item.appendChild(swatch);
    item.appendChild(document.createTextNode(gid));
    legend.appendChild(item);
  });
  const overCommitItem = document.createElement('span');
  const overSwatch = document.createElement('span');
  overSwatch.className = 'legend-swatch';
  overSwatch.style.background = '#ff6b6b';
  overCommitItem.appendChild(overSwatch);
  overCommitItem.appendChild(document.createTextNode('Overcommitment window'));
  legend.appendChild(overCommitItem);
}

renderHeroStats();
renderAiBriefing();
renderSeverityFilters();
renderBudgetTable();
renderFlagsTable();
renderTimeline();
attachSortHandlers('budget-table', budgetSort, renderBudgetTable);
attachSortHandlers('flags-table', flagsSort, renderFlagsTable);
document.getElementById('budget-search').addEventListener('input', renderBudgetTable);
document.getElementById('flags-search').addEventListener('input', renderFlagsTable);
"""
