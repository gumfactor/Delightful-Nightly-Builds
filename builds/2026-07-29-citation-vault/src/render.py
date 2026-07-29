"""Self-contained dark-mode HTML dashboard generator.

All paper-derived text reaches the page only as JSON data inside a
<script type="application/json"> block; the client-side JS below renders it
exclusively via textContent/createElement, never innerHTML, so no
user-supplied string (title, author, note, tag) can execute as markup.
"""

import json

STATUS_COLUMNS = [
    ("to-read", "To Read"),
    ("reading", "Reading"),
    ("read", "Read"),
    ("cited", "Cited"),
]


def _safe_json_for_script_tag(data) -> str:
    # Prevent a paper's title/note/abstract containing "</script>" from closing
    # the embedding <script> tag early.
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def render_dashboard(papers: list, notes_by_paper: dict) -> str:
    """papers: list of paper dicts. notes_by_paper: {paper_id: [note dict, ...]}."""
    payload = {
        "papers": papers,
        "notes": {str(pid): notes for pid, notes in notes_by_paper.items()},
    }
    data_json = _safe_json_for_script_tag(payload)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Citation Vault</title>
<style>
{_CSS}
</style>
</head>
<body>
<div class="app">
  <header class="topbar">
    <h1>Citation Vault</h1>
    <input id="search-box" type="text" placeholder="Search title, author, abstract...">
  </header>

  <div class="tagbar" id="tagbar"></div>

  <main class="board" id="board"></main>
</div>

<div class="detail-overlay" id="detail-overlay">
  <div class="detail-panel" id="detail-panel"></div>
</div>

