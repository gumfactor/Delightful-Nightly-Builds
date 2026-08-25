"""Self-contained dark-mode HTML dashboard for Grant Vault.

All chunk data is embedded as one JSON blob inside a
<script type="application/json"> tag. The page's own JavaScript parses
that JSON and builds every piece of chunk-derived DOM via
document.createElement / .textContent only -- there is no innerHTML
assignment anywhere in this module or the generated page, so chunk text
(which may contain arbitrary user-ingested content, including HTML-like
strings) can never be interpreted as markup.
"""

import json
import sqlite3
from datetime import datetime, timezone

from src import store

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Grant Vault</title>
<style>
  :root {{
    --bg: #0f1115;
    --bg-elevated: #1a1d24;
    --border: #2a2e37;
    --text: #e6e8eb;
    --text-dim: #9aa1ac;
    --accent: #5b9dff;
    --high: #3ecf8e;
    --medium: #f2b134;
    --low: #f2596b;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }}
  header {{ padding: 1.5rem 1rem; border-bottom: 1px solid var(--border); }}
  h1 {{ margin: 0 0 0.25rem; font-size: 1.5rem; }}
  .subtitle {{ color: var(--text-dim); font-size: 0.9rem; }}
  main {{ max-width: 960px; margin: 0 auto; padding: 1rem; }}
  .controls {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; }}
  input[type="search"] {{
    flex: 1 1 240px;
    padding: 0.6rem 0.8rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-size: 1rem;
  }}
  .tabs {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1rem; }}
  .tab {{
    padding: 0.4rem 0.8rem;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--bg-elevated);
    color: var(--text-dim);
    cursor: pointer;
    font-size: 0.85rem;
  }}
  .tab[aria-selected="true"] {{ background: var(--accent); color: #05070a; border-color: var(--accent); }}
  .chunk-card {{
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.8rem;
  }}
  .chunk-meta {{ display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; font-size: 0.8rem; color: var(--text-dim); }}
  .badge {{ padding: 0.15rem 0.5rem; border-radius: 999px; font-weight: 600; }}
  .badge-high {{ background: rgba(62,207,142,0.15); color: var(--high); }}
  .badge-medium {{ background: rgba(242,177,52,0.15); color: var(--medium); }}
  .badge-low {{ background: rgba(242,89,107,0.15); color: var(--low); }}
  .chunk-text {{ white-space: pre-wrap; margin: 0 0 0.6rem; }}
  .chunk-summary {{ font-style: italic; color: var(--text-dim); margin: 0 0 0.6rem; }}
  .tag-list {{ display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.6rem; }}
  .tag-chip {{ font-size: 0.75rem; padding: 0.1rem 0.5rem; border-radius: 999px; background: var(--bg); border: 1px solid var(--border); color: var(--text-dim); cursor: pointer; }}
  .tag-chip[aria-pressed="true"] {{ border-color: var(--accent); color: var(--accent); }}
  button.copy-btn {{
    font-size: 0.8rem; padding: 0.3rem 0.7rem; border-radius: 6px;
    border: 1px solid var(--border); background: var(--bg); color: var(--text);
    cursor: pointer;
  }}
  .empty-state {{ color: var(--text-dim); text-align: center; padding: 2rem 0; }}
  @media (max-width: 480px) {{
    h1 {{ font-size: 1.2rem; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Grant Vault</h1>
  <p class="subtitle">{doc_count} document(s) &middot; {chunk_count} chunk(s) &middot; generated {generated_at}</p>
</header>
<main>
  <div class="controls">
    <input type="search" id="search-box" placeholder="Search your grant language..." aria-label="Search chunks">
  </div>
  <div class="tabs" id="section-tabs" role="tablist" aria-label="Filter by section"></div>
  <div class="tabs" id="tag-chips" role="group" aria-label="Filter by tag"></div>
  <div id="results"></div>
</main>
<script type="application/json" id="chunk-data">{chunk_json}</script>
<script>
(function () {{
  var raw = document.getElementById('chunk-data').textContent;
  var chunks = JSON.parse(raw);
  var sections = Array.from(new Set(chunks.map(function (c) {{ return c.section_type; }}))).sort();
  var activeSection = 'All';
  var activeTag = null;

  function allTags() {{
    var set = new Set();
    chunks.forEach(function (c) {{ c.tags.forEach(function (t) {{ set.add(t); }}); }});
    return Array.from(set).sort();
  }}

  function tierClass(tier) {{
    if (tier === 'High') return 'badge-high';
    if (tier === 'Medium') return 'badge-medium';
    return 'badge-low';
  }}

  function renderTabs() {{
    var container = document.getElementById('section-tabs');
    container.textContent = '';
    container.appendChild(makeTab('All', activeSection === 'All'));
    sections.forEach(function (section) {{
      container.appendChild(makeTab(section, activeSection === section));
    }});
  }}

  function makeTab(label, selected) {{
    var btn = document.createElement('button');
    btn.className = 'tab';
    btn.type = 'button';
    btn.setAttribute('role', 'tab');
    btn.setAttribute('aria-selected', selected ? 'true' : 'false');
    btn.textContent = label;
    btn.addEventListener('click', function () {{
      activeSection = label;
      renderTabs();
      renderResults();
    }});
    return btn;
  }}

  function renderTagChips() {{
    var container = document.getElementById('tag-chips');
    container.textContent = '';
    allTags().forEach(function (tag) {{
      var chip = document.createElement('button');
      chip.className = 'tag-chip';
      chip.type = 'button';
      chip.setAttribute('aria-pressed', activeTag === tag ? 'true' : 'false');
      chip.textContent = '#' + tag;
      chip.addEventListener('click', function () {{
        activeTag = activeTag === tag ? null : tag;
        renderTagChips();
        renderResults();
      }});
      container.appendChild(chip);
    }});
  }}

  function renderResults() {{
    var query = document.getElementById('search-box').value.trim().toLowerCase();
    var results = document.getElementById('results');
    results.textContent = '';

    var filtered = chunks.filter(function (c) {{
      if (activeSection !== 'All' && c.section_type !== activeSection) return false;
      if (activeTag && c.tags.indexOf(activeTag) === -1) return false;
      if (query && c.text.toLowerCase().indexOf(query) === -1) return false;
      return true;
    }});

    if (filtered.length === 0) {{
      var empty = document.createElement('p');
      empty.className = 'empty-state';
      empty.textContent = 'No chunks match your filters yet.';
      results.appendChild(empty);
      return;
    }}

    filtered.forEach(function (chunk) {{
      results.appendChild(buildCard(chunk));
    }});
  }}

  function buildCard(chunk) {{
    var card = document.createElement('article');
    card.className = 'chunk-card';

    var meta = document.createElement('div');
    meta.className = 'chunk-meta';

    var section = document.createElement('span');
    section.textContent = chunk.section_type;
    meta.appendChild(section);

    var badge = document.createElement('span');
    badge.className = 'badge ' + tierClass(chunk.reuse_tier);
    badge.textContent = chunk.reuse_tier + ' (' + chunk.reuse_score + '/10)';
    meta.appendChild(badge);

    var source = document.createElement('span');
    source.textContent = chunk.document_path;
    meta.appendChild(source);

    card.appendChild(meta);

    if (chunk.ai_summary) {{
      var summary = document.createElement('p');
      summary.className = 'chunk-summary';
      summary.textContent = chunk.ai_summary;
      card.appendChild(summary);
    }}

    var text = document.createElement('p');
    text.className = 'chunk-text';
    text.textContent = chunk.text;
    card.appendChild(text);

    var tagList = document.createElement('div');
    tagList.className = 'tag-list';
    chunk.tags.forEach(function (tag) {{
      var span = document.createElement('span');
      span.className = 'tag-chip';
      span.textContent = '#' + tag;
      tagList.appendChild(span);
    }});
    card.appendChild(tagList);

    var copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.type = 'button';
    copyBtn.textContent = 'Copy';
    copyBtn.addEventListener('click', function () {{
      if (navigator.clipboard) {{
        navigator.clipboard.writeText(chunk.text);
      }}
      copyBtn.textContent = 'Copied!';
      setTimeout(function () {{ copyBtn.textContent = 'Copy'; }}, 1500);
    }});
    card.appendChild(copyBtn);

    return card;
  }}

  document.getElementById('search-box').addEventListener('input', renderResults);

  renderTabs();
  renderTagChips();
  renderResults();
}})();
</script>
</body>
</html>
"""


def _safe_embed_json(data: list[dict]) -> str:
    """Serialize data and neutralize any '</script' sequence within it.

    This is defense-in-depth beyond the textContent-only rendering: even
    though the JSON is only ever read via .textContent client-side, a raw
    '</script>' substring inside a chunk's text would otherwise terminate
    the embedding <script> tag at the HTML-parser level before any
    JavaScript runs.
    """
    raw = json.dumps(data)
    return raw.replace("</", "<\\/")


def render_html(conn: sqlite3.Connection, output_path: str) -> None:
    chunks = store.get_all_chunks(conn)
    document_paths = {chunk["document_path"] for chunk in chunks}

    html = _HTML_TEMPLATE.format(
        doc_count=len(document_paths),
        chunk_count=len(chunks),
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        chunk_json=_safe_embed_json(chunks),
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
