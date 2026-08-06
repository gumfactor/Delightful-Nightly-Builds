"""Terminal and self-contained HTML rendering for the manuscript pipeline."""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from typing import Any

from . import db

STAGE_ORDER = (
    "submitted",
    "under_review",
    "revise_resubmit",
    "accepted",
    "published",
    "rejected",
    "withdrawn",
)

STAGE_LABELS = {
    "submitted": "Submitted",
    "under_review": "Under Review",
    "revise_resubmit": "Revise & Resubmit",
    "accepted": "Accepted",
    "published": "Published",
    "rejected": "Rejected",
    "withdrawn": "Withdrawn",
}


def build_summary(manuscripts: list[sqlite3.Row], today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    funnel = {stage: 0 for stage in STAGE_ORDER}
    at_risk = []
    rows = []

    for m in manuscripts:
        funnel[m["status"]] = funnel.get(m["status"], 0) + 1
        risk = db.is_at_risk(m, today)
        row = {
            "id": m["id"],
            "title": m["title"],
            "authors": m["authors"],
            "journal": m["journal"],
            "status": m["status"],
            "days_in_stage": db.days_in_stage(m, today),
            "at_risk": risk,
            "revision_deadline": m["revision_deadline"],
            "doi": m["doi"],
        }
        rows.append(row)
        if risk:
            at_risk.append(row)

    return {"funnel": funnel, "rows": rows, "at_risk": at_risk}


def render_terminal(manuscripts: list[sqlite3.Row], today: date | None = None) -> str:
    summary = build_summary(manuscripts, today)
    lines = ["Manuscript Pipeline", "=" * 40]

    lines.append("\nFunnel:")
    for stage in STAGE_ORDER:
        count = summary["funnel"][stage]
        if count:
            lines.append(f"  {STAGE_LABELS[stage]:<20} {count}")

    if summary["at_risk"]:
        lines.append("\nAt risk:")
        for row in summary["at_risk"]:
            lines.append(f"  [#{row['id']}] {row['title']} — {STAGE_LABELS[row['status']]}, {row['days_in_stage']}d")
    else:
        lines.append("\nAt risk: none")

    lines.append("\nAll manuscripts:")
    for row in summary["rows"]:
        flag = " (AT RISK)" if row["at_risk"] else ""
        lines.append(f"  [#{row['id']}] {row['title']} — {STAGE_LABELS[row['status']]}, {row['days_in_stage']}d{flag}")

    return "\n".join(lines)


def _safe_json_for_script(data: Any) -> str:
    """Serialize for embedding inside a <script type="application/json"> element.

    <script> content is HTML "raw text" -- character references are NOT decoded
    by the browser, so html.escape()-ing the quotes would corrupt the JSON
    itself once read back via .textContent. Instead, only the substrings that
    could break out of the script element (or be misread as a comment/tag
    start) are neutralized, using JSON's own \\uXXXX escapes -- which remain
    valid JSON and are decoded correctly by JSON.parse.
    """
    raw = json.dumps(data)
    return raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render_html(manuscripts: list[sqlite3.Row], today: date | None = None) -> str:
    summary = build_summary(manuscripts, today)

    # All dynamic values are passed to the browser as a JSON blob (safely
    # encoded for embedding in a <script> element, see _safe_json_for_script)
    # and built into the DOM via textContent/createElement -- never innerHTML
    # from user-controlled data.
    data_json = _safe_json_for_script(summary)

    funnel_labels = [STAGE_LABELS[s] for s in STAGE_ORDER]
    funnel_counts = [summary["funnel"][s] for s in STAGE_ORDER]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Manuscript Pipeline</title>
<style>
  :root {{
    --bg: #0f1117; --panel: #1a1d27; --text: #e6e8ef; --muted: #8b90a3;
    --accent: #6ea8fe; --risk: #ff6b6b; --border: #2a2e3d;
  }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system, system-ui, sans-serif;
          margin: 0; padding: 24px; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 4px; }}
  .subtitle {{ color: var(--muted); margin-bottom: 24px; }}
  .funnel {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px; }}
  .stage-tile {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
                 padding: 12px 16px; min-width: 120px; }}
  .stage-tile .count {{ font-size: 1.6rem; font-weight: 600; }}
  .stage-tile .label {{ color: var(--muted); font-size: 0.85rem; }}
  table {{ width: 100%; border-collapse: collapse; background: var(--panel); border-radius: 8px; overflow: hidden; }}
  th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
  th {{ color: var(--muted); font-weight: 500; cursor: pointer; }}
  tr.at-risk td {{ color: var(--risk); }}
  input#search {{ background: var(--panel); border: 1px solid var(--border); color: var(--text);
                  padding: 8px 10px; border-radius: 6px; margin-bottom: 12px; width: 260px; }}
  #chart-fallback {{ display: none; }}
  section {{ margin-bottom: 28px; }}
