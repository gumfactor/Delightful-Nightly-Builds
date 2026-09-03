"""Render a self-contained dark-mode HTML dashboard for the Promptbook library.

Dynamic data is delivered as JSON inside a script tag with ``</`` escaped to prevent premature
tag termination, and the DOM is built exclusively via ``createElement``/``textContent`` — never
``innerHTML`` — so prompt text (which may contain arbitrary user-typed content, including HTML-
looking text) can never execute as markup.
"""
from __future__ import annotations

import json
import sqlite3

from src.storage import get_all_prompts, get_stats


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "prompt_uuid": row["prompt_uuid"],
        "project": row["project"],
        "git_branch": row["git_branch"],
        "entrypoint": row["entrypoint"],
        "timestamp": row["timestamp"],
        "prompt_text": row["prompt_text"],
        "task_type": row["task_type"],
        "score": row["score"],
        "tools_used": json.loads(row["tools_used"]),
        "files_edited": row["files_edited"],
        "test_run": bool(row["test_run"]),
        "test_passed": None if row["test_passed"] is None else bool(row["test_passed"]),
        "git_commit": bool(row["git_commit"]),
        "had_error": bool(row["had_error"]),
        "ai_note": row["ai_note"],
    }


def render_html(conn: sqlite3.Connection) -> str:
    prompts = [_row_to_dict(r) for r in get_all_prompts(conn)]
    stats = get_stats(conn)
    payload = json.dumps({"prompts": prompts, "stats": stats}).replace("</", "<\\/")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Promptbook</title>
