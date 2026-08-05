"""Self-contained dark-mode HTML dashboard renderer for Impact Ledger.

All dynamic data is passed to the browser as a JSON blob (safely escaped against
premature </script> closure) and every DOM node the client builds from it uses
createElement/textContent — never innerHTML from a data-derived string — so a
malicious title/venue/AI-note string can never execute as markup.
"""

from __future__ import annotations

import json
from typing import Any

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


def _safe_json_script(data: dict[str, Any]) -> str:
    """JSON-encode data for embedding inside a <script type="application/json"> tag."""
    return json.dumps(data).replace("</", "<\\/")


def render_dashboard(
    author: dict[str, Any],
    trend: list[dict[str, Any]],
    papers: list[dict[str, Any]],
    rising: list[dict[str, Any]],
    ai_notes: dict[str, str],
) -> str:
    payload = {
        "author": author,
        "trend": trend,
        "papers": papers,
        "rising": rising,
        "aiNotes": ai_notes,
    }
    data_json = _safe_json_script(payload)

    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Impact Ledger — {author.get('display_name', 'Unknown')}</title>
<style>
  :root {{
    --bg: #0f1115;
    --panel: #171a21;
    --border: #2a2e38;
    --text: #e6e8ec;
    --muted: #9aa1ad;
    --accent: #5eb0ff;
    --rising: #4ade80;
    --space-1: 8px;
    --space-2: 16px;
    --space-3: 24px;
    --space-4: 32px;
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
    padding: var(--space-3) var(--space-3) var(--space-2);
    border-bottom: 1px solid var(--border);
  }}
  header h1 {{ margin: 0 0 4px; font-size: 1.4rem; }}
  header p {{ margin: 0; color: var(--muted); font-size: 0.9rem; }}
  main {{
    max-width: 1100px;
    margin: 0 auto;
    padding: var(--space-3);
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }}
  .stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: var(--space-2);
  }}
  .stat-tile {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: var(--space-2);
  }}
  .stat-tile .value {{ font-size: 1.6rem; font-weight: 600; }}
  .stat-tile .label {{ color: var(--muted); font-size: 0.8rem; margin-top: 4px; }}
  section {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: var(--space-3);
  }}
  section h2 {{ margin-top: 0; font-size: 1.1rem; }}
  .muted-note {{ color: var(--muted); font-size: 0.9rem; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th, td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 500; cursor: pointer; user-select: none; }}
  tr:hover td {{ background: rgba(255,255,255,0.02); }}
  input[type="search"] {{
    width: 100%;
    padding: 8px 10px;
    margin-bottom: var(--space-2);
    background: #10131a;
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
  }}
  .rising-card {{
    border: 1px solid var(--border);
    border-left: 3px solid var(--rising);
    border-radius: 8px;
    padding: var(--space-2);
    margin-bottom: var(--space-2);
  }}
  .rising-card .title {{ font-weight: 600; margin-bottom: 4px; }}
  .rising-card .delta {{ color: var(--rising); font-size: 0.85rem; margin-bottom: 6px; }}
  .rising-card .note {{ color: var(--text); font-size: 0.9rem; }}
  .concepts {{ display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }}
  .concept-chip {{
    background: rgba(94,176,255,0.12);
    color: var(--accent);
    border-radius: 999px;
    padding: 2px 8px;
    font-size: 0.75rem;
  }}
  canvas {{ max-width: 100%; }}
  @media (prefers-color-scheme: light) {{
    :root:not([data-theme="dark"]) {{
      --bg: #f7f8fa; --panel: #ffffff; --border: #dfe3e8; --text: #1a1d23; --muted: #6b7280;
    }}
  }}
</style>
</head>
<body>
<header>
  <h1>Impact Ledger</h1>
  <p class="muted-note" id="subtitle"></p>
</header>
<main>
  <div class="stats" id="stats"></div>

  <section>
    <h2>Citation Growth</h2>
    <div id="trend-container">
      <canvas id="trend-chart" height="90"></canvas>
    </div>
  </section>

  <section>
    <h2>Rising Papers</h2>
    <div id="rising-container"></div>
  </section>

  <section>
    <h2>All Papers</h2>
    <input type="search" id="paper-search" placeholder="Search by title, venue, or concept...">
    <table id="paper-table">
      <thead>
        <tr>
          <th data-key="title">Title</th>
          <th data-key="publication_year">Year</th>
          <th data-key="host_venue">Venue</th>
          <th data-key="cited_by_count">Citations</th>
          <th>Concepts</th>
        </tr>
      </thead>
      <tbody id="paper-tbody"></tbody>
    </table>
  </section>
</main>