<script id="paper-data" type="application/json">{data_json}</script>
<script>
{_JS}
</script>
</body>
</html>
"""


_CSS = """
:root {
  --bg: #0f1115;
  --panel: #171a21;
  --border: #2a2e38;
  --text: #e6e8ec;
  --muted: #9aa1ac;
  --accent: #6ea8fe;
  --to-read: #6ea8fe;
  --reading: #f0b429;
  --read: #4caf50;
  --cited: #a370f0;
}
@media (prefers-color-scheme: light) {
  :root {
    --bg: #f5f6f8;
    --panel: #ffffff;
    --border: #dde1e7;
    --text: #1a1d23;
    --muted: #5b6270;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
}
.app { max-width: 1200px; margin: 0 auto; padding: 16px; }
.topbar {
  display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
  justify-content: space-between; margin-bottom: 12px;
}
.topbar h1 { font-size: 1.4rem; margin: 0; }
#search-box {
  flex: 1; min-width: 200px; max-width: 360px; padding: 8px 12px;
  background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
  color: var(--text); font-size: 0.95rem;
}
.tagbar { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
.tag-chip {
  padding: 4px 10px; border-radius: 999px; border: 1px solid var(--border);
  background: var(--panel); color: var(--muted); font-size: 0.8rem; cursor: pointer;
}
.tag-chip.active { border-color: var(--accent); color: var(--accent); }
.board {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
}
@media (max-width: 800px) {
  .board { grid-template-columns: 1fr; }
}
.column {
  background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
  padding: 10px; min-height: 120px;
}
.column-header {
  font-weight: 600; font-size: 0.85rem; text-transform: uppercase;
  letter-spacing: 0.04em; margin-bottom: 8px; display: flex; justify-content: space-between;
}
.card {
  background: var(--bg); border: 1px solid var(--border); border-left: 3px solid var(--accent);
  border-radius: 8px; padding: 10px; margin-bottom: 8px; cursor: pointer;
}
.card:hover { border-color: var(--accent); }
.card-title { font-size: 0.9rem; font-weight: 600; margin-bottom: 4px; }
.card-meta { font-size: 0.78rem; color: var(--muted); }
.card-tags { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
.card-tags span {
  font-size: 0.7rem; background: var(--panel); border: 1px solid var(--border);
  border-radius: 999px; padding: 1px 7px; color: var(--muted);
}
.empty-note { color: var(--muted); font-size: 0.8rem; padding: 8px 0; }
.detail-overlay {
  display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  align-items: center; justify-content: center; padding: 16px; z-index: 10;
}
.detail-overlay.open { display: flex; }
.detail-panel {
  background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
  padding: 20px; max-width: 640px; width: 100%; max-height: 85vh; overflow-y: auto;
}
.detail-panel h2 { margin-top: 0; }
.detail-close {
  float: right; background: none; border: 1px solid var(--border); color: var(--text);
  border-radius: 6px; padding: 4px 10px; cursor: pointer;
}
.note-item {
  border-top: 1px solid var(--border); padding: 8px 0; font-size: 0.88rem;
}
.note-time { color: var(--muted); font-size: 0.75rem; }
.copy-btn {
  margin-top: 12px; padding: 6px 12px; border-radius: 6px; border: 1px solid var(--accent);
  background: transparent; color: var(--accent); cursor: pointer;
}
"""

_JS = """
const raw = document.getElementById('paper-data').textContent;
const data = JSON.parse(raw);
const papers = data.papers;
const notesByPaper = data.notes;

const STATUS_COLUMNS = [
  ['to-read', 'To Read'],
  ['reading', 'Reading'],
  ['read', 'Read'],
  ['cited', 'Cited'],
];

let activeTag = null;
let searchTerm = '';

function allTags() {
  const s = new Set();
  papers.forEach(p => (p.tags || []).forEach(t => s.add(t)));
  return Array.from(s).sort();
}

function matchesFilters(p) {
  if (activeTag && !(p.tags || []).includes(activeTag)) return false;
  if (searchTerm) {
    const hay = (p.title + ' ' + (p.authors || []).join(' ') + ' ' + (p.abstract || '')).toLowerCase();
    if (!hay.includes(searchTerm.toLowerCase())) return false;
  }
  return true;
}

function renderTagbar() {
  const bar = document.getElementById('tagbar');
  bar.textContent = '';
  allTags().forEach(tag => {
    const chip = document.createElement('button');
    chip.className = 'tag-chip' + (tag === activeTag ? ' active' : '');
    chip.textContent = tag;
    chip.addEventListener('click', () => {
      activeTag = (activeTag === tag) ? null : tag;
      renderAll();
    });
    bar.appendChild(chip);
  });
}

function renderBoard() {
  const board = document.getElementById('board');
  board.textContent = '';
  STATUS_COLUMNS.forEach(([status, label]) => {
    const col = document.createElement('div');
    col.className = 'column';

    const header = document.createElement('div');
    header.className = 'column-header';
    const labelSpan = document.createElement('span');
    labelSpan.textContent = label;
    header.appendChild(labelSpan);

    const filtered = papers.filter(p => p.status === status && matchesFilters(p));
    const countSpan = document.createElement('span');
    countSpan.textContent = String(filtered.length);
    header.appendChild(countSpan);
    col.appendChild(header);

    if (filtered.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'empty-note';
      empty.textContent = 'Nothing here.';
      col.appendChild(empty);
    }

    filtered.forEach(p => {
      const card = document.createElement('div');
      card.className = 'card';
      card.addEventListener('click', () => openDetail(p.id));

      const title = document.createElement('div');
      title.className = 'card-title';
      title.textContent = p.title;
      card.appendChild(title);

      const meta = document.createElement('div');
      meta.className = 'card-meta';
      meta.textContent = (p.authors && p.authors.length ? p.authors.join(', ') : 'Unknown author') +
        (p.year ? ' (' + p.year + ')' : '');
      card.appendChild(meta);

      if (p.tags && p.tags.length) {
        const tagsWrap = document.createElement('div');
        tagsWrap.className = 'card-tags';
        p.tags.forEach(t => {
          const chip = document.createElement('span');
          chip.textContent = t;
          tagsWrap.appendChild(chip);
        });
        card.appendChild(tagsWrap);
      }

      col.appendChild(card);
    });

    board.appendChild(col);
  });
}

function bibtexEscape(text) {
  if (!text) return '';
  return text.replace(/[\\\\{}&%$#_]/g, c => ({
    '\\\\': '\\\\textbackslash{}', '{': '\\\\{', '}': '\\\\}', '&': '\\\\&',
    '%': '\\\\%', '$': '\\\\$', '#': '\\\\#', '_': '\\\\_'
  })[c]);
}

function bibtexFor(p) {
  const lastName = (p.authors && p.authors[0]) ? p.authors[0].split(' ').pop() : 'anon';
  const key = (lastName.toLowerCase().replace(/[^a-z0-9]/g, '') || 'anon') + (p.year || 'nd');
  const authorField = (p.authors && p.authors.length ? p.authors.map(bibtexEscape).join(' and ') : 'Unknown');
  let entry = '@article{' + key + ',\\n';
  entry += '  title = {' + bibtexEscape(p.title) + '},\\n';
  entry += '  author = {' + authorField + '},\\n';
  if (p.year) entry += '  year = {' + p.year + '},\\n';
  if (p.journal) entry += '  journal = {' + bibtexEscape(p.journal) + '},\\n';
  if (p.doi) entry += '  doi = {' + p.doi + '},\\n';
  entry += '}';
  return entry;
}

function openDetail(paperId) {
  const p = papers.find(x => x.id === paperId);
  if (!p) return;
  const overlay = document.getElementById('detail-overlay');
  const panel = document.getElementById('detail-panel');
  panel.textContent = '';

  const closeBtn = document.createElement('button');
  closeBtn.className = 'detail-close';
  closeBtn.textContent = 'Close';
  closeBtn.addEventListener('click', () => overlay.classList.remove('open'));
  panel.appendChild(closeBtn);

  const h2 = document.createElement('h2');
  h2.textContent = p.title;
  panel.appendChild(h2);

  const meta = document.createElement('div');
  meta.className = 'card-meta';
  meta.textContent = (p.authors && p.authors.length ? p.authors.join(', ') : 'Unknown author') +
    (p.year ? ' (' + p.year + ')' : '') + (p.journal ? ' — ' + p.journal : '');
  panel.appendChild(meta);

  if (p.abstract) {
    const abs = document.createElement('p');
    abs.textContent = p.abstract;
    panel.appendChild(abs);
  }

  if (p.tags && p.tags.length) {
    const tagsWrap = document.createElement('div');
    tagsWrap.className = 'card-tags';
    p.tags.forEach(t => {
      const chip = document.createElement('span');
      chip.textContent = t;
      tagsWrap.appendChild(chip);
    });
    panel.appendChild(tagsWrap);
  }

  const notesHeader = document.createElement('h3');
  notesHeader.textContent = 'Notes';
  panel.appendChild(notesHeader);

  const notes = notesByPaper[String(paperId)] || [];
  if (notes.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-note';
    empty.textContent = 'No notes yet.';
    panel.appendChild(empty);
  }
  notes.forEach(n => {
    const item = document.createElement('div');
    item.className = 'note-item';
    const time = document.createElement('div');
    time.className = 'note-time';
    time.textContent = n.created_at;
    item.appendChild(time);
    const text = document.createElement('div');
    text.textContent = n.text;
    item.appendChild(text);
    panel.appendChild(item);
  });

  const copyBtn = document.createElement('button');
  copyBtn.className = 'copy-btn';
  copyBtn.textContent = 'Copy BibTeX';
  copyBtn.addEventListener('click', () => {
    const bib = bibtexFor(p);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(bib).catch(() => {});
    }
    copyBtn.textContent = 'Copied!';
    setTimeout(() => { copyBtn.textContent = 'Copy BibTeX'; }, 1500);
  });
  panel.appendChild(copyBtn);

  overlay.classList.add('open');
}

document.getElementById('detail-overlay').addEventListener('click', (e) => {
  if (e.target.id === 'detail-overlay') e.target.classList.remove('open');
});

document.getElementById('search-box').addEventListener('input', (e) => {
  searchTerm = e.target.value;
  renderBoard();
});

function renderAll() {
  renderTagbar();
  renderBoard();
}

renderAll();
"""
