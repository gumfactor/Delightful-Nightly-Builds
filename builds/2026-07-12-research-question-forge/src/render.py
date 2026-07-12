"""Self-contained dark-mode HTML viewer for the Research Question Forge library."""
from __future__ import annotations

import html
import json
import sqlite3
from pathlib import Path

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Research Question Forge</title>
<style>
  :root {
    --bg: #0f1115; --panel: #171a21; --border: #2a2e38; --text: #e6e8ee;
    --muted: #8b93a3; --accent: #7aa2f7; --star: #f6c945; --ok: #6cd97e;
    --warn: #f5a742; --danger: #f56c6c;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.5;
  }
  header { padding: 20px 24px 8px; }
  h1 { margin: 0 0 4px; font-size: 22px; }
  .sub { color: var(--muted); font-size: 13px; margin-bottom: 16px; }
  .controls {
    display: flex; gap: 10px; flex-wrap: wrap; padding: 0 24px 16px;
    align-items: center;
  }
  input[type=text], select {
    background: var(--panel); border: 1px solid var(--border); color: var(--text);
    padding: 8px 10px; border-radius: 6px; font-size: 14px;
  }
  input[type=text] { flex: 1; min-width: 180px; }
  .count { color: var(--muted); font-size: 13px; padding: 0 24px 8px; }
  main { display: grid; grid-template-columns: 1fr; gap: 0; padding: 0 24px 24px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }
  th { color: var(--muted); font-weight: 600; position: sticky; top: 0; background: var(--bg); }
  tr.row { cursor: pointer; }
  tr.row:hover { background: var(--panel); }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
  .badge.feasible-now { background: rgba(108,217,126,0.15); color: var(--ok); }
  .badge.needs-resources { background: rgba(245,167,66,0.15); color: var(--warn); }
  .badge.speculative { background: rgba(245,108,108,0.15); color: var(--danger); }
  .star { color: var(--muted); }
  .star.on { color: var(--star); }
  .novelty { font-variant-numeric: tabular-nums; }
  #detail {
    display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6);
    align-items: flex-start; justify-content: center; padding: 40px 16px; z-index: 10;
  }
  #detail.open { display: flex; }
  #detail .panel {
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 24px; max-width: 640px; width: 100%; max-height: 85vh; overflow-y: auto;
  }
  #detail .panel h2 { margin-top: 0; font-size: 17px; }
  #detail .close { float: right; cursor: pointer; color: var(--muted); font-size: 20px; line-height: 1; }
  #detail .field { margin-bottom: 14px; }
  #detail .field .label { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; }
  #detail pre {
    white-space: pre-wrap; word-break: break-word; background: #0d0f13; border: 1px solid var(--border);
    border-radius: 6px; padding: 10px; font-family: inherit; font-size: 13px; margin: 0;
  }
  button {
    background: var(--accent); color: #0f1115; border: none; border-radius: 6px;
    padding: 8px 12px; font-size: 13px; font-weight: 600; cursor: pointer;
  }
  button.secondary { background: transparent; border: 1px solid var(--border); color: var(--text); }
  .empty { padding: 40px 24px; color: var(--muted); text-align: center; }
  @media (max-width: 640px) {
    th:nth-child(3), td:nth-child(3) { display: none; }
  }
</style>
</head>
<body>
<header>
  <h1>Research Question Forge</h1>
  <div class="sub">__SUBTITLE__</div>
</header>
<div class="controls">
  <input type="text" id="q" placeholder="Search skeleton, rationale, tag...">
  <select id="testabilityFilter">
    <option value="">All testability</option>
    <option value="feasible-now">Feasible now</option>
    <option value="needs-resources">Needs resources</option>
    <option value="speculative">Speculative</option>
  </select>
  <select id="starFilter">
    <option value="">All</option>
    <option value="1">Starred only</option>
    <option value="0">Unstarred only</option>
  </select>
</div>
<div class="count" id="count"></div>
<main>
  <table id="tbl">
    <thead>
      <tr><th></th><th>Question</th><th>Testability</th><th>Novelty</th><th>Tag</th></tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div class="empty" id="emptyMsg" style="display:none">No questions match your filters.</div>
</main>

<div id="detail">
  <div class="panel">
    <span class="close" id="closeBtn">&times;</span>
    <h2 id="dSkeleton"></h2>
    <div class="field"><div class="label">Testability</div><div id="dTestability"></div></div>
    <div class="field"><div class="label">Novelty score</div><div id="dNovelty"></div></div>
    <div class="field"><div class="label">Rationale</div><pre id="dRationale"></pre></div>
    <div class="field"><div class="label">AI polish (<span id="dSource"></span>)</div><pre id="dPolish"></pre></div>
    <div class="field"><div class="label">Tag</div><div id="dTag"></div></div>
    <button id="copyBtn">Copy as Markdown</button>
    <button class="secondary" id="closeBtn2">Close</button>
  </div>
</div>