<style>
  :root {{
    --bg: #0f1115;
    --panel: #171a21;
    --border: #2a2e38;
    --text: #e6e8ec;
    --muted: #8b91a0;
    --accent: #6ea8fe;
    --good: #4caf7d;
    --mid: #d9a441;
    --bad: #d9534f;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 0;
    background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }}
  header {{ padding: 24px 20px 12px; border-bottom: 1px solid var(--border); }}
  h1 {{ margin: 0 0 4px; font-size: 1.5rem; }}
  .sub {{ color: var(--muted); font-size: 0.9rem; }}
  .stats {{ display: flex; flex-wrap: wrap; gap: 12px; padding: 16px 20px; }}
  .stat-card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 16px; min-width: 120px; flex: 1 1 120px;
  }}
  .stat-card .n {{ font-size: 1.4rem; font-weight: 600; }}
  .stat-card .l {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; }}
  .controls {{
    display: flex; flex-wrap: wrap; gap: 10px; padding: 0 20px 16px; align-items: center;
  }}
  .controls input, .controls select {{
    background: var(--panel); color: var(--text); border: 1px solid var(--border);
    border-radius: 8px; padding: 8px 10px; font-size: 0.9rem;
  }}
  .controls input[type="search"] {{ flex: 1 1 220px; }}
  main {{ padding: 0 20px 40px; }}
  .card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 14px 16px; margin-bottom: 12px;
  }}
  .card-top {{ display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; }}
  .badge {{
    display: inline-block; border-radius: 999px; padding: 2px 10px; font-size: 0.72rem;
    font-weight: 600; text-transform: uppercase; letter-spacing: 0.02em;
    background: rgba(110,168,254,0.15); color: var(--accent);
  }}
  .score {{ font-weight: 700; font-size: 1.05rem; }}
  .score.good {{ color: var(--good); }}
  .score.mid {{ color: var(--mid); }}
  .score.bad {{ color: var(--bad); }}
  .prompt-text {{
    white-space: pre-wrap; margin: 10px 0; line-height: 1.4; font-size: 0.95rem;
  }}
  .meta {{ color: var(--muted); font-size: 0.78rem; display: flex; flex-wrap: wrap; gap: 10px; }}
  .ai-note {{ margin-top: 8px; font-size: 0.85rem; color: var(--accent); font-style: italic; }}
  button.copy {{
    background: transparent; border: 1px solid var(--border); color: var(--text);
    border-radius: 6px; padding: 4px 10px; font-size: 0.78rem; cursor: pointer;
  }}
  button.copy:hover {{ border-color: var(--accent); }}
  .empty {{ color: var(--muted); padding: 40px 0; text-align: center; }}
  @media (max-width: 480px) {{
    .card-top {{ flex-direction: column; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Promptbook</h1>
  <div class="sub">Your own past prompts, scored by what happened next.</div>
</header>
<div class="stats" id="stats"></div>
<div class="controls">
  <input type="search" id="q" placeholder="Search prompt text…" data-testid="search-input">
  <select id="taskType" data-testid="task-type-filter"><option value="">All task types</option></select>
  <select id="project" data-testid="project-filter"><option value="">All projects</option></select>
  <select id="minScore" data-testid="min-score-filter">
    <option value="0">Any score</option>
    <option value="7">7+ only</option>
    <option value="4">4+ only</option>
  </select>
</div>
<main id="list" data-testid="prompt-list"></main>

<script id="promptbook-data" type="application/json">{payload}</script>
<script>
(function() {{
  var data = JSON.parse(document.getElementById('promptbook-data').textContent);
  var prompts = data.prompts;
  var stats = data.stats;

  function scoreClass(s) {{
    if (s >= 7) return 'good';
    if (s >= 4) return 'mid';
    return 'bad';
  }}

  function renderStats() {{
    var container = document.getElementById('stats');
    var cards = [
      ['Total prompts', stats.total],
      ['Avg score', stats.avg_score],
      ['Task types', Object.keys(stats.by_task_type).length],
      ['Projects', Object.keys(stats.by_project).length]
    ];
    cards.forEach(function(c) {{
      var card = document.createElement('div');
      card.className = 'stat-card';
      var n = document.createElement('div');
      n.className = 'n';
      n.textContent = c[1];
      var l = document.createElement('div');
      l.className = 'l';
      l.textContent = c[0];
      card.appendChild(n);
      card.appendChild(l);
      container.appendChild(card);
    }});
  }}

  function populateSelect(id, values) {{
    var select = document.getElementById(id);
    values.forEach(function(v) {{
      var opt = document.createElement('option');
      opt.value = v;
      opt.textContent = v;
      select.appendChild(opt);
    }});
  }}

  function shortProject(p) {{
    var parts = p.split('/');
    return parts[parts.length - 1] || p;
  }}

  function renderCard(p) {{
    var card = document.createElement('div');
    card.className = 'card';
    card.setAttribute('data-testid', 'prompt-card');

    var top = document.createElement('div');
    top.className = 'card-top';

    var left = document.createElement('div');
    var badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = p.task_type;
    left.appendChild(badge);

    var right = document.createElement('div');
    var score = document.createElement('span');
    score.className = 'score ' + scoreClass(p.score);
    score.textContent = p.score + '/10';
    score.setAttribute('data-testid', 'prompt-score');
    right.appendChild(score);

    top.appendChild(left);
    top.appendChild(right);
    card.appendChild(top);

    var text = document.createElement('div');
    text.className = 'prompt-text';
    text.textContent = p.prompt_text;
    text.setAttribute('data-testid', 'prompt-text');
    card.appendChild(text);

    if (p.ai_note) {{
      var note = document.createElement('div');
      note.className = 'ai-note';
      note.textContent = p.ai_note;
      card.appendChild(note);
    }}

    var meta = document.createElement('div');
    meta.className = 'meta';
    var bits = [
      shortProject(p.project),
      p.timestamp,
      p.tools_used.length + ' tool(s)',
      p.git_commit ? 'commit' : null,
      p.test_run ? (p.test_passed === true ? 'tests passed' : p.test_passed === false ? 'tests failed' : 'tests run') : null,
      p.had_error ? 'error seen' : null
    ].filter(Boolean);
    bits.forEach(function(b) {{
      var span = document.createElement('span');
      span.textContent = b;
      meta.appendChild(span);
    }});
    card.appendChild(meta);

    var copyBtn = document.createElement('button');
    copyBtn.className = 'copy';
    copyBtn.textContent = 'Copy prompt';
    copyBtn.setAttribute('data-testid', 'copy-button');
    copyBtn.addEventListener('click', function() {{
      if (navigator.clipboard) {{
        navigator.clipboard.writeText(p.prompt_text).catch(function() {{}});
      }}
    }});
    card.appendChild(copyBtn);

    return card;
  }}

  function applyFilters() {{
    var q = document.getElementById('q').value.toLowerCase();
    var taskType = document.getElementById('taskType').value;
    var project = document.getElementById('project').value;
    var minScore = parseInt(document.getElementById('minScore').value, 10);

    var filtered = prompts.filter(function(p) {{
      if (q && p.prompt_text.toLowerCase().indexOf(q) === -1) return false;
      if (taskType && p.task_type !== taskType) return false;
      if (project && p.project !== project) return false;
      if (p.score < minScore) return false;
      return true;
    }});

    var list = document.getElementById('list');
    while (list.firstChild) list.removeChild(list.firstChild);

    if (filtered.length === 0) {{
      var empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = 'No prompts match these filters.';
      list.appendChild(empty);
      return;
    }}
    filtered.forEach(function(p) {{ list.appendChild(renderCard(p)); }});
  }}

  renderStats();
  populateSelect('taskType', Object.keys(stats.by_task_type).sort());
  populateSelect('project', Object.keys(stats.by_project).sort());
  document.getElementById('q').addEventListener('input', applyFilters);
  document.getElementById('taskType').addEventListener('change', applyFilters);
  document.getElementById('project').addEventListener('change', applyFilters);
  document.getElementById('minScore').addEventListener('change', applyFilters);
  applyFilters();
}})();
</script>
</body>
</html>
"""
