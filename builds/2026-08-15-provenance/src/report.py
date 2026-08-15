"""Self-contained dark-mode HTML batch report.

Row data is delivered to the page as a JSON payload inside a
``<script type="application/json">`` tag and consumed via
``JSON.parse(...textContent)`` — every DOM node the table builds uses
``createElement``/``textContent``, never ``innerHTML``, so a business name
or note containing markup can never execute in the browser. The JSON
payload itself has every ``</`` sequence escaped to ``<\\/`` so a value
like ``</script><script>...`` can't prematurely close the data tag either.
"""

from __future__ import annotations

import json

_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Provenance — Batch Ownership Report</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {
    --bg: #0f1115; --panel: #171a21; --border: #2a2f3a; --text: #e6e8ec;
    --muted: #9aa2b1; --canadian: #2fae66; --foreign: #d9534f; --uncertain: #e0a53a;
    --accent: #5b8def;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--text); font-family: -apple-system, Segoe UI, Roboto, sans-serif; }
  header { padding: 24px; border-bottom: 1px solid var(--border); }
  h1 { margin: 0 0 4px; font-size: 1.4rem; }
  .sub { color: var(--muted); font-size: 0.9rem; }
  .stats { display: flex; gap: 12px; padding: 16px 24px; flex-wrap: wrap; }
  .stat { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 10px 16px; min-width: 110px; }
  .stat .n { font-size: 1.4rem; font-weight: 700; }
  .stat .l { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; }
  .controls { display: flex; gap: 8px; padding: 0 24px 16px; flex-wrap: wrap; align-items: center; }
  input[type="search"] { background: var(--panel); border: 1px solid var(--border); color: var(--text); padding: 8px 12px; border-radius: 6px; flex: 1; min-width: 180px; }
  button.filter { background: var(--panel); border: 1px solid var(--border); color: var(--text); padding: 8px 12px; border-radius: 6px; cursor: pointer; }
  button.filter.active { border-color: var(--accent); color: var(--accent); }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 10px 14px; border-bottom: 1px solid var(--border); font-size: 0.9rem; vertical-align: top; }
  th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
  .badge.canadian { background: rgba(47,174,102,0.18); color: var(--canadian); }
  .badge.foreign { background: rgba(217,83,79,0.18); color: var(--foreign); }
  .badge.uncertain { background: rgba(224,165,58,0.18); color: var(--uncertain); }
  .empty { padding: 40px 24px; color: var(--muted); text-align: center; }
  .main-wrap { overflow-x: auto; }
</style>
</head>
<body>
<header>
  <h1>Provenance — Batch Ownership Report</h1>
  <div class="sub">Generated locally. All classification data stays on this page.</div>
</header>
<div class="stats" id="stats"></div>
<div class="controls">
  <input type="search" id="search" placeholder="Search business name or evidence...">
  <button class="filter active" data-verdict="all">All</button>
  <button class="filter" data-verdict="canadian">Canadian</button>
  <button class="filter" data-verdict="foreign">Foreign</button>
  <button class="filter" data-verdict="uncertain">Uncertain</button>
</div>
<div class="main-wrap">
  <table id="table">
    <thead>
      <tr>
        <th>Business</th><th>Verdict</th><th>Confidence</th><th>Evidence</th><th>QID</th><th>AI Note</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
</div>
<div class="empty" id="empty" hidden>No rows match your filters.</div>

<script type="application/json" id="report-data">__JSON_PAYLOAD__</script>
<script>
(function () {
  var data = JSON.parse(document.getElementById('report-data').textContent);
  var rows = data.rows;
  var stats = data.stats;

  var statsEl = document.getElementById('stats');
  var statDefs = [
    ['total', 'Total'], ['canadian', 'Canadian'], ['foreign', 'Foreign'],
    ['uncertain', 'Uncertain'], ['cache_hits', 'Cache Hits'], ['cache_misses', 'Cache Misses']
  ];
  statDefs.forEach(function (def) {
    var key = def[0], label = def[1];
    var box = document.createElement('div');
    box.className = 'stat';
    var n = document.createElement('div');
    n.className = 'n';
    n.textContent = String(stats[key] != null ? stats[key] : 0);
    var l = document.createElement('div');
    l.className = 'l';
    l.textContent = label;
    box.appendChild(n);
    box.appendChild(l);
    statsEl.appendChild(box);
  });

  var tbody = document.getElementById('tbody');
  var emptyEl = document.getElementById('empty');
  var searchInput = document.getElementById('search');
  var filterButtons = document.querySelectorAll('button.filter');
  var activeVerdict = 'all';

  function badge(verdict) {
    var span = document.createElement('span');
    span.className = 'badge ' + verdict;
    span.textContent = verdict;
    return span;
  }

  function renderRows() {
    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
    var term = searchInput.value.trim().toLowerCase();
    var shown = 0;
    rows.forEach(function (row) {
      if (activeVerdict !== 'all' && row.verdict !== activeVerdict) return;
      var haystack = ((row.name || '') + ' ' + (row.evidence || '')).toLowerCase();
      if (term && haystack.indexOf(term) === -1) return;
      shown += 1;

      var tr = document.createElement('tr');

      var nameTd = document.createElement('td');
      nameTd.textContent = row.name || '';
      tr.appendChild(nameTd);

      var verdictTd = document.createElement('td');
      verdictTd.appendChild(badge(row.verdict));
      tr.appendChild(verdictTd);

      var confTd = document.createElement('td');
      confTd.textContent = (typeof row.confidence === 'number') ? row.confidence.toFixed(2) : '';
      tr.appendChild(confTd);

      var evTd = document.createElement('td');
      evTd.textContent = row.evidence || '';
      tr.appendChild(evTd);

      var qidTd = document.createElement('td');
      qidTd.textContent = row.wikidata_qid || '';
      tr.appendChild(qidTd);

      var aiTd = document.createElement('td');
      aiTd.textContent = row.ai_note || '';
      tr.appendChild(aiTd);

      tbody.appendChild(tr);
    });
    emptyEl.hidden = shown !== 0;
  }

  searchInput.addEventListener('input', renderRows);
  filterButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      filterButtons.forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      activeVerdict = btn.getAttribute('data-verdict');
      renderRows();
    });
  });

  renderRows();
})();
</script>
</body>
</html>
"""


def render_html(rows: list[dict], stats: dict) -> str:
    """Render the batch report. ``rows`` values must be JSON-serializable."""
    payload = json.dumps({"rows": rows, "stats": stats})
    safe_payload = payload.replace("</", "<\\/")
    return _TEMPLATE.replace("__JSON_PAYLOAD__", safe_payload)
