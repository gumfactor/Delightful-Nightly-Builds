"""Self-contained dark-mode HTML dashboard renderer.

All row/field data is embedded as JSON inside a <script type="application/json">
tag and rendered client-side via createElement/textContent — never via
innerHTML string concatenation — so arbitrary CSV field content (including a
deliberately hostile business name) can never execute as script or markup.
"""
from __future__ import annotations

import json

CHART_JS_CDN_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


def render_html_report(report: dict, source_filename: str) -> str:
    # A field value containing the literal substring "</script" would
    # otherwise close the surrounding <script type="application/json"> tag
    # early, regardless of it being inside a JSON string literal — escape
    # every "</" so embedded field text (e.g. a hostile business name) can
    # never break out of the data block.
    data_json = json.dumps(report).replace("</", "<\\/")
    return _TEMPLATE.format(
        source_filename=_escape_for_html_text(source_filename),
        data_json=data_json,
        chart_cdn=CHART_JS_CDN_URL,
    )


def _escape_for_html_text(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Canada List CSV Quality Report — {source_filename}</title>
<style>
  :root {{
    --bg: #0f1420;
    --bg-panel: #161d2e;
    --bg-tile: #1c2438;
    --border: #2a3348;
    --text: #e6ebf5;
    --text-dim: #9aa7c0;
    --accent: #5eb0ff;
    --error: #ff6b6b;
    --warning: #ffb84d;
    --ok: #57d38c;
    --radius: 10px;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
  }}
  header {{
    padding: 1.5rem 1.25rem;
    border-bottom: 1px solid var(--border);
  }}
  header h1 {{ margin: 0 0 0.25rem; font-size: 1.4rem; }}
  header p {{ margin: 0; color: var(--text-dim); font-size: 0.9rem; }}
  main {{ padding: 1.25rem; max-width: 1200px; margin: 0 auto; }}
  .tiles {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }}
  .tile {{
    background: var(--bg-tile);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
  }}
  .tile .value {{ font-size: 1.8rem; font-weight: 700; }}
  .tile .label {{ color: var(--text-dim); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.03em; }}
  .tile.error .value {{ color: var(--error); }}
  .tile.warning .value {{ color: var(--warning); }}
  .tile.ok .value {{ color: var(--ok); }}
  section {{
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 1.5rem;
    overflow-x: auto;
  }}
  section h2 {{ margin-top: 0; font-size: 1.1rem; }}
  .controls {{ display: flex; gap: 0.5rem; margin-bottom: 0.75rem; flex-wrap: wrap; }}
  input[type="text"] {{
    background: var(--bg-tile);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.4rem 0.6rem;
    border-radius: 6px;
    min-width: 200px;
  }}
  button.filter-btn {{
    background: var(--bg-tile);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.4rem 0.75rem;
    border-radius: 6px;
    cursor: pointer;
  }}
  button.filter-btn.active {{ border-color: var(--accent); color: var(--accent); }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; }}
  th, td {{ text-align: left; padding: 0.45rem 0.6rem; border-bottom: 1px solid var(--border); white-space: nowrap; }}
  th {{ cursor: pointer; color: var(--text-dim); user-select: none; position: sticky; top: 0; background: var(--bg-panel); }}
  th:hover {{ color: var(--text); }}
  tr.action-drop td.action {{ color: var(--error); }}
  tr.action-review td.action {{ color: var(--warning); }}
  tr.action-keep td.action {{ color: var(--ok); }}
  .cluster-card {{
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.75rem;
    background: var(--bg-tile);
  }}
  .cluster-card .meta {{ color: var(--text-dim); font-size: 0.8rem; margin-bottom: 0.5rem; }}
  .cluster-row {{ padding: 0.25rem 0; border-top: 1px dashed var(--border); }}
  .cluster-row:first-of-type {{ border-top: none; }}
  #fallback-table {{ display: none; }}
  canvas {{ max-height: 260px; }}
  footer {{ text-align: center; color: var(--text-dim); font-size: 0.75rem; padding: 1.5rem; }}
</style>
</head>
<body>
<header>
  <h1>Canada List CSV Quality Report</h1>
  <p>Source file: {source_filename}</p>
