"""Render the Connectome knowledge base as a single self-contained HTML file."""

from __future__ import annotations

import html
import json
import os
import sqlite3

import storage

MAX_TAG_CLOUD = 40


def _safe_json(data) -> str:
    """JSON-encode data for embedding inside a <script type="application/json"> tag.

    Escapes '</' to '<\\/' (a JSON-legal escape for '/') so a note containing a
    literal '</script>' string can never terminate the surrounding tag early —
    the HTML parser scans for that byte sequence before any JS/JSON parsing
    happens, regardless of the script tag's type attribute.
    """
    raw = json.dumps(data, ensure_ascii=False)
    return raw.replace("</", "<\\/")


def _escaped_body_html(body: str) -> str:
    """Escape a note body for safe static embedding, preserving line breaks."""
    return html.escape(body).replace("\n", "<br>")


def build_data(conn: sqlite3.Connection) -> dict:
    notes = storage.all_notes(conn)
    doc_freq = storage.get_doc_frequencies(conn)
    all_links = storage.get_all_links(conn)
    categories = storage.get_categories(conn)

    note_concepts = {row["id"]: storage.get_note_concepts(conn, row["id"]) for row in notes}
    link_counts: dict[int, int] = {}
    for link in all_links:
        link_counts[link.note_a] = link_counts.get(link.note_a, 0) + 1
        link_counts[link.note_b] = link_counts.get(link.note_b, 0) + 1

    notes_payload = []
    for row in notes:
        concepts = sorted(note_concepts[row["id"]].items(), key=lambda p: p[1], reverse=True)
        snippet = row["body"].strip().splitlines()[0][:160] if row["body"].strip() else ""
        notes_payload.append({
            "id": row["id"],
            "title": row["title"],
            "path": row["path"],
            "category": row["category"],
            "subcategory": row["subcategory"],
            "snippet": snippet,
            "concepts": [term for term, _ in concepts[:8]],
            "link_count": link_counts.get(row["id"], 0),
        })

    tag_cloud = sorted(doc_freq.items(), key=lambda p: p[1], reverse=True)[:MAX_TAG_CLOUD]

    links_payload = [
        {
            "source": link.note_a,
            "target": link.note_b,
            "score": round(link.score, 4),
            "shared": link.shared_concepts[:5],
        }
        for link in all_links
    ]

    return {
        "notes": notes_payload,
        "categories": categories,
        "tag_cloud": [{"term": term, "count": count} for term, count in tag_cloud],
        "links": links_payload,
    }


