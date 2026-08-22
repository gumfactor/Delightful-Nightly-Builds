"""Self-contained dark-mode HTML dashboard generator.

All dynamic data (domain labels, renewal titles, registrar names, AI
briefing text) is untrusted user- or network-sourced text. It is delivered
to the page as a JSON payload inside a <script type="application/json"> tag
and read back with JSON.parse(el.textContent) — never interpolated into the
HTML string directly, and never inserted into the DOM via innerHTML. The
JSON text itself has "</" escaped to "<\\/" so an embedded "</script>"
sequence in, say, a malicious domain label can never prematurely close the
surrounding <script> tag (a real bug class: raw html.escape() would corrupt
the JSON once read via .textContent, since <script> content is HTML raw
text and never HTML-entity-decoded).
"""

from __future__ import annotations

import json
from typing import Any


def _safe_json_for_script_tag(data: Any) -> str:
    return json.dumps(data).replace("</", "<\\/")


def render_dashboard(
    items: list[dict[str, Any]],
    briefing_text: str,
    used_ai: bool,
    domain_histories: dict[str, list[dict[str, Any]]],
    generated_at: str,
) -> str:
    """Render the full dashboard as a single self-contained HTML string.

    items: list of {id, source, title, project_label, category, expiration,
        days_remaining, urgency, detail}
    domain_histories: {domain_name: [{"date": iso, "ssl_days_remaining": int|None}, ...]}
    """
    bucket_order = ["Overdue", "Due This Week", "Due This Month", "Upcoming", "Healthy", "Unknown"]
    bucket_counts = {bucket: 0 for bucket in bucket_order}
    for item in items:
        bucket_counts[item["urgency"]] = bucket_counts.get(item["urgency"], 0) + 1

    total_items = len(items)
    attention_items = [item for item in items if item["urgency"] in ("Overdue", "Due This Week")]

    payload = _safe_json_for_script_tag(
        {
            "items": items,
            "domainHistories": domain_histories,
            "bucketCounts": bucket_counts,
            "bucketOrder": bucket_order,
            "briefingText": briefing_text,
            "usedAi": used_ai,
            "generatedAt": generated_at,
        }
    )

    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Renewal Radar</title>
