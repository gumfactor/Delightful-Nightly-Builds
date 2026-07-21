"""Renders the analogy library to a single self-contained, dark-mode HTML
file. All entry text is delivered to the browser as JSON and inserted via
`textContent`/`createElement` on the client side — never `innerHTML` — so
generated or AI-polished text can never execute as markup.
"""

from __future__ import annotations

import json
from typing import Iterable

_PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bridgework — Analogy Library</title>
<style>
  :root {
    --bg: #12141a; --panel: #1b1e27; --border: #2c303c; --text: #e6e8ee;
    --muted: #9aa1b4; --accent: #7db8ff; --accent-2: #c9a4ff; --chip: #262a35;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  header { padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border); }
  header h1 { margin: 0 0 0.25rem; font-size: 1.4rem; }
  header p { margin: 0; color: var(--muted); font-size: 0.9rem; }
  .controls {
    display: flex; flex-wrap: wrap; gap: 0.5rem; padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--border);
  }
  .controls input, .controls select {
    background: var(--panel); color: var(--text); border: 1px solid var(--border);
    border-radius: 6px; padding: 0.45rem 0.6rem; font-size: 0.9rem;
  }
  .controls input { flex: 1; min-width: 180px; }
  main { display: grid; grid-template-columns: minmax(280px, 1fr) minmax(320px, 1.4fr); gap: 0; }
  @media (max-width: 800px) { main { grid-template-columns: 1fr; } }
  #list { border-right: 1px solid var(--border); max-height: 80vh; overflow-y: auto; }
  .card {
    padding: 0.9rem 1.25rem; border-bottom: 1px solid var(--border); cursor: pointer;
  }
  .card:hover, .card.active { background: var(--panel); }
  .card .hook { font-size: 0.92rem; margin: 0 0 0.35rem; }
  .chips { display: flex; flex-wrap: wrap; gap: 0.35rem; }
  .chip {
    background: var(--chip); color: var(--muted); border-radius: 999px;
    padding: 0.1rem 0.55rem; font-size: 0.72rem;
  }
  .chip.source-ai { color: var(--accent-2); }
  .chip.source-template { color: var(--accent); }
  #detail { padding: 1.5rem; }
  #detail h2 { margin-top: 0; font-size: 1.15rem; }
  #detail .label { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; margin: 1rem 0 0.25rem; }
  #detail p { line-height: 1.55; margin: 0.25rem 0 0; }
  #detail button {
    margin-top: 1.25rem; background: var(--accent); color: #101216; border: none;
    border-radius: 6px; padding: 0.5rem 0.9rem; font-size: 0.85rem; cursor: pointer; font-weight: 600;
  }
  #copy-status { color: var(--muted); font-size: 0.8rem; margin-left: 0.6rem; }
  .empty { color: var(--muted); padding: 2rem 1.5rem; }
</style>
</head>
<body>
<header>
  <h1>Bridgework — Analogy Library</h1>
  <p>__COUNT__ analogies bridging stress, empathy, and psychopathy neuroscience to everyday domains.</p>
</header>
<div class="controls">
  <input id="search" type="text" placeholder="Search hook, analogy, concept, domain...">
  <select id="filter-subdomain"><option value="">All subdomains</option></select>
  <select id="filter-audience"><option value="">All audiences</option></select>
  <select id="filter-source"><option value="">All sources</option></select>
</div>
<main>
  <div id="list"></div>
  <div id="detail"><p class="empty">Select an analogy from the list.</p></div>