</header>
<main>
  <div class="tiles" id="tiles"></div>

  <section>
    <h2>Issues by type</h2>
    <canvas id="issueChart" height="90"></canvas>
    <div id="fallback-table"></div>
  </section>

  <section>
    <h2>Rows</h2>
    <div class="controls">
      <input type="text" id="searchBox" placeholder="Search rows...">
      <button class="filter-btn active" data-filter="all">All</button>
      <button class="filter-btn" data-filter="drop">Drop</button>
      <button class="filter-btn" data-filter="review">Review</button>
      <button class="filter-btn" data-filter="keep">Keep</button>
    </div>
    <table id="rowTable">
      <thead><tr id="rowTableHead"></tr></thead>
      <tbody id="rowTableBody"></tbody>
    </table>
  </section>

  <section>
    <h2>Duplicate clusters</h2>
    <div id="clusters"></div>
  </section>
</main>
<footer>Generated by the Canada List CSV Quality Inspector.</footer>

<script id="qc-data" type="application/json">{data_json}</script>
<script src="{chart_cdn}"></script>
<script>
(function() {{
  var report = JSON.parse(document.getElementById('qc-data').textContent);
  var summary = report.summary || {{}};

  function el(tag, attrs, text) {{
    var node = document.createElement(tag);
    if (attrs) {{
      for (var key in attrs) {{
        node.setAttribute(key, attrs[key]);
      }}
    }}
    if (text !== undefined && text !== null) {{
      node.textContent = String(text);
    }}
    return node;
  }}

  function renderTiles() {{
    var tiles = document.getElementById('tiles');
    var specs = [
      ['Total rows', summary.total_rows, ''],
      ['Errors', summary.error_rows, 'error'],
      ['Warnings', summary.warning_rows, 'warning'],
      ['Clean rows', summary.clean_rows, 'ok'],
      ['Duplicate clusters', summary.duplicate_cluster_count, '']
    ];
    specs.forEach(function(spec) {{
      var tile = el('div', {{ 'class': 'tile ' + spec[2] }});
      tile.appendChild(el('div', {{ 'class': 'value' }}, spec[1]));
      tile.appendChild(el('div', {{ 'class': 'label' }}, spec[0]));
      tiles.appendChild(tile);
    }});
  }}

  function issueCounts() {{
    var counts = {{}};
    (report.rows || []).forEach(function(row) {{
      (row.flags || []).forEach(function(flag) {{
        counts[flag.code] = (counts[flag.code] || 0) + 1;
      }});
    }});
    return counts;
  }}

  function renderChart() {{
    var counts = issueCounts();
    var labels = Object.keys(counts);
    var values = labels.map(function(l) {{ return counts[l]; }});

    if (labels.length === 0) {{
      document.getElementById('issueChart').style.display = 'none';
      var empty = el('p', null, 'No issues found — every row passed all checks.');
      document.getElementById('fallback-table').appendChild(empty);
      document.getElementById('fallback-table').style.display = 'block';
      return;
    }}

    if (typeof Chart === 'undefined') {{
      renderFallbackTable(labels, values);
      return;
    }}
    try {{
      var ctx = document.getElementById('issueChart').getContext('2d');
      new Chart(ctx, {{
        type: 'bar',
        data: {{
          labels: labels,
          datasets: [{{ label: 'Occurrences', data: values, backgroundColor: '#5eb0ff' }}]
        }},
        options: {{
          responsive: true,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9aa7c0' }}, grid: {{ color: '#2a3348' }} }},
            y: {{ ticks: {{ color: '#9aa7c0' }}, grid: {{ color: '#2a3348' }}, beginAtZero: true }}
          }}
        }}
      }});
    }} catch (err) {{
      renderFallbackTable(labels, values);
    }}
  }}

  function renderFallbackTable(labels, values) {{
    document.getElementById('issueChart').style.display = 'none';
    var container = document.getElementById('fallback-table');
    var table = el('table');
    var headRow = el('tr');
    headRow.appendChild(el('th', null, 'Issue code'));
    headRow.appendChild(el('th', null, 'Count'));
    table.appendChild(headRow);
    labels.forEach(function(label, i) {{
      var row = el('tr');
      row.appendChild(el('td', null, label));
      row.appendChild(el('td', null, values[i]));
      table.appendChild(row);
    }});
    container.appendChild(table);
    container.style.display = 'block';
  }}

  var allColumns = (report.header || []);
  var extraCols = ['QC_Flags', 'Recommended_Action'];

  function renderRowTableHead() {{
    var headRow = document.getElementById('rowTableHead');
    allColumns.concat(extraCols).forEach(function(col) {{
      var th = el('th', {{ 'data-col': col }}, col);
      th.addEventListener('click', function() {{ sortBy(col); }});
      headRow.appendChild(th);
    }});
  }}

  var currentFilter = 'all';
  var currentSearch = '';
  var sortState = {{ col: null, dir: 1 }};

  function rowMatchesFilter(row) {{
    if (currentFilter !== 'all' && row.recommended_action !== currentFilter) return false;
    if (!currentSearch) return true;
    var haystack = JSON.stringify(row.fields).toLowerCase();
    return haystack.indexOf(currentSearch.toLowerCase()) !== -1;
  }}

  function renderRowTableBody() {{
    var body = document.getElementById('rowTableBody');
    body.innerHTML = '';
    var rows = (report.rows || []).filter(rowMatchesFilter);
    if (sortState.col) {{
      rows = rows.slice().sort(function(a, b) {{
        var av = sortState.col === 'QC_Flags' ? a.flags.length
          : sortState.col === 'Recommended_Action' ? a.recommended_action
          : (a.fields[sortState.col] || '');
        var bv = sortState.col === 'QC_Flags' ? b.flags.length
          : sortState.col === 'Recommended_Action' ? b.recommended_action
          : (b.fields[sortState.col] || '');
        if (av < bv) return -1 * sortState.dir;
        if (av > bv) return 1 * sortState.dir;
        return 0;
      }});
    }}
    rows.forEach(function(row) {{
      var tr = el('tr', {{ 'class': 'action-' + row.recommended_action }});
      allColumns.forEach(function(col) {{
        tr.appendChild(el('td', null, row.fields[col] !== undefined ? row.fields[col] : ''));
      }});
      var flagsSummary = row.flags.map(function(f) {{ return f.severity + ':' + f.code; }}).join('; ');
      tr.appendChild(el('td', null, flagsSummary || '—'));
      tr.appendChild(el('td', {{ 'class': 'action' }}, row.recommended_action));
      body.appendChild(tr);
    }});
  }}

  function sortBy(col) {{
    if (sortState.col === col) {{
      sortState.dir *= -1;
    }} else {{
      sortState.col = col;
      sortState.dir = 1;
    }}
    renderRowTableBody();
  }}

  function renderClusters() {{
    var container = document.getElementById('clusters');
    var clusters = report.duplicate_clusters || [];
    if (clusters.length === 0) {{
      container.appendChild(el('p', null, 'No duplicate clusters detected.'));
      return;
    }}
    var nameCol = allColumns.filter(function(c) {{ return c.toLowerCase() === 'business_name'; }})[0];
    var provinceCol = allColumns.filter(function(c) {{ return c.toLowerCase() === 'province'; }})[0];
    var websiteCol = allColumns.filter(function(c) {{ return c.toLowerCase() === 'website'; }})[0];

    var rowsByIndex = {{}};
    (report.rows || []).forEach(function(r) {{ rowsByIndex[r.row_index] = r; }});

    clusters.forEach(function(cluster) {{
      var card = el('div', {{ 'class': 'cluster-card' }});
      var metaText = 'Match basis: ' + cluster.match_basis + ' — similarity ' +
        (cluster.similarity_score * 100).toFixed(0) + '%';
      if (cluster.ai_confirmed === true) metaText += ' — AI confirmed duplicate';
      if (cluster.ai_confirmed === false) metaText += ' — AI says likely NOT duplicate';
      card.appendChild(el('div', {{ 'class': 'meta' }}, metaText));
      if (cluster.ai_reasoning) {{
        card.appendChild(el('div', {{ 'class': 'meta' }}, 'AI note: ' + cluster.ai_reasoning));
      }}
      cluster.row_indices.forEach(function(idx) {{
        var row = rowsByIndex[idx];
        if (!row) return;
        var line = 'Row ' + idx + ': ' +
          (nameCol ? (row.fields[nameCol] || '') : '') +
          (provinceCol ? ' (' + (row.fields[provinceCol] || '') + ')' : '') +
          (websiteCol ? ' — ' + (row.fields[websiteCol] || '') : '');
        card.appendChild(el('div', {{ 'class': 'cluster-row' }}, line));
      }});
      container.appendChild(card);
    }});
  }}

  document.getElementById('searchBox').addEventListener('input', function(e) {{
    currentSearch = e.target.value;
    renderRowTableBody();
  }});
  Array.prototype.forEach.call(document.querySelectorAll('.filter-btn'), function(btn) {{
    btn.addEventListener('click', function() {{
      currentFilter = btn.getAttribute('data-filter');
      Array.prototype.forEach.call(document.querySelectorAll('.filter-btn'), function(b) {{
        b.classList.remove('active');
      }});
      btn.classList.add('active');
      renderRowTableBody();
    }});
  }});

  renderTiles();
  renderChart();
  renderRowTableHead();
  renderRowTableBody();
  renderClusters();
}})();
</script>
</body>
</html>
"""