<script type="application/json" id="data">__DATA_JSON__</script>
<script>
(function () {
  var raw = document.getElementById('data').textContent;
  var questions = JSON.parse(raw);
  var tbody = document.getElementById('tbody');
  var countEl = document.getElementById('count');
  var emptyMsg = document.getElementById('emptyMsg');
  var qInput = document.getElementById('q');
  var testFilter = document.getElementById('testabilityFilter');
  var starFilter = document.getElementById('starFilter');

  function esc(s) {
    var div = document.createElement('div');
    div.textContent = s == null ? '' : String(s);
    return div.innerHTML;
  }

  function matches(item, term, testability, star) {
    if (testability && item.testability !== testability) return false;
    if (star !== '' && (item.starred ? '1' : '0') !== star) return false;
    if (!term) return true;
    var haystack = (item.skeleton + ' ' + item.rationale + ' ' + (item.tag || '')).toLowerCase();
    return haystack.indexOf(term.toLowerCase()) !== -1;
  }

  function render() {
    var term = qInput.value.trim();
    var testability = testFilter.value;
    var star = starFilter.value;
    var filtered = questions.filter(function (item) {
      return matches(item, term, testability, star);
    });
    tbody.innerHTML = '';
    filtered.forEach(function (item) {
      var tr = document.createElement('tr');
      tr.className = 'row';
      tr.setAttribute('data-testid', 'question-row');
      tr.setAttribute('data-id', item.id);
      tr.innerHTML =
        '<td><span class="star' + (item.starred ? ' on' : '') + '">' + (item.starred ? '★' : '☆') + '</span></td>' +
        '<td>' + esc(item.skeleton) + '</td>' +
        '<td><span class="badge ' + esc(item.testability) + '">' + esc(item.testability) + '</span></td>' +
        '<td class="novelty">' + item.novelty_score.toFixed(2) + '</td>' +
        '<td>' + esc(item.tag) + '</td>';
      tr.addEventListener('click', function () { openDetail(item); });
      tbody.appendChild(tr);
    });
    countEl.textContent = filtered.length + ' of ' + questions.length + ' question' + (questions.length === 1 ? '' : 's');
    emptyMsg.style.display = filtered.length === 0 ? 'block' : 'none';
  }

  var detailEl = document.getElementById('detail');
  var currentItem = null;

  function openDetail(item) {
    currentItem = item;
    document.getElementById('dSkeleton').textContent = item.skeleton;
    document.getElementById('dTestability').textContent = item.testability;
    document.getElementById('dNovelty').textContent = item.novelty_score.toFixed(4);
    document.getElementById('dRationale').textContent = item.rationale;
    document.getElementById('dPolish').textContent = item.ai_polish || '(no AI polish saved)';
    document.getElementById('dSource').textContent = item.ai_source;
    document.getElementById('dTag').textContent = item.tag || '(untagged)';
    detailEl.classList.add('open');
  }

  function closeDetail() {
    detailEl.classList.remove('open');
    currentItem = null;
  }

  document.getElementById('closeBtn').addEventListener('click', closeDetail);
  document.getElementById('closeBtn2').addEventListener('click', closeDetail);
  detailEl.addEventListener('click', function (e) {
    if (e.target === detailEl) closeDetail();
  });

  document.getElementById('copyBtn').addEventListener('click', function () {
    if (!currentItem) return;
    var md = '### ' + currentItem.skeleton + '\\n\\n' +
      '**Rationale:** ' + currentItem.rationale + '\\n\\n' +
      '**Testability:** ' + currentItem.testability + '\\n\\n' +
      (currentItem.ai_polish ? '**Polished:**\\n\\n' + currentItem.ai_polish : '');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(md);
    }
    var btn = document.getElementById('copyBtn');
    var original = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(function () { btn.textContent = original; }, 1200);
  });

  qInput.addEventListener('input', render);
  testFilter.addEventListener('change', render);
  starFilter.addEventListener('change', render);

  render();
})();
</script>
</body>
</html>
"""


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "population": row["population"],
        "construct": row["construct"],
        "outcome": row["outcome"],
        "method": row["method"],
        "frame": row["frame"],
        "skeleton": row["skeleton"],
        "rationale": row["rationale"],
        "testability": row["testability"],
        "novelty_score": row["novelty_score"],
        "ai_polish": row["ai_polish"],
        "ai_source": row["ai_source"],
        "starred": bool(row["starred"]),
        "used": bool(row["used"]),
        "tag": row["tag"] or "",
    }


def render_html(questions: list[sqlite3.Row] | list[dict]) -> str:
    dicts = [q if isinstance(q, dict) else _row_to_dict(q) for q in questions]
    data_json = json.dumps(dicts, ensure_ascii=True)
    # Prevent a stored value like "</script>" from breaking out of the JSON <script> block.
    data_json = data_json.replace("</", "<\\/")
    subtitle = html.escape(f"{len(dicts)} question{'s' if len(dicts) != 1 else ''} in your library")
    return TEMPLATE.replace("__DATA_JSON__", data_json).replace("__SUBTITLE__", subtitle)


def write_html(questions: list[sqlite3.Row] | list[dict], output_path: Path | str) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html(questions), encoding="utf-8")
    return output_path