<style>
  :root {{
    --bg: #0f1419;
    --panel: #161c24;
    --panel-border: #262e3a;
    --text: #e6edf3;
    --text-dim: #8b98a5;
    --accent: #4fa8ff;
    --overdue: #ff5c5c;
    --this-week: #ffb454;
    --this-month: #f0d264;
    --upcoming: #7ee787;
    --healthy: #4fa8ff;
    --unknown: #6e7a87;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
    padding: 1.5rem;
  }}
  h1 {{ margin: 0 0 0.25rem; font-size: 1.6rem; }}
  .subtitle {{ color: var(--text-dim); margin-bottom: 1.5rem; font-size: 0.9rem; }}
  .hero-stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }}
  .stat-card {{
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 10px;
    padding: 0.9rem;
    text-align: center;
  }}
  .stat-card .num {{ font-size: 1.6rem; font-weight: 700; }}
  .stat-card .label {{ font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.03em; }}
  .stat-card[data-bucket="Overdue"] .num {{ color: var(--overdue); }}
  .stat-card[data-bucket="Due This Week"] .num {{ color: var(--this-week); }}
  .stat-card[data-bucket="Due This Month"] .num {{ color: var(--this-month); }}
  .stat-card[data-bucket="Upcoming"] .num {{ color: var(--upcoming); }}
  .stat-card[data-bucket="Healthy"] .num {{ color: var(--healthy); }}
  .stat-card[data-bucket="Unknown"] .num {{ color: var(--unknown); }}
  .panel {{
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
  }}
  .panel h2 {{ margin: 0 0 0.75rem; font-size: 1.05rem; }}
  #attention-panel.empty {{ color: var(--text-dim); font-style: italic; }}
  .attention-row {{
    display: flex;
    justify-content: space-between;
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--panel-border);
    font-size: 0.9rem;
  }}
  .attention-row:last-child {{ border-bottom: none; }}
  .badge {{
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
  }}
  .badge.Overdue {{ background: color-mix(in srgb, var(--overdue) 25%, transparent); color: var(--overdue); }}
  .badge.Due-This-Week {{ background: color-mix(in srgb, var(--this-week) 25%, transparent); color: var(--this-week); }}
  .badge.Due-This-Month {{ background: color-mix(in srgb, var(--this-month) 25%, transparent); color: var(--this-month); }}
  .badge.Upcoming {{ background: color-mix(in srgb, var(--upcoming) 25%, transparent); color: var(--upcoming); }}
  .badge.Healthy {{ background: color-mix(in srgb, var(--healthy) 25%, transparent); color: var(--healthy); }}
  .badge.Unknown {{ background: color-mix(in srgb, var(--unknown) 25%, transparent); color: var(--unknown); }}
  .source-tag {{ font-size: 0.7rem; color: var(--text-dim); border: 1px solid var(--panel-border); border-radius: 4px; padding: 0.05rem 0.35rem; }}
  input#search {{
    width: 100%;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.75rem;
    background: var(--bg);
    border: 1px solid var(--panel-border);
    border-radius: 8px;
    color: var(--text);
    font-size: 0.9rem;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  th, td {{ text-align: left; padding: 0.5rem 0.6rem; border-bottom: 1px solid var(--panel-border); }}
  th {{ cursor: pointer; color: var(--text-dim); font-weight: 600; user-select: none; white-space: nowrap; }}
  th:hover {{ color: var(--text); }}
  tbody tr:hover {{ background: rgba(255,255,255,0.03); }}
  .ai-tag {{ font-size: 0.7rem; color: var(--accent); margin-left: 0.4rem; }}
  #history-select {{
    background: var(--bg);
    color: var(--text);
    border: 1px solid var(--panel-border);
    border-radius: 6px;
    padding: 0.35rem 0.5rem;
    margin-bottom: 0.75rem;
  }}
  canvas {{ max-width: 100%; }}
  .empty-state {{ color: var(--text-dim); font-style: italic; padding: 0.5rem 0; }}
  footer {{ color: var(--text-dim); font-size: 0.75rem; margin-top: 2rem; text-align: center; }}
