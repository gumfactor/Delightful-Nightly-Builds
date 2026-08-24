"""Self-contained dark-mode HTML dashboard for a batch of lecture reports.

All dynamic content is delivered as a JSON payload and built into the DOM via
createElement/textContent — never innerHTML — so lecture text (including any
malicious payload a note might contain) can never execute as markup.
"""
from __future__ import annotations

import json
from pathlib import Path

from parser import Lecture
from timing import LectureReport

STATUS_LABELS = {
    "on_target": "On target",
    "over_budget": "Over budget",
    "under_budget": "Under budget",
}


def _lecture_payload(lecture: Lecture, report: LectureReport) -> dict:
    return {
        "path": Path(lecture.path).name,
        "title": lecture.title,
        "budgetStatus": report.budget_status,
        "budgetLabel": STATUS_LABELS[report.budget_status],
        "totalMinutes": round(report.total_minutes, 1),
        "targetMinutes": round(report.target_minutes, 1),
        "worstSection": report.worst_section,
        "denseSections": report.dense_sections,
        "objectiveFlag": report.objective_flag,
        "headingSkipWarning": report.heading_skip_warning,
        "objectives": lecture.objectives,
        "sections": [
            {
                "heading": s.heading,
                "bulletCount": s.bullet_count,
                "estimatedMinutes": round(t.estimated_minutes, 1),
            }
            for s, t in zip(lecture.sections, report.section_timings)
        ],
    }


def build_dashboard_html(lectures_and_reports: list[tuple[Lecture, LectureReport]]) -> str:
    payload = [_lecture_payload(lec, rep) for lec, rep in lectures_and_reports]
    # `</script>` inside JSON-encoded lecture text must never terminate this
    # data script tag early — escape the forward slash the same way JS's
    # JSON.stringify replacer conventions do.
    data_json = json.dumps(payload).replace("</", "<\\/")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lecture Loom — Batch Dashboard</title>
<style>
  :root {{
    --bg: #0f1115;
    --panel: #171a21;
    --border: #2a2e39;
    --text: #e6e8ec;
    --muted: #9aa1ac;
    --accent: #6ea8fe;
    --ok: #3ddc97;
    --warn: #f5c451;
    --bad: #ef5b5b;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 1.5rem;
  }}
  h1 {{ font-size: 1.4rem; margin: 0 0 1rem; }}
  .summary {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; }}
  .stat {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    min-width: 120px;
  }}
  .stat .label {{ color: var(--muted); font-size: 0.75rem; }}
  .stat .value {{ font-size: 1.3rem; font-weight: 600; }}
  input[type="search"] {{
    width: 100%;
    max-width: 320px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 1rem;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
  }}
  table {{ width: 100%; border-collapse: collapse; overflow-x: auto; display: block; }}
  th, td {{
    text-align: left;
    padding: 0.6rem 0.75rem;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }}
  th {{ color: var(--muted); font-weight: 500; font-size: 0.8rem; }}
  tr.lecture-row {{ cursor: pointer; }}
  tr.lecture-row:hover {{ background: var(--panel); }}
  .badge {{
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
  }}
  .badge.on_target {{ background: rgba(61,220,151,0.15); color: var(--ok); }}
  .badge.over_budget {{ background: rgba(239,91,91,0.15); color: var(--bad); }}
  .badge.under_budget {{ background: rgba(245,196,81,0.15); color: var(--warn); }}
  .flag-missing, .flag-sparse {{ color: var(--warn); }}
  .detail-row td {{ background: var(--panel); white-space: normal; }}
  .detail-row.hidden {{ display: none; }}
  .detail-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
  @media (max-width: 640px) {{ .detail-grid {{ grid-template-columns: 1fr; }} }}
  ul {{ margin: 0.25rem 0; padding-left: 1.2rem; }}
</style>
</head>
<body>
<h1>Lecture Loom — Batch Dashboard</h1>
<div class="summary" id="summary"></div>
<input type="search" id="search" placeholder="Search lectures...">
<table>
  <thead>
    <tr>
      <th>Lecture</th>
      <th>Status</th>
      <th>Est. / Target (min)</th>
      <th>Sections</th>
      <th>Objectives</th>
      <th>Flags</th>
    </tr>
  </thead>
  <tbody id="rows"></tbody>
