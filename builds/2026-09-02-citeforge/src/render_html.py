"""Self-contained dark-mode HTML bibliography report.

Reference data is delivered to the page as a JSON payload inside a
`<script type="application/json">` tag (with '</' escaped so a malicious
title can never prematurely close the tag) and built into the DOM
exclusively with `createElement`/`textContent` — never `innerHTML` — so
injected markup in a title/author/journal name can never execute.
"""

from __future__ import annotations

import json

from . import styles
from .models import Reference


def _escape_for_script_tag(json_text: str) -> str:
    return json_text.replace("</", "<\\/")


def _build_payload(refs: list[Reference]) -> list[dict]:
    payload = []
    for ref in refs:
        authors_display = ", ".join(a.family for a in ref.authors) or "(no authors)"
        style_outputs = {key: module.format_reference(ref) for key, module in styles.STYLES.items()}
        payload.append(
            {
                "id": ref.ref_id,
                "authors": authors_display,
                "year": ref.year or "n.d.",
                "title": ref.title,
                "ref_type": ref.ref_type,
                "needs_review": ref.needs_review,
                "styles": style_outputs,
            }
        )
    return payload


def render(refs: list[Reference]) -> str:
    payload_json = _escape_for_script_tag(json.dumps(_build_payload(refs)))
    style_labels_json = _escape_for_script_tag(json.dumps(styles.STYLE_LABELS))
    html = _TEMPLATE
    html = html.replace("__PAYLOAD_JSON__", payload_json)
    html = html.replace("__STYLE_LABELS_JSON__", style_labels_json)
    html = html.replace("__COUNT__", str(len(refs)))
    return html


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CiteForge Report</title>
<style>
  :root {
    --bg: #0f1115; --panel: #1a1d24; --border: #2a2e37; --text: #e6e8eb;
    --muted: #9aa1ac; --accent: #6ea8fe; --code-bg: #12141a;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 24px; line-height: 1.5;
  }
  h1 { font-size: 1.4rem; margin-bottom: 4px; }
  .subtitle { color: var(--muted); margin-bottom: 20px; font-size: 0.9rem; }
  input#search {
    width: 100%; max-width: 480px; padding: 10px 12px; margin-bottom: 20px;
    background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
    color: var(--text); font-size: 0.95rem;
  }
  .card {
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 18px; margin-bottom: 16px;
  }
  .card h2 { font-size: 1.02rem; margin: 0 0 4px; word-break: break-word; }
  .card .meta { color: var(--muted); font-size: 0.85rem; margin-bottom: 12px; }
  .review-badge {
    display: inline-block; background: #4a3410; color: #f5c065; font-size: 0.75rem;
    padding: 2px 8px; border-radius: 6px; margin-left: 8px; vertical-align: middle;
  }
  .style-block { margin-bottom: 10px; }
  .style-label { font-size: 0.78rem; color: var(--accent); text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 4px; }
  .style-row { display: flex; gap: 10px; align-items: flex-start; }
  .style-text {
    background: var(--code-bg); border: 1px solid var(--border); border-radius: 6px;
    padding: 8px 10px; font-size: 0.88rem; flex: 1; white-space: pre-wrap; word-break: break-word;
  }
  .copy-btn {
    background: var(--border); color: var(--text); border: none; border-radius: 6px;
    padding: 6px 10px; font-size: 0.78rem; cursor: pointer; white-space: nowrap;
  }
  .copy-btn:hover { background: var(--accent); color: #0f1115; }
  .empty { color: var(--muted); }
  em { font-style: italic; }
  @media (max-width: 480px) {
    body { padding: 14px; }
    .style-row { flex-direction: column; }
  }
</style>
</head>
<body>
<h1>CiteForge Report</h1>
<div class="subtitle">__COUNT__ reference(s) — APA 7, AMA 11, Vancouver/ICMJE, Chicago Author-Date 17</div>
<input id="search" type="text" placeholder="Search by author, title, or year...">
<div id="cards"></div>

<script type="application/json" id="ref-data">__PAYLOAD_JSON__</script>
<script type="application/json" id="style-labels">__STYLE_LABELS_JSON__</script>
<script>
(function () {
  var data = JSON.parse(document.getElementById('ref-data').textContent);
  var styleLabels = JSON.parse(document.getElementById('style-labels').textContent);
  var container = document.getElementById('cards');
  var searchBox = document.getElementById('search');

  function renderEmphasisText(text, parentEl) {
    var parts = text.split('*');
    parts.forEach(function (part, i) {
      if (part === '') return;
      if (i % 2 === 1) {
        var em = document.createElement('em');
        em.textContent = part;
        parentEl.appendChild(em);
      } else {
        parentEl.appendChild(document.createTextNode(part));
      }
    });
  }

  function buildCard(ref) {
    var card = document.createElement('div');
    card.className = 'card';

    var h2 = document.createElement('h2');
    h2.textContent = ref.title;
    if (ref.needs_review) {
      var badge = document.createElement('span');
      badge.className = 'review-badge';
      badge.textContent = 'NEEDS REVIEW';
      h2.appendChild(badge);
    }
    card.appendChild(h2);

    var meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = ref.authors + ' — ' + ref.year + ' — [id ' + ref.id + '] ' + ref.ref_type;
    card.appendChild(meta);

    Object.keys(styleLabels).forEach(function (key) {
      var block = document.createElement('div');
      block.className = 'style-block';

      var label = document.createElement('div');
      label.className = 'style-label';
      label.textContent = styleLabels[key];
      block.appendChild(label);

      var row = document.createElement('div');
      row.className = 'style-row';

      var textEl = document.createElement('div');
      textEl.className = 'style-text';
      var formatted = ref.styles[key] || '';
      renderEmphasisText(formatted, textEl);
      row.appendChild(textEl);

      var btn = document.createElement('button');
      btn.className = 'copy-btn';
      btn.type = 'button';
      btn.textContent = 'Copy';
      btn.addEventListener('click', function () {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(formatted);
          btn.textContent = 'Copied!';
          setTimeout(function () { btn.textContent = 'Copy'; }, 1200);
        }
      });
      row.appendChild(btn);

      block.appendChild(row);
      card.appendChild(block);
    });

    return card;
  }

  function renderAll(filterText) {
    container.textContent = '';
    var q = (filterText || '').toLowerCase();
    var matches = data.filter(function (ref) {
      if (!q) return true;
      return (ref.authors + ' ' + ref.title + ' ' + ref.year).toLowerCase().indexOf(q) !== -1;
    });
    if (matches.length === 0) {
      var empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = 'No references match your search.';
      container.appendChild(empty);
      return;
    }
    matches.forEach(function (ref) { container.appendChild(buildCard(ref)); });
  }

  searchBox.addEventListener('input', function () { renderAll(searchBox.value); });
  renderAll('');
})();
</script>
</body>
</html>
"""