</style>
</head>
<body>
<h1>Manuscript Pipeline</h1>
<div class="subtitle">Submission &rarr; review &rarr; revision &rarr; publication tracker</div>

<section>
  <div class="funnel" id="funnel"></div>
  <canvas id="funnel-chart" height="80"></canvas>
  <div id="chart-fallback"></div>
</section>

<section>
  <input id="search" type="text" placeholder="Search title, journal, author...">
  <table id="manuscript-table">
    <thead>
      <tr>
        <th data-key="title">Title</th>
        <th data-key="journal">Journal</th>
        <th data-key="status">Status</th>
        <th data-key="days_in_stage">Days</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>
</section>

<script id="manuscript-data" type="application/json">{data_json}</script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<script>
(function () {{
  const raw = document.getElementById('manuscript-data').textContent;
  const summary = JSON.parse(raw);

  const stageLabels = {json.dumps(funnel_labels)};
  const stageCounts = {json.dumps(funnel_counts)};

  const funnelEl = document.getElementById('funnel');
  stageLabels.forEach((label, i) => {{
    if (stageCounts[i] === 0) return;
    const tile = document.createElement('div');
    tile.className = 'stage-tile';
    const count = document.createElement('div');
    count.className = 'count';
    count.textContent = String(stageCounts[i]);
    const lab = document.createElement('div');
    lab.className = 'label';
    lab.textContent = label;
    tile.appendChild(count);
    tile.appendChild(lab);
    funnelEl.appendChild(tile);
  }});

  function renderTable(rows) {{
    const tbody = document.querySelector('#manuscript-table tbody');
    tbody.textContent = '';
    rows.forEach(row => {{
      const tr = document.createElement('tr');
      if (row.at_risk) tr.className = 'at-risk';
      ['title', 'journal', 'status', 'days_in_stage'].forEach(key => {{
        const td = document.createElement('td');
        td.textContent = String(row[key]);
        tr.appendChild(td);
      }});
      tbody.appendChild(tr);
    }});
  }}
  renderTable(summary.rows);

  document.getElementById('search').addEventListener('input', (e) => {{
    const q = e.target.value.toLowerCase();
    const filtered = summary.rows.filter(r =>
      r.title.toLowerCase().includes(q) ||
      r.journal.toLowerCase().includes(q) ||
      r.authors.toLowerCase().includes(q)
    );
    renderTable(filtered);
  }});

  document.querySelectorAll('#manuscript-table th').forEach(th => {{
    th.addEventListener('click', () => {{
      const key = th.dataset.key;
      const sorted = [...summary.rows].sort((a, b) => {{
        if (a[key] < b[key]) return -1;
        if (a[key] > b[key]) return 1;
        return 0;
      }});
      renderTable(sorted);
    }});
  }});

  function drawFallbackTable() {{
    const fallback = document.getElementById('chart-fallback');
    fallback.style.display = 'block';
    const table = document.createElement('table');
    stageLabels.forEach((label, i) => {{
      if (stageCounts[i] === 0) return;
      const tr = document.createElement('tr');
      const tdLabel = document.createElement('td');
      tdLabel.textContent = label;
      const tdCount = document.createElement('td');
      tdCount.textContent = String(stageCounts[i]);
      tr.appendChild(tdLabel);
      tr.appendChild(tdCount);
      table.appendChild(tr);
    }});
    fallback.appendChild(table);
  }}

  if (typeof Chart === 'undefined') {{
    document.getElementById('funnel-chart').style.display = 'none';
    drawFallbackTable();
  }} else {{
    const ctx = document.getElementById('funnel-chart');
    new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels: stageLabels,
        datasets: [{{ label: 'Manuscripts', data: stageCounts, backgroundColor: '#6ea8fe' }}]
      }},
      options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }} }}
    }});
  }}
}})();
</script>
</body>
</html>
"""