</main>
<script id="data" type="application/json">__DATA_JSON__</script>
<script>
(function () {
  var entries = JSON.parse(document.getElementById('data').textContent);
  var listEl = document.getElementById('list');
  var detailEl = document.getElementById('detail');
  var searchEl = document.getElementById('search');
  var subdomainEl = document.getElementById('filter-subdomain');
  var audienceEl = document.getElementById('filter-audience');
  var sourceEl = document.getElementById('filter-source');
  var activeId = null;

  function unique(field) {
    var seen = {}; var out = [];
    entries.forEach(function (e) { if (!seen[e[field]]) { seen[e[field]] = true; out.push(e[field]); } });
    return out.sort();
  }

  function addOptions(select, values) {
    values.forEach(function (v) {
      var opt = document.createElement('option');
      opt.value = v; opt.textContent = v;
      select.appendChild(opt);
    });
  }
  addOptions(subdomainEl, unique('subdomain'));
  addOptions(audienceEl, unique('audience'));
  addOptions(sourceEl, unique('source'));

  function matches(entry) {
    var q = searchEl.value.trim().toLowerCase();
    if (q) {
      var haystack = (entry.hook + ' ' + entry.analogy + ' ' + entry.concept_name + ' ' + entry.domain_name).toLowerCase();
      if (haystack.indexOf(q) === -1) return false;
    }
    if (subdomainEl.value && entry.subdomain !== subdomainEl.value) return false;
    if (audienceEl.value && entry.audience !== audienceEl.value) return false;
    if (sourceEl.value && entry.source !== sourceEl.value) return false;
    return true;
  }

  function card(entry) {
    var div = document.createElement('div');
    div.className = 'card' + (entry.id === activeId ? ' active' : '');
    div.setAttribute('data-id', entry.id);

    var hook = document.createElement('p');
    hook.className = 'hook';
    hook.textContent = entry.hook;
    div.appendChild(hook);

    var chips = document.createElement('div');
    chips.className = 'chips';
    [entry.concept_name, entry.domain_name, entry.audience].forEach(function (label) {
      var chip = document.createElement('span');
      chip.className = 'chip';
      chip.textContent = label;
      chips.appendChild(chip);
    });
    var sourceChip = document.createElement('span');
    sourceChip.className = 'chip source-' + entry.source;
    sourceChip.textContent = entry.source;
    chips.appendChild(sourceChip);
    div.appendChild(chips);

    div.addEventListener('click', function () { showDetail(entry.id); });
    return div;
  }

  function renderList() {
    listEl.innerHTML = '';
    var filtered = entries.filter(matches);
    if (filtered.length === 0) {
      var empty = document.createElement('p');
      empty.className = 'empty';
      empty.textContent = 'No analogies match these filters.';
      listEl.appendChild(empty);
      return;
    }
    filtered.forEach(function (entry) { listEl.appendChild(card(entry)); });
  }

  function asMarkdown(entry) {
    return '### ' + entry.hook + '\\n\\n' + entry.analogy + '\\n\\n*' + entry.caveat + '*\\n\\n' +
      '_' + entry.concept_name + ' \\u2192 ' + entry.domain_name + ' (' + entry.audience + ', ' + entry.source + ')_';
  }

  function showDetail(id) {
    activeId = id;
    var entry = entries.filter(function (e) { return e.id === id; })[0];
    detailEl.innerHTML = '';
    if (!entry) {
      var empty = document.createElement('p');
      empty.className = 'empty';
      empty.textContent = 'Select an analogy from the list.';
      detailEl.appendChild(empty);
      return;
    }

    var h2 = document.createElement('h2');
    h2.textContent = entry.hook;
    detailEl.appendChild(h2);

    var meta = document.createElement('div');
    meta.className = 'chips';
    [entry.concept_name, entry.domain_name, entry.audience, entry.source].forEach(function (label) {
      var chip = document.createElement('span');
      chip.className = 'chip';
      chip.textContent = label;
      meta.appendChild(chip);
    });
    detailEl.appendChild(meta);

    [['Analogy', entry.analogy], ['Where it breaks down', entry.caveat]].forEach(function (pair) {
      var label = document.createElement('div');
      label.className = 'label';
      label.textContent = pair[0];
      detailEl.appendChild(label);
      var p = document.createElement('p');
      p.textContent = pair[1];
      detailEl.appendChild(p);
    });

    var button = document.createElement('button');
    button.textContent = 'Copy as Markdown';
    var status = document.createElement('span');
    status.id = 'copy-status';
    button.addEventListener('click', function () {
      var md = asMarkdown(entry);
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(md).then(function () {
          status.textContent = 'Copied.';
        }, function () {
          status.textContent = 'Copy failed — select and copy manually.';
        });
      } else {
        status.textContent = 'Clipboard unavailable — select and copy manually.';
      }
    });
    detailEl.appendChild(button);
    detailEl.appendChild(status);

    renderList();
  }

  [searchEl, subdomainEl, audienceEl, sourceEl].forEach(function (el) {
    el.addEventListener('input', renderList);
    el.addEventListener('change', renderList);
  });

  renderList();
})();
</script>
</body>
</html>
"""


def _safe_json_for_script(entries: Iterable[dict]) -> str:
    """JSON-encode entries for embedding inside an inline <script> tag,
    escaping any '</' sequence so a malicious analogy string can never
    close the surrounding script tag early."""
    return json.dumps(list(entries)).replace("</", "<\\/")


def render_html(entries: Iterable[dict]) -> str:
    entries = list(entries)
    html_data = _safe_json_for_script(entries)
    page = _PAGE_TEMPLATE.replace("__DATA_JSON__", html_data)
    page = page.replace("__COUNT__", str(len(entries)))
    return page
