"""Self-contained dark-mode HTML dashboard for the Maple Press piece library.

All piece data is delivered to the browser as a JSON payload inside a
<script type="application/json"> tag and read back via .textContent /
JSON.parse — the DOM itself is built with createElement/textContent only, so
nothing from a business name, description, or generated body is ever
interpreted as HTML.
"""

from __future__ import annotations

import json


def _safe_json(data) -> str:
    """JSON-encode data for embedding inside a <script> tag.

    Escapes '</' so a value containing a literal '</script>' cannot terminate
    the script element early — required regardless of the script's MIME type,
    since HTML's raw-text parsing rule for <script> applies to the closing
    tag sequence itself, not the declared type attribute.
    """
    return json.dumps(data).replace("</", "<\\/")


def render_html(pieces: list[dict]) -> str:
    payload = _safe_json(pieces)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Maple Press — Piece Library</title>
<style>
  :root {{
    --bg: #0f1512;
    --panel: #161e19;
    --border: #263029;
    --text: #e7ece9;
    --muted: #93a39a;
    --accent: #d3453a;
    --accent-soft: #3a2321;
    --focus: #d3453a;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.5;
  }}
  header {{
    padding: 1.5rem 1.25rem 1rem;
    border-bottom: 1px solid var(--border);
  }}
  header h1 {{ margin: 0 0 0.25rem; font-size: 1.4rem; }}
  header p {{ margin: 0; color: var(--muted); font-size: 0.9rem; }}
  .controls {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border);
  }}
  .controls input, .controls select {{
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.5rem 0.7rem;
    border-radius: 6px;
    font-size: 0.9rem;
  }}
  .controls input {{ flex: 1; min-width: 180px; }}
  main {{ padding: 1rem 1.25rem 3rem; max-width: 900px; margin: 0 auto; }}
  .empty {{ color: var(--muted); padding: 2rem 0; text-align: center; }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.8rem;
    cursor: pointer;
  }}
  .card-head {{ display: flex; justify-content: space-between; align-items: baseline; gap: 0.75rem; }}
  .card-head h2 {{ font-size: 1.05rem; margin: 0; }}
  .badges {{ display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.4rem; }}
  .badge {{
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    color: var(--muted);
    background: var(--accent-soft);
    border-radius: 999px;
    padding: 0.15rem 0.55rem;
  }}
  .body {{
    display: none;
    white-space: pre-wrap;
    margin-top: 0.9rem;
    padding-top: 0.9rem;
    border-top: 1px solid var(--border);
    font-size: 0.92rem;
  }}
  .card.open .body {{ display: block; }}
  .copy-btn {{
    margin-top: 0.7rem;
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.35rem 0.7rem;
    border-radius: 6px;
    font-size: 0.8rem;
    cursor: pointer;
  }}
  .copy-btn:hover {{ border-color: var(--accent); }}
  .id {{ color: var(--muted); font-size: 0.8rem; }}
</style>
</head>
<body>
<header>
  <h1>Maple Press — Piece Library</h1>
  <p>Generated Canada List editorial copy. Click a piece to expand it.</p>
</header>
<div class="controls">
  <input type="text" id="search" placeholder="Search headlines and businesses…">
  <select id="type-filter"><option value="">All types</option></select>
  <select id="tone-filter"><option value="">All tones</option></select>
</div>
<main id="list"></main>

<script type="application/json" id="pieces-data">{payload}</script>
<script>
(function () {{
  var pieces = JSON.parse(document.getElementById('pieces-data').textContent);
  var listEl = document.getElementById('list');
  var searchEl = document.getElementById('search');
  var typeEl = document.getElementById('type-filter');
  var toneEl = document.getElementById('tone-filter');

  function uniqueSorted(values) {{
    var seen = {{}};
    var out = [];
    values.forEach(function (v) {{
      if (v && !seen[v]) {{ seen[v] = true; out.push(v); }}
    }});
    out.sort();
    return out;
  }}

  uniqueSorted(pieces.map(function (p) {{ return p.piece_type; }})).forEach(function (t) {{
    var opt = document.createElement('option');
    opt.value = t;
    opt.textContent = t;
    typeEl.appendChild(opt);
  }});
  uniqueSorted(pieces.map(function (p) {{ return p.tone; }})).forEach(function (t) {{
    var opt = document.createElement('option');
    opt.value = t;
    opt.textContent = t;
    toneEl.appendChild(opt);
  }});

  function businessNames(piece) {{
    return (piece.businesses || []).map(function (b) {{ return b.name; }}).join(' ');
  }}

  function matches(piece, query, typeFilter, toneFilter) {{
    if (typeFilter && piece.piece_type !== typeFilter) return false;
    if (toneFilter && piece.tone !== toneFilter) return false;
    if (!query) return true;
    var haystack = (piece.headline + ' ' + businessNames(piece)).toLowerCase();
    return haystack.indexOf(query.toLowerCase()) !== -1;
  }}

  function buildCard(piece) {{
    var card = document.createElement('div');
    card.className = 'card';

    var head = document.createElement('div');
    head.className = 'card-head';

    var h2 = document.createElement('h2');
    h2.textContent = piece.headline;
    head.appendChild(h2);

    var idSpan = document.createElement('span');
    idSpan.className = 'id';
    idSpan.textContent = '#' + piece.id;
    head.appendChild(idSpan);

    card.appendChild(head);

    var badges = document.createElement('div');
    badges.className = 'badges';
    [piece.piece_type, piece.tone, piece.occasion,
     piece.ai_polished ? 'ai-polished' : 'deterministic'].forEach(function (label) {{
      var badge = document.createElement('span');
      badge.className = 'badge';
      badge.textContent = label;
      badges.appendChild(badge);
    }});
    card.appendChild(badges);

    var bodyEl = document.createElement('div');
    bodyEl.className = 'body';
    bodyEl.textContent = piece.body_markdown;
    card.appendChild(bodyEl);

    var copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.type = 'button';
    copyBtn.textContent = 'Copy as Markdown';
    copyBtn.addEventListener('click', function (event) {{
      event.stopPropagation();
      var text = '# ' + piece.headline + '\\n\\n' + piece.body_markdown;
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(text).catch(function () {{}});
      }}
    }});
    bodyEl.appendChild(document.createElement('br'));
    bodyEl.appendChild(copyBtn);

    card.addEventListener('click', function () {{
      card.classList.toggle('open');
    }});

    return card;
  }}

  function render() {{
    var query = searchEl.value.trim();
    var typeFilter = typeEl.value;
    var toneFilter = toneEl.value;

    while (listEl.firstChild) listEl.removeChild(listEl.firstChild);

    var visible = pieces.filter(function (p) {{
      return matches(p, query, typeFilter, toneFilter);
    }});

    if (visible.length === 0) {{
      var empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = pieces.length === 0
        ? 'No pieces yet. Run "generate" to create your first one.'
        : 'No pieces match your filters.';
      listEl.appendChild(empty);
      return;
    }}

    visible.forEach(function (p) {{ listEl.appendChild(buildCard(p)); }});
  }}

  searchEl.addEventListener('input', render);
  typeEl.addEventListener('change', render);
  toneEl.addEventListener('change', render);

  render();
}})();
</script>
</body>
</html>
"""