</style>
</head>
<body>
  <h1>Renewal Radar</h1>
  <div class="subtitle">Generated <span id="generated-at"></span></div>

  <div class="hero-stats" id="hero-stats"></div>

  <div class="panel">
    <h2>Admin Briefing<span class="ai-tag" id="ai-tag" hidden>AI-generated</span></h2>
    <p id="briefing-text"></p>
  </div>

  <div class="panel">
    <h2>Attention This Week</h2>
    <div id="attention-panel"></div>
  </div>

  <div class="panel">
    <h2>Domain Expiration History</h2>
    <select id="history-select"></select>
    <canvas id="history-chart" width="760" height="220"></canvas>
    <div id="history-empty" class="empty-state" hidden>No sync history yet for this domain.</div>
  </div>

  <div class="panel">
    <h2>All Tracked Items</h2>
    <input id="search" type="text" placeholder="Search by title, project, or category&hellip;">
    <div style="overflow-x:auto">
      <table id="items-table">
        <thead>
          <tr>
            <th data-key="source">Source</th>
            <th data-key="title">Title</th>
            <th data-key="project_label">Project</th>
            <th data-key="category">Category</th>
            <th data-key="expiration">Due / Expires</th>
            <th data-key="days_remaining">Days</th>
            <th data-key="urgency">Urgency</th>
            <th data-key="detail">Detail</th>
          </tr>
        </thead>
        <tbody id="items-body"></tbody>
      </table>
    </div>
    <div id="table-empty" class="empty-state" hidden>No items match your search.</div>
  </div>

  <footer>Renewal Radar &mdash; RDAP + live TLS checks + manually tracked renewals. No data leaves this machine except the RDAP/TLS lookups themselves and, optionally, aggregate counts sent to the Anthropic API.</footer>

  <script type="application/json" id="data-payload">{payload}</script>
  <script>
    const DATA = JSON.parse(document.getElementById('data-payload').textContent);
    const BUCKET_COLORS = {{
      "Overdue": "#ff5c5c",
      "Due This Week": "#ffb454",
      "Due This Month": "#f0d264",
      "Upcoming": "#7ee787",
      "Healthy": "#4fa8ff",
      "Unknown": "#6e7a87"
    }};

    function el(tag, opts) {{
      const node = document.createElement(tag);
      opts = opts || {{}};
      if (opts.text !== undefined) node.textContent = opts.text;
      if (opts.className) node.className = opts.className;
      if (opts.attrs) {{
        for (const [key, value] of Object.entries(opts.attrs)) node.setAttribute(key, value);
      }}
      return node;
    }}

    function badgeClass(urgency) {{
      return 'badge ' + urgency.replace(/ /g, '-');
    }}

    document.getElementById('generated-at').textContent = DATA.generatedAt;
    document.getElementById('briefing-text').textContent = DATA.briefingText;
    if (DATA.usedAi) document.getElementById('ai-tag').hidden = false;

    // Hero stats
    const heroStats = document.getElementById('hero-stats');
    DATA.bucketOrder.forEach(bucket => {{
      const card = el('div', {{ className: 'stat-card', attrs: {{ 'data-bucket': bucket }} }});
      card.appendChild(el('div', {{ className: 'num', text: String(DATA.bucketCounts[bucket] || 0) }}));
      card.appendChild(el('div', {{ className: 'label', text: bucket }}));
      heroStats.appendChild(card);
    }});

    // Attention panel
    const attentionPanel = document.getElementById('attention-panel');
    const attentionItems = DATA.items.filter(i => i.urgency === 'Overdue' || i.urgency === 'Due This Week');
    if (attentionItems.length === 0) {{
      attentionPanel.classList.add('empty');
      attentionPanel.appendChild(el('div', {{ text: 'Nothing overdue or due this week.' }}));
    }} else {{
      attentionItems.forEach(item => {{
        const row = el('div', {{ className: 'attention-row' }});
        const left = el('span');
        left.appendChild(el('span', {{ className: 'source-tag', text: item.source }}));
        left.appendChild(document.createTextNode(' ' + item.title));
        row.appendChild(left);
        row.appendChild(el('span', {{ className: badgeClass(item.urgency), text: item.urgency }}));
        attentionPanel.appendChild(row);
      }});
    }}

    // Domain history chart
    const historySelect = document.getElementById('history-select');
    const domains = Object.keys(DATA.domainHistories);
    const chart = document.getElementById('history-chart');
    const historyEmpty = document.getElementById('history-empty');
    const ctx = chart.getContext('2d');

    function drawHistory(domain) {{
      const history = DATA.domainHistories[domain] || [];
      ctx.clearRect(0, 0, chart.width, chart.height);
      const points = history.filter(p => p.ssl_days_remaining !== null && p.ssl_days_remaining !== undefined);
      if (points.length === 0) {{
        historyEmpty.hidden = false;
        chart.hidden = true;
        return;
      }}
      historyEmpty.hidden = true;
      chart.hidden = false;

      const padding = 36;
      const w = chart.width - padding * 2;
      const h = chart.height - padding * 2;
      const values = points.map(p => p.ssl_days_remaining);
      const minV = Math.min(0, ...values);
      const maxV = Math.max(...values, 1);

      ctx.strokeStyle = '#262e3a';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(padding, padding);
      ctx.lineTo(padding, chart.height - padding);
      ctx.lineTo(chart.width - padding, chart.height - padding);
      ctx.stroke();

      ctx.fillStyle = '#8b98a5';
      ctx.font = '11px sans-serif';
      ctx.fillText(String(maxV) + 'd', 2, padding + 4);
      ctx.fillText(String(minV) + 'd', 2, chart.height - padding + 4);

      ctx.strokeStyle = '#4fa8ff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      points.forEach((p, i) => {{
        const x = padding + (points.length === 1 ? w / 2 : (w * i) / (points.length - 1));
        const y = chart.height - padding - ((p.ssl_days_remaining - minV) / (maxV - minV || 1)) * h;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }});
      ctx.stroke();

      ctx.fillStyle = '#4fa8ff';
      points.forEach((p, i) => {{
        const x = padding + (points.length === 1 ? w / 2 : (w * i) / (points.length - 1));
        const y = chart.height - padding - ((p.ssl_days_remaining - minV) / (maxV - minV || 1)) * h;
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      }});
    }}

    if (domains.length === 0) {{
      historySelect.hidden = true;
      historyEmpty.hidden = false;
      chart.hidden = true;
    }} else {{
      domains.forEach(domain => {{
        historySelect.appendChild(el('option', {{ text: domain, attrs: {{ value: domain }} }}));
      }});
      historySelect.addEventListener('change', () => drawHistory(historySelect.value));
      drawHistory(domains[0]);
    }}

    // Items table
    const tbody = document.getElementById('items-body');
    const searchInput = document.getElementById('search');
    const tableEmpty = document.getElementById('table-empty');
    let sortKey = 'urgency';
    let sortAsc = true;
    const bucketOrderIndex = Object.fromEntries(DATA.bucketOrder.map((b, i) => [b, i]));

    function fmtField(item, key) {{
      if (key === 'days_remaining') {{
        return item.days_remaining === null || item.days_remaining === undefined ? '—' : String(item.days_remaining);
      }}
      const value = item[key];
      return value === null || value === undefined || value === '' ? '—' : String(value);
    }}

    function renderTable() {{
      const query = searchInput.value.trim().toLowerCase();
      let rows = DATA.items.filter(item => {{
        if (!query) return true;
        const haystack = [item.title, item.project_label, item.category, item.detail].join(' ').toLowerCase();
        return haystack.includes(query);
      }});

      rows = rows.slice().sort((a, b) => {{
        let av, bv;
        if (sortKey === 'urgency') {{
          av = bucketOrderIndex[a.urgency];
          bv = bucketOrderIndex[b.urgency];
        }} else if (sortKey === 'days_remaining') {{
          av = a.days_remaining === null || a.days_remaining === undefined ? Infinity : a.days_remaining;
          bv = b.days_remaining === null || b.days_remaining === undefined ? Infinity : b.days_remaining;
        }} else {{
          av = (a[sortKey] || '').toString().toLowerCase();
          bv = (b[sortKey] || '').toString().toLowerCase();
        }}
        if (av < bv) return sortAsc ? -1 : 1;
        if (av > bv) return sortAsc ? 1 : -1;
        return 0;
      }});

      while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
      tableEmpty.hidden = rows.length !== 0;

      rows.forEach(item => {{
        const tr = el('tr');
        tr.appendChild(el('td', {{ text: item.source }}));
        tr.appendChild(el('td', {{ text: item.title }}));
        tr.appendChild(el('td', {{ text: fmtField(item, 'project_label') }}));
        tr.appendChild(el('td', {{ text: fmtField(item, 'category') }}));
        tr.appendChild(el('td', {{ text: fmtField(item, 'expiration') }}));
        tr.appendChild(el('td', {{ text: fmtField(item, 'days_remaining') }}));
        const urgencyTd = el('td');
        urgencyTd.appendChild(el('span', {{ className: badgeClass(item.urgency), text: item.urgency }}));
        tr.appendChild(urgencyTd);
        tr.appendChild(el('td', {{ text: fmtField(item, 'detail') }}));
        tbody.appendChild(tr);
      }});
    }}

    document.querySelectorAll('#items-table th').forEach(th => {{
      th.addEventListener('click', () => {{
        const key = th.getAttribute('data-key');
        if (sortKey === key) {{ sortAsc = !sortAsc; }} else {{ sortKey = key; sortAsc = true; }}
        renderTable();
      }});
    }});
    searchInput.addEventListener('input', renderTable);
    renderTable();
  </script>
</body>
</html>
"""