def render_knowledge_base(conn: sqlite3.Connection, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    data = build_data(conn)
    notes = storage.all_notes(conn)

    detail_divs = []
    for row in notes:
        meta = html.escape(row["category"])
        if row["subcategory"]:
            meta += " · " + html.escape(row["subcategory"])
        detail_divs.append(
            f'<div class="note-detail" data-note-id="{row["id"]}" hidden>'
            f'<h2>{html.escape(row["title"])}</h2>'
            f'<div class="note-meta">{meta}</div>'
            f'<div class="note-path">{html.escape(row["path"])}</div>'
            f'<div class="note-body">{_escaped_body_html(row["body"])}</div>'
            f'</div>'
        )

    html_doc = _PAGE_TEMPLATE.format(
        detail_divs="\n".join(detail_divs),
        data_json=_safe_json(data),
    )

    output_path = os.path.join(output_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return output_path


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Connectome — Personal Knowledge Graph</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{
    --bg: #0f1117; --panel: #171a23; --border: #2a2e3a; --text: #e6e8ee;
    --muted: #9298a8; --accent: #6ea8fe; --accent-dim: #2f4a72;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg); color: var(--text);
  }}
  header {{ padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border); }}
  header h1 {{ margin: 0; font-size: 1.3rem; }}
  header p {{ margin: 0.25rem 0 0; color: var(--muted); font-size: 0.9rem; }}
  .layout {{ display: flex; flex-wrap: wrap; gap: 1rem; padding: 1rem 1.5rem; max-width: 1400px; margin: 0 auto; }}
  .col {{ flex: 1 1 320px; min-width: 280px; }}
  .panel {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem; margin-bottom: 1rem; overflow-x: auto;
  }}
  .panel h2 {{ margin-top: 0; font-size: 1rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }}
  input[type="search"] {{
    width: 100%; padding: 0.5rem 0.75rem; border-radius: 6px; border: 1px solid var(--border);
    background: #0c0e13; color: var(--text); font-size: 0.95rem;
  }}
  .note-item {{
    padding: 0.6rem 0.5rem; border-radius: 6px; cursor: pointer; border: 1px solid transparent;
  }}
  .note-item:hover, .note-item.active {{ background: var(--accent-dim); border-color: var(--accent); }}
  .note-item .title {{ font-weight: 600; }}
  .note-item .snippet {{ color: var(--muted); font-size: 0.85rem; }}
  .tag {{
    display: inline-block; margin: 0.15rem; padding: 0.2rem 0.55rem; border-radius: 999px;
    background: #232838; color: var(--accent); font-size: 0.8rem; cursor: pointer; border: 1px solid var(--border);
  }}
  .tag.active {{ background: var(--accent); color: #0c0e13; }}
  .category-chip {{
    display: inline-flex; align-items: center; gap: 0.35rem; margin: 0.15rem; padding: 0.2rem 0.6rem;
    border-radius: 999px; background: #232838; font-size: 0.8rem; cursor: pointer; border: 1px solid var(--border);
  }}
  .category-chip .dot {{ width: 0.6rem; height: 0.6rem; border-radius: 50%; flex-shrink: 0; }}
  .category-chip.active {{ border-color: var(--accent); background: var(--accent-dim); }}
  .note-item .item-meta {{ color: var(--muted); font-size: 0.75rem; margin-top: 0.1rem; }}
  .note-detail h2 {{ margin-top: 0; color: var(--text); text-transform: none; letter-spacing: 0; font-size: 1.15rem; }}
  .note-meta {{ color: var(--muted); font-size: 0.8rem; margin-bottom: 0.25rem; }}
  .note-path {{ color: var(--muted); font-size: 0.8rem; margin-bottom: 0.75rem; }}
  .note-body {{ line-height: 1.5; white-space: normal; }}
  .related-list {{ margin-top: 1rem; }}
  .related-list li {{ margin-bottom: 0.4rem; cursor: pointer; }}
  .related-list .score {{ color: var(--muted); font-size: 0.8rem; }}
  canvas {{ display: block; width: 100%; height: 360px; background: #0c0e13; border-radius: 8px; }}
  #graph-legend {{ margin-top: 0.6rem; }}
  .empty {{ color: var(--muted); font-style: italic; }}
</style>
</head>
<body>
<header>
  <h1>Connectome</h1>
  <p>Personal knowledge graph — search, browse, and see how your notes connect.</p>
</header>
<div class="layout">
  <div class="col">
    <div class="panel">
      <h2>Search</h2>
      <input type="search" id="search-box" placeholder="Search notes and concepts...">
      <div id="note-list" style="margin-top: 0.75rem;"></div>
    </div>
    <div class="panel">
      <h2>Category</h2>
      <div id="category-filter"></div>
    </div>
    <div class="panel">
      <h2>Tag Cloud</h2>
      <div id="tag-cloud"></div>
    </div>
  </div>
  <div class="col" style="flex: 2 1 480px;">
    <div class="panel" id="detail-panel">
      <h2>Note</h2>
      <div id="detail-container"><p class="empty">Select a note to view it.</p></div>
      <div class="related-list" id="related-container"></div>
    </div>
  </div>
  <div class="col">
    <div class="panel">
      <h2>Concept Graph</h2>
      <canvas id="graph-canvas" width="360" height="360"></canvas>
      <p class="empty" id="graph-empty" hidden>No links yet — index more notes to see connections.</p>
      <div id="graph-legend"></div>
    </div>
  </div>
</div>

{detail_divs}

<script type="application/json" id="connectome-data">{data_json}</script>
<script>
(function() {{
  const DATA = JSON.parse(document.getElementById('connectome-data').textContent);
  const noteById = Object.fromEntries(DATA.notes.map(n => [n.id, n]));
  const CATEGORY_COLORS = ['#f2b632', '#5fd0a0', '#e0708c', '#8f9bff', '#5fc4d0', '#d98f4a'];
  function categoryColor(name) {{
    const idx = DATA.categories.indexOf(name);
    return CATEGORY_COLORS[(idx < 0 ? 0 : idx) % CATEGORY_COLORS.length];
  }}
  let activeTag = null;
  let activeCategory = null;

  function renderNoteList(filterText) {{
    const list = document.getElementById('note-list');
    list.innerHTML = '';
    const q = (filterText || '').toLowerCase();
    const filtered = DATA.notes.filter(n => {{
      const matchesTag = !activeTag || n.concepts.includes(activeTag);
      const matchesCategory = !activeCategory || n.category === activeCategory;
      const matchesText = !q || n.title.toLowerCase().includes(q) ||
        n.snippet.toLowerCase().includes(q) || n.concepts.some(c => c.includes(q));
      return matchesTag && matchesCategory && matchesText;
    }});
    if (filtered.length === 0) {{
      list.innerHTML = '<p class="empty">No notes match.</p>';
      return;
    }}
    for (const note of filtered) {{
      const item = document.createElement('div');
      item.className = 'note-item';
      item.dataset.noteId = note.id;
      const title = document.createElement('div');
      title.className = 'title';
      title.textContent = note.title;
      const snippet = document.createElement('div');
      snippet.className = 'snippet';
      snippet.textContent = note.snippet;
      const meta = document.createElement('div');
      meta.className = 'item-meta';
      meta.textContent = note.category + (note.subcategory ? ' · ' + note.subcategory : '');
      item.appendChild(title);
      item.appendChild(snippet);
      item.appendChild(meta);
      item.addEventListener('click', () => showNote(note.id));
      list.appendChild(item);
    }}
  }}

  function renderCategoryFilter() {{
    const container = document.getElementById('category-filter');
    container.innerHTML = '';
    if (DATA.categories.length <= 1) {{
      container.innerHTML = '<p class="empty">Only one category indexed.</p>';
      return;
    }}
    for (const category of DATA.categories) {{
      const chip = document.createElement('span');
      chip.className = 'category-chip' + (category === activeCategory ? ' active' : '');
      const dot = document.createElement('span');
      dot.className = 'dot';
      dot.style.background = categoryColor(category);
      const label = document.createElement('span');
      label.textContent = category;
      chip.appendChild(dot);
      chip.appendChild(label);
      chip.addEventListener('click', () => {{
        activeCategory = (activeCategory === category) ? null : category;
        renderCategoryFilter();
        renderNoteList(document.getElementById('search-box').value);
      }});
      container.appendChild(chip);
    }}
  }}

  function renderGraphLegend() {{
    const legend = document.getElementById('graph-legend');
    legend.innerHTML = '';
    if (DATA.categories.length <= 1) return;
    for (const category of DATA.categories) {{
      const entry = document.createElement('span');
      entry.className = 'category-chip';
      entry.style.cursor = 'default';
      const dot = document.createElement('span');
      dot.className = 'dot';
      dot.style.background = categoryColor(category);
      const label = document.createElement('span');
      label.textContent = category;
      entry.appendChild(dot);
      entry.appendChild(label);
      legend.appendChild(entry);
    }}
  }}

  function renderTagCloud() {{
    const cloud = document.getElementById('tag-cloud');
    cloud.innerHTML = '';
    for (const entry of DATA.tag_cloud) {{
      const tag = document.createElement('span');
      tag.className = 'tag' + (entry.term === activeTag ? ' active' : '');
      tag.textContent = entry.term + ' (' + entry.count + ')';
      tag.addEventListener('click', () => {{
        activeTag = (activeTag === entry.term) ? null : entry.term;
        renderTagCloud();
        renderNoteList(document.getElementById('search-box').value);
      }});
      cloud.appendChild(tag);
    }}
  }}

  function showNote(noteId) {{
    document.querySelectorAll('.note-detail').forEach(el => el.hidden = true);
    const target = document.querySelector('.note-detail[data-note-id="' + noteId + '"]');
    const container = document.getElementById('detail-container');
    container.innerHTML = '';
    if (target) {{
      container.appendChild(target.cloneNode(true)).hidden = false;
    }}
    document.querySelectorAll('.note-item').forEach(el => {{
      el.classList.toggle('active', String(el.dataset.noteId) === String(noteId));
    }});
    renderRelated(noteId);
    drawGraph(noteId);
  }}

  function renderRelated(noteId) {{
    const relatedContainer = document.getElementById('related-container');
    relatedContainer.innerHTML = '';
    const links = DATA.links.filter(l => l.source === noteId || l.target === noteId);
    if (links.length === 0) {{
      relatedContainer.innerHTML = '<p class="empty">No related notes yet.</p>';
      return;
    }}
    const heading = document.createElement('h2');
    heading.textContent = 'Related notes';
    relatedContainer.appendChild(heading);
    const ul = document.createElement('ul');
    links.sort((a, b) => b.score - a.score);
    for (const link of links) {{
      const otherId = link.source === noteId ? link.target : link.source;
      const other = noteById[otherId];
      if (!other) continue;
      const li = document.createElement('li');
      const label = document.createElement('span');
      label.textContent = other.title + ' ';
      const score = document.createElement('span');
      score.className = 'score';
      score.textContent = '(shared: ' + link.shared.join(', ') + ')';
      li.appendChild(label);
      li.appendChild(score);
      li.addEventListener('click', () => showNote(otherId));
      ul.appendChild(li);
    }}
    relatedContainer.appendChild(ul);
  }}

  function drawGraph(highlightId) {{
    const canvas = document.getElementById('graph-canvas');
    const ctx = canvas.getContext('2d');
    const emptyMsg = document.getElementById('graph-empty');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (DATA.notes.length === 0) {{ emptyMsg.hidden = false; return; }}
    emptyMsg.hidden = true;

    const cx = canvas.width / 2, cy = canvas.height / 2;
    const radius = Math.min(cx, cy) - 30;
    const n = DATA.notes.length;
    const positions = {{}};
    DATA.notes.forEach((note, i) => {{
      const angle = (2 * Math.PI * i) / n;
      positions[note.id] = {{
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      }};
    }});

    ctx.lineWidth = 1;
    for (const link of DATA.links) {{
      const a = positions[link.source], b = positions[link.target];
      if (!a || !b) continue;
      const isHighlighted = highlightId && (link.source === highlightId || link.target === highlightId);
      ctx.strokeStyle = isHighlighted ? '#6ea8fe' : 'rgba(110,168,254,0.25)';
      ctx.lineWidth = isHighlighted ? 2 : 1;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }}

    for (const note of DATA.notes) {{
      const pos = positions[note.id];
      const size = 4 + Math.min(note.link_count, 8);
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, size, 0, 2 * Math.PI);
      ctx.fillStyle = note.id === highlightId ? '#6ea8fe' : categoryColor(note.category);
      ctx.fill();
      ctx.strokeStyle = '#e6e8ee';
      ctx.lineWidth = note.id === highlightId ? 2 : 0.5;
      ctx.stroke();
    }}
  }}

  document.getElementById('graph-canvas').addEventListener('click', (event) => {{
    const rect = event.target.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const cx = event.target.width / 2, cy = event.target.height / 2;
    const radius = Math.min(cx, cy) - 30;
    const n = DATA.notes.length;
    let closest = null, closestDist = Infinity;
    DATA.notes.forEach((note, i) => {{
      const angle = (2 * Math.PI * i) / n;
      const px = cx + radius * Math.cos(angle), py = cy + radius * Math.sin(angle);
      const dist = Math.hypot(px - x, py - y);
      if (dist < closestDist) {{ closestDist = dist; closest = note; }}
    }});
    if (closest && closestDist < 20) showNote(closest.id);
  }});

  document.getElementById('search-box').addEventListener('input', (e) => renderNoteList(e.target.value));

  renderNoteList('');
  renderCategoryFilter();
  renderTagCloud();
  renderGraphLegend();
  drawGraph(null);
  if (DATA.notes.length > 0) showNote(DATA.notes[0].id);
}})();
</script>
</body>
</html>
"""