</table>
<script type="application/json" id="loom-data">{data_json}</script>
<script>
(function () {{
  var data = JSON.parse(document.getElementById('loom-data').textContent);
  var rowsBody = document.getElementById('rows');
  var summary = document.getElementById('summary');

  function stat(label, value) {{
    var box = document.createElement('div');
    box.className = 'stat';
    var l = document.createElement('div');
    l.className = 'label';
    l.textContent = label;
    var v = document.createElement('div');
    v.className = 'value';
    v.textContent = value;
    box.appendChild(l);
    box.appendChild(v);
    return box;
  }}

  var overCount = data.filter(function (d) {{ return d.budgetStatus === 'over_budget'; }}).length;
  var missingObjCount = data.filter(function (d) {{ return d.objectiveFlag === 'missing'; }}).length;
  summary.appendChild(stat('Lectures', data.length));
  summary.appendChild(stat('Over budget', overCount));
  summary.appendChild(stat('Missing objectives', missingObjCount));

  function flagText(d) {{
    var flags = [];
    if (d.objectiveFlag === 'missing') flags.push('no objectives');
    if (d.objectiveFlag === 'sparse') flags.push('sparse objectives');
    if (d.denseSections.length) flags.push(d.denseSections.length + ' dense section(s)');
    if (d.headingSkipWarning) flags.push('heading skip');
    return flags.length ? flags.join(', ') : '—';
  }}

  function buildDetail(d) {{
    var tr = document.createElement('tr');
    tr.className = 'detail-row hidden';
    var td = document.createElement('td');
    td.colSpan = 6;

    var grid = document.createElement('div');
    grid.className = 'detail-grid';

    var objBox = document.createElement('div');
    var objTitle = document.createElement('strong');
    objTitle.textContent = 'Objectives';
    objBox.appendChild(objTitle);
    var objList = document.createElement('ul');
    if (d.objectives.length === 0) {{
      var li = document.createElement('li');
      li.textContent = '(none detected)';
      objList.appendChild(li);
    }} else {{
      d.objectives.forEach(function (o) {{
        var li = document.createElement('li');
        li.textContent = o;
        objList.appendChild(li);
      }});
    }}
    objBox.appendChild(objList);

    var secBox = document.createElement('div');
    var secTitle = document.createElement('strong');
    secTitle.textContent = 'Sections';
    secBox.appendChild(secTitle);
    var secList = document.createElement('ul');
    d.sections.forEach(function (s) {{
      var li = document.createElement('li');
      li.textContent = s.heading + ' — ' + s.bulletCount + ' bullets, ~' + s.estimatedMinutes + ' min';
      secList.appendChild(li);
    }});
    secBox.appendChild(secList);

    grid.appendChild(objBox);
    grid.appendChild(secBox);
    td.appendChild(grid);
    tr.appendChild(td);
    return tr;
  }}

  function render(filterText) {{
    while (rowsBody.firstChild) rowsBody.removeChild(rowsBody.firstChild);
    var needle = (filterText || '').toLowerCase();
    data.forEach(function (d) {{
      if (needle && d.title.toLowerCase().indexOf(needle) === -1) return;

      var row = document.createElement('tr');
      row.className = 'lecture-row';

      var tdTitle = document.createElement('td');
      tdTitle.textContent = d.title;
      row.appendChild(tdTitle);

      var tdStatus = document.createElement('td');
      var badge = document.createElement('span');
      badge.className = 'badge ' + d.budgetStatus;
      badge.textContent = d.budgetLabel;
      tdStatus.appendChild(badge);
      row.appendChild(tdStatus);

      var tdMinutes = document.createElement('td');
      tdMinutes.textContent = d.totalMinutes + ' / ' + d.targetMinutes;
      row.appendChild(tdMinutes);

      var tdSections = document.createElement('td');
      tdSections.textContent = String(d.sections.length);
      row.appendChild(tdSections);

      var tdObjectives = document.createElement('td');
      tdObjectives.textContent = String(d.objectives.length);
      if (d.objectiveFlag !== 'ok') tdObjectives.className = 'flag-' + d.objectiveFlag;
      row.appendChild(tdObjectives);

      var tdFlags = document.createElement('td');
      tdFlags.textContent = flagText(d);
      row.appendChild(tdFlags);

      var detail = buildDetail(d);
      row.addEventListener('click', function () {{
        detail.classList.toggle('hidden');
      }});

      rowsBody.appendChild(row);
      rowsBody.appendChild(detail);
    }});
  }}

  document.getElementById('search').addEventListener('input', function (e) {{
    render(e.target.value);
  }});

  render('');
}})();
</script>
</body>
</html>
"""
