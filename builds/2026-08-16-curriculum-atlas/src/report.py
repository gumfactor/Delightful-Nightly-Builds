"""Self-contained dark-mode HTML dashboard renderer.

All dynamic data is delivered as a JSON payload inside a
``<script type="application/json">`` tag and read back with ``textContent`` —
never ``innerHTML``. The DOM is built exclusively with
``createElement``/``textContent`` in the embedded JS, so no course, concept,
or objective string coming from user-authored course materials is ever
interpreted as markup.

``</`` sequences inside the JSON payload are escaped to ``<\\/`` (a legal
JSON escape for a plain solidus) before embedding, because the HTML
tokenizer ends a ``<script>`` element at the first literal ``</script``
substring regardless of any JSON-level quoting.
"""

from __future__ import annotations

import json

_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Curriculum Atlas</title>
<style>
  :root {
    --bg: #0f1115; --panel: #171a21; --panel-2: #1e222b; --border: #2a2f3a;
    --text: #e6e8ee; --muted: #9aa3b2; --accent: #7aa2f7; --warn: #f7768e;
    --ok: #9ece6a; --badge-marker: #7aa2f7; --badge-heading: #bb9af7;
    --badge-heuristic: #6b7280;
  }
  * { box-sizing: border-box; }
  body {
    background: var(--bg); color: var(--text); margin: 0;
    font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  header {
    padding: 20px 24px; border-bottom: 1px solid var(--border);
    display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap;
  }
  header h1 { margin: 0; font-size: 20px; }
  header .meta { color: var(--muted); font-size: 13px; }
  nav { display: flex; gap: 4px; padding: 12px 24px 0; flex-wrap: wrap; }
  nav button {
    background: var(--panel); color: var(--text); border: 1px solid var(--border);
    padding: 8px 14px; border-radius: 8px 8px 0 0; cursor: pointer; font-size: 13px;
  }
  nav button.active { background: var(--panel-2); border-bottom-color: var(--panel-2); color: var(--accent); }
  main { padding: 16px 24px 40px; max-width: 1100px; margin: 0 auto; }
  section.tab { display: none; }
  section.tab.active { display: block; }
  .search {
    width: 100%; padding: 10px 12px; margin-bottom: 16px; border-radius: 8px;
    border: 1px solid var(--border); background: var(--panel); color: var(--text); font-size: 14px;
  }
  .card {
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px; margin-bottom: 14px;
  }
  .card h2 { margin: 0 0 4px; font-size: 16px; }
  .card .sub { color: var(--muted); font-size: 13px; margin-bottom: 10px; }
  .concept-row {
    display: flex; align-items: center; gap: 8px; padding: 6px 0;
    border-top: 1px solid var(--border);
  }
  .concept-row:first-of-type { border-top: none; }
  .concept-name { font-weight: 600; }
  .concept-note { color: var(--muted); font-size: 13px; }
  .badge {
    font-size: 11px; padding: 2px 7px; border-radius: 999px; color: #0f1115; font-weight: 600;
  }
  .badge.marker { background: var(--badge-marker); }
  .badge.heading { background: var(--badge-heading); }
  .badge.heuristic { background: var(--badge-heuristic); color: #e6e8ee; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 600; }
  .flag-ok { color: var(--ok); }
  .flag-warn { color: var(--warn); font-weight: 600; }
  .empty { color: var(--muted); font-style: italic; padding: 20px 0; }
  .diff-cols { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
  .diff-cols h3 { font-size: 13px; color: var(--muted); margin: 0 0 6px; }
  .diff-cols ul { margin: 0; padding-left: 18px; }
  @media (max-width: 700px) { .diff-cols { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<header>
  <h1>Curriculum Atlas</h1>
  <span class="meta">Generated __GENERATED_AT__</span>
</header>
<nav>
  <button data-tab="courses" class="active">Courses</button>
  <button data-tab="overlap">Cross-Course Overlap</button>
  <button data-tab="gaps">Objective Gaps</button>
</nav>
<main>
  <input class="search" id="search" placeholder="Search concepts, courses, or objectives...">
  <section class="tab active" id="tab-courses"></section>
  <section class="tab" id="tab-overlap"></section>
  <section class="tab" id="tab-gaps"></section>
</main>
<script type="application/json" id="atlas-data">__ATLAS_DATA_JSON__</script>
<script>
(function () {
  var data = JSON.parse(document.getElementById('atlas-data').textContent);
  var el = function (tag, opts) {
    var e = document.createElement(tag);
    opts = opts || {};
    if (opts.text !== undefined) e.textContent = opts.text;
    if (opts.cls) e.className = opts.cls;
    return e;
  };

  function renderCourses(filter) {
    var root = document.getElementById('tab-courses');
    while (root.firstChild) root.removeChild(root.firstChild);
    var any = false;
    data.courses.forEach(function (course) {
      course.terms.forEach(function (termBlock) {
        var concepts = termBlock.concepts.filter(function (c) {
          return !filter || matches(filter, [course.name, termBlock.term, c.display_name, c.note]);
        });
        if (filter && concepts.length === 0 && !matches(filter, [course.name, termBlock.term])) return;
        any = true;
        var card = el('div', { cls: 'card' });
        card.appendChild(el('h2', { text: course.name }));
        card.appendChild(el('div', {
          cls: 'sub',
          text: termBlock.term + ' — ' + termBlock.documents.length + ' document(s), ' +
                termBlock.concepts.length + ' concept(s), ' + termBlock.objectives.length + ' objective(s)'
        }));
        if (concepts.length === 0) {
          card.appendChild(el('div', { cls: 'empty', text: 'No concepts extracted yet.' }));
        } else {
          concepts.forEach(function (c) {
            var row = el('div', { cls: 'concept-row' });
            row.appendChild(el('span', { cls: 'badge ' + c.source, text: c.source }));
            var nameWrap = el('div');
            nameWrap.appendChild(el('div', { cls: 'concept-name', text: c.display_name }));
            if (c.note) nameWrap.appendChild(el('div', { cls: 'concept-note', text: c.note }));
            row.appendChild(nameWrap);
            card.appendChild(row);
          });
        }
        root.appendChild(card);
      });
    });
    if (!any) root.appendChild(el('div', { cls: 'empty', text: 'No courses match your search.' }));
  }

  function renderOverlap(filter) {
    var root = document.getElementById('tab-overlap');
    while (root.firstChild) root.removeChild(root.firstChild);
    var rows = data.overlap.filter(function (o) {
      return !filter || matches(filter, [o.display_name]);
    });
    if (rows.length === 0) {
      root.appendChild(el('div', { cls: 'empty', text: 'No concepts currently appear in more than one course.' }));
      return;
    }
    var table = el('table');
    var thead = el('thead');
    var hr = el('tr');
    ['Concept', 'Courses', 'Appears In'].forEach(function (h) { hr.appendChild(el('th', { text: h })); });
    thead.appendChild(hr);
    table.appendChild(thead);
    var tbody = el('tbody');
    rows.forEach(function (o) {
      var tr = el('tr');
      tr.appendChild(el('td', { text: o.display_name }));
      tr.appendChild(el('td', { text: String(o.course_count) }));
      var locCell = el('td');
      o.locations.forEach(function (loc, i) {
        if (i > 0) locCell.appendChild(document.createTextNode(', '));
        locCell.appendChild(document.createTextNode(loc.course_name + ' (' + loc.term + ')'));
      });
      tr.appendChild(locCell);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    root.appendChild(table);
  }

  function renderGaps(filter) {
    var root = document.getElementById('tab-gaps');
    while (root.firstChild) root.removeChild(root.firstChild);
    var any = false;
    data.courses.forEach(function (course) {
      course.terms.forEach(function (termBlock) {
        var objectives = termBlock.objectives.filter(function (o) {
          return !filter || matches(filter, [course.name, termBlock.term, o.text]);
        });
        if (objectives.length === 0) return;
        any = true;
        var card = el('div', { cls: 'card' });
        card.appendChild(el('h2', { text: course.name + ' — ' + termBlock.term }));
        var table = el('table');
        var thead = el('thead');
        var hr = el('tr');
        ['Objective', 'Best Match', 'Score', 'Status'].forEach(function (h) {
          hr.appendChild(el('th', { text: h }));
        });
        thead.appendChild(hr);
        table.appendChild(thead);
        var tbody = el('tbody');
        objectives.forEach(function (o) {
          var tr = el('tr');
          tr.appendChild(el('td', { text: o.objective_text }));
          tr.appendChild(el('td', { text: o.best_concept || '—' }));
          tr.appendChild(el('td', { text: o.best_score.toFixed(2) }));
          tr.appendChild(el('td', {
            cls: o.flagged ? 'flag-warn' : 'flag-ok',
            text: o.flagged ? 'Not clearly covered' : 'Covered'
          }));
          tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        card.appendChild(table);
        root.appendChild(card);
      });
    });
    if (!any) root.appendChild(el('div', { cls: 'empty', text: 'No objectives extracted yet.' }));
  }

  function matches(filter, fields) {
    var f = filter.toLowerCase();
    return fields.some(function (v) { return v && String(v).toLowerCase().indexOf(f) !== -1; });
  }

  function renderAll() {
    var filter = document.getElementById('search').value.trim();
    renderCourses(filter);
    renderOverlap(filter);
    renderGaps(filter);
  }

  document.querySelectorAll('nav button').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('nav button').forEach(function (b) { b.classList.remove('active'); });
      document.querySelectorAll('section.tab').forEach(function (s) { s.classList.remove('active'); });
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    });
  });
  document.getElementById('search').addEventListener('input', renderAll);

  renderAll();
})();
</script>
</body>
</html>
"""


def _safe_json_for_script(obj) -> str:
    raw = json.dumps(obj)
    return raw.replace("</", "<\\/")


def render_dashboard(payload: dict, out_path: str) -> None:
    html = _TEMPLATE.replace("__ATLAS_DATA_JSON__", _safe_json_for_script(payload))
    html = html.replace("__GENERATED_AT__", payload.get("generated_at", ""))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