<script type="application/json" id="impact-ledger-data">{data_json}</script>
<script src="{CHART_JS_CDN}"></script>
<script>
(function () {{
  var data = JSON.parse(document.getElementById('impact-ledger-data').textContent);

  function el(tag, opts) {{
    var node = document.createElement(tag);
    opts = opts || {{}};
    if (opts.className) node.className = opts.className;
    if (opts.text !== undefined) node.textContent = opts.text;
    return node;
  }}

  // Header subtitle
  var subtitle = document.getElementById('subtitle');
  subtitle.textContent = data.author.display_name
    ? (data.author.display_name + ' — last synced ' + (data.author.last_synced || 'never'))
    : 'No author synced yet';

  // Stat tiles
  var stats = document.getElementById('stats');
  var tiles = [
    ['Total Citations', data.author.cited_by_count],
    ['Works Tracked', data.author.works_count],
    ['h-index', data.author.h_index],
    ['i10-index', data.author.i10_index]
  ];
  tiles.forEach(function (pair) {{
    var tile = el('div', {{ className: 'stat-tile' }});
    var value = el('div', {{ className: 'value', text: (pair[1] === null || pair[1] === undefined) ? '—' : pair[1] }});
    var label = el('div', {{ className: 'label', text: pair[0] }});
    tile.appendChild(value);
    tile.appendChild(label);
    stats.appendChild(tile);
  }});

  // Citation trend chart (or fallback message/table)
  var trendContainer = document.getElementById('trend-container');
  function renderTrendFallback() {{
    trendContainer.innerHTML = '';
    if (data.trend.length < 2) {{
      trendContainer.appendChild(el('p', {{
        className: 'muted-note',
        text: 'Not enough history yet — sync again on a later date to see a citation growth trend.'
      }}));
      return;
    }}
    var table = el('table');
    var thead = el('thead');
    var headRow = el('tr');
    headRow.appendChild(el('th', {{ text: 'Date' }}));
    headRow.appendChild(el('th', {{ text: 'Total Citations' }}));
    thead.appendChild(headRow);
    table.appendChild(thead);
    var tbody = el('tbody');
    data.trend.forEach(function (point) {{
      var row = el('tr');
      row.appendChild(el('td', {{ text: point.sync_date }}));
      row.appendChild(el('td', {{ text: point.total_citations }}));
      tbody.appendChild(row);
    }});
    table.appendChild(tbody);
    trendContainer.appendChild(table);
  }}

  if (data.trend.length < 2) {{
    renderTrendFallback();
  }} else if (typeof Chart === 'undefined') {{
    renderTrendFallback();
  }} else {{
    var ctx = document.getElementById('trend-chart').getContext('2d');
    new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: data.trend.map(function (p) {{ return p.sync_date; }}),
        datasets: [{{
          label: 'Total citations',
          data: data.trend.map(function (p) {{ return p.total_citations; }}),
          borderColor: '#5eb0ff',
          backgroundColor: 'rgba(94,176,255,0.15)',
          tension: 0.2,
          fill: true
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{ y: {{ beginAtZero: true }} }}
      }}
    }});
  }}

  // Rising papers
  var risingContainer = document.getElementById('rising-container');
  if (data.rising.length === 0) {{
    risingContainer.appendChild(el('p', {{
      className: 'muted-note',
      text: 'No rising-paper data yet — this appears after at least two syncs on different dates.'
    }}));
  }} else {{
    data.rising.forEach(function (paper) {{
      var card = el('div', {{ className: 'rising-card' }});
      card.appendChild(el('div', {{ className: 'title', text: paper.title }}));
      card.appendChild(el('div', {{
        className: 'delta',
        text: '+' + paper.velocity + ' citations (' + paper.previous_cited_by_count + ' → ' + paper.cited_by_count + ')'
      }}));
      var note = data.aiNotes[paper.work_id];
      if (note) {{
        card.appendChild(el('div', {{ className: 'note', text: note }}));
      }}
      risingContainer.appendChild(card);
    }});
  }}

  // Paper table
  var tbody = document.getElementById('paper-tbody');
  function renderPapers(list) {{
    tbody.innerHTML = '';
    list.forEach(function (paper) {{
      var row = el('tr');
      row.appendChild(el('td', {{ text: paper.title }}));
      row.appendChild(el('td', {{ text: paper.publication_year || '—' }}));
      row.appendChild(el('td', {{ text: paper.host_venue || '—' }}));
      row.appendChild(el('td', {{ text: paper.cited_by_count }}));
      var conceptsCell = el('td');
      var conceptsWrap = el('div', {{ className: 'concepts' }});
      (paper.concepts || []).slice(0, 4).forEach(function (concept) {{
        conceptsWrap.appendChild(el('span', {{ className: 'concept-chip', text: concept }}));
      }});
      conceptsCell.appendChild(conceptsWrap);
      row.appendChild(conceptsCell);
      tbody.appendChild(row);
    }});
  }}
  renderPapers(data.papers);

  var searchBox = document.getElementById('paper-search');
  searchBox.addEventListener('input', function () {{
    var query = searchBox.value.toLowerCase();
    var filtered = data.papers.filter(function (paper) {{
      var haystack = [paper.title, paper.host_venue].concat(paper.concepts || []).join(' ').toLowerCase();
      return haystack.indexOf(query) !== -1;
    }});
    renderPapers(filtered);
  }});

  var sortState = {{ key: null, dir: 1 }};
  document.querySelectorAll('#paper-table th[data-key]').forEach(function (th) {{
    th.addEventListener('click', function () {{
      var key = th.getAttribute('data-key');
      sortState.dir = (sortState.key === key) ? -sortState.dir : 1;
      sortState.key = key;
      var sorted = data.papers.slice().sort(function (a, b) {{
        var av = a[key] === null || a[key] === undefined ? '' : a[key];
        var bv = b[key] === null || b[key] === undefined ? '' : b[key];
        if (av < bv) return -1 * sortState.dir;
        if (av > bv) return 1 * sortState.dir;
        return 0;
      }});
      renderPapers(sorted);
    }});
  }});
}})();
</script>
</body>
</html>
"""
