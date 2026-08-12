"""Self-contained dark-mode HTML dashboard generator for Snipvault.

All snippet data is embedded as an escaped JSON payload inside a
<script type="application/json"> tag and read back client-side with
JSON.parse + textContent/createElement. No snippet field is ever
string-concatenated directly into the HTML markup.
"""

from __future__ import annotations

import json

from .db import Snippet


def render_html(snippets: list) -> str:
    payload = [
        {
            "id": s.id,
            "title": s.title,
            "language": s.language,
            "code": s.code,
            "description": s.description,
            "tags": s.tags,
            "source": s.source or "",
            "updated_at": s.updated_at,
            "usage_count": s.usage_count,
        }
        for s in snippets
    ]
    data_json = json.dumps(payload, ensure_ascii=False)
    # Escaping only the "</" prefix is insufficient: a payload containing an
    # HTML comment immediately followed by a script tag can drive the HTML
    # tokenizer into its script-data (double-)escaped state, where the real
    # closing script tag merely exits that state instead of ending the
    # element, silently swallowing everything after it (including the
    # bootstrap <script> block below). Replacing every "<" with its JSON
    # unicode escape removes all raw "<" characters from the data block, so
    # no HTML-parser state transition can ever trigger inside it. "<" cannot
    # occur in JSON's own structural syntax, only inside a string value, so
    # this substitution is content-preserving and JSON.parse decodes the
    # escape back to a literal "<".
    LT_ESCAPE = "\\" + "u003c"
    data_json_safe = data_json.replace("<", LT_ESCAPE)

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Snipvault</title>
<style>
  :root {{
    --bg: #0f1115; --panel: #171a21; --border: #262b36; --text: #e6e9ef;
    --muted: #8a93a5; --accent: #5eb0ff; --code-bg: #0b0d11;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }}
  header {{
    padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border);
    display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center;
  }}
  h1 {{ font-size: 1.25rem; margin: 0; margin-right: auto; }}
  input, select {{
    background: var(--panel); color: var(--text); border: 1px solid var(--border);
    border-radius: 6px; padding: 0.5rem 0.75rem; font-size: 0.9rem;
  }}
  #search {{ min-width: 220px; flex: 1; max-width: 420px; }}
  main {{ padding: 1.5rem; max-width: 960px; margin: 0 auto; }}
  .card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem 1.25rem; margin-bottom: 1rem;
  }}
  .card-head {{ display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; flex-wrap: wrap; }}
  .card-title {{ font-weight: 600; font-size: 1.05rem; cursor: pointer; }}
  .meta {{ color: var(--muted); font-size: 0.8rem; }}
  .tags {{ margin-top: 0.35rem; }}
  .tag {{
    display: inline-block; background: #1d2330; color: var(--accent);
    border-radius: 999px; padding: 0.15rem 0.6rem; font-size: 0.75rem; margin: 0.15rem 0.25rem 0 0;
  }}
  pre {{
    background: var(--code-bg); border: 1px solid var(--border); border-radius: 8px;
    padding: 0.75rem; overflow-x: auto; font-size: 0.85rem; margin-top: 0.75rem; display: none;
  }}
  pre.open {{ display: block; }}
  .copy-btn {{
    background: var(--panel); color: var(--accent); border: 1px solid var(--border);
    border-radius: 6px; padding: 0.25rem 0.6rem; font-size: 0.8rem; cursor: pointer; margin-top: 0.5rem;
  }}
  #empty {{ color: var(--muted); text-align: center; padding: 3rem 1rem; }}
  @media (max-width: 600px) {{
    header {{ padding: 1rem; }}
    main {{ padding: 1rem; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Snipvault</h1>
  <input id="search" type="text" placeholder="Search title, tags, description, code...">
  <select id="lang-filter"><option value="">All languages</option></select>
</header>
<main>
  <div id="list"></div>
  <div id="empty" style="display:none">No snippets match.</div>
</main>
<script type="application/json" id="snippet-data">{data_json_safe}</script>
<script>
(function() {{
  var data = JSON.parse(document.getElementById('snippet-data').textContent);

  var langSelect = document.getElementById('lang-filter');
  var langs = Array.from(new Set(data.map(function(s) {{ return s.language; }}))).sort();
  langs.forEach(function(lang) {{
    var opt = document.createElement('option');
    opt.value = lang;
    opt.textContent = lang;
    langSelect.appendChild(opt);
  }});

  function matches(snippet, query, lang) {{
    if (lang && snippet.language !== lang) return false;
    if (!query) return true;
    var haystack = [snippet.title, snippet.description, snippet.tags.join(' '), snippet.code]
      .join(' ').toLowerCase();
    return query.toLowerCase().split(/\\s+/).every(function(term) {{
      return term === '' || haystack.indexOf(term) !== -1;
    }});
  }}

  function buildCard(snippet) {{
    var card = document.createElement('div');
    card.className = 'card';

    var head = document.createElement('div');
    head.className = 'card-head';

    var title = document.createElement('div');
    title.className = 'card-title';
    title.textContent = snippet.title;

    var meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = snippet.language + ' · used ' + snippet.usage_count + 'x · ' + snippet.updated_at.slice(0, 10);

    head.appendChild(title);
    head.appendChild(meta);
    card.appendChild(head);

    if (snippet.description) {{
      var desc = document.createElement('div');
      desc.className = 'meta';
      desc.style.marginTop = '0.35rem';
      desc.textContent = snippet.description;
      card.appendChild(desc);
    }}

    if (snippet.tags.length) {{
      var tagsWrap = document.createElement('div');
      tagsWrap.className = 'tags';
      snippet.tags.forEach(function(tag) {{
        var el = document.createElement('span');
        el.className = 'tag';
        el.textContent = tag;
        tagsWrap.appendChild(el);
      }});
      card.appendChild(tagsWrap);
    }}

    var pre = document.createElement('pre');
    var codeEl = document.createElement('code');
    codeEl.textContent = snippet.code;
    pre.appendChild(codeEl);
    card.appendChild(pre);

    var copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = 'Copy';
    copyBtn.addEventListener('click', function(evt) {{
      evt.stopPropagation();

      function showResult(ok) {{
        copyBtn.textContent = ok ? 'Copied!' : 'Copy failed';
        setTimeout(function() {{ copyBtn.textContent = 'Copy'; }}, 1200);
      }}

      function fallbackCopy() {{
        // navigator.clipboard requires a secure context and is typically
        // unavailable from a file:// origin, which is how this dashboard
        // is opened by default — fall back to a hidden-textarea copy.
        try {{
          var textarea = document.createElement('textarea');
          textarea.value = snippet.code;
          textarea.style.position = 'fixed';
          textarea.style.opacity = '0';
          document.body.appendChild(textarea);
          textarea.focus();
          textarea.select();
          var ok = document.execCommand('copy');
          document.body.removeChild(textarea);
          showResult(ok);
        }} catch (err) {{
          showResult(false);
        }}
      }}

      if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(snippet.code).then(
          function() {{ showResult(true); }},
          fallbackCopy
        );
      }} else {{
        fallbackCopy();
      }}
    }});
    card.appendChild(copyBtn);

    title.addEventListener('click', function() {{
      pre.classList.toggle('open');
    }});

    return card;
  }}

  function render() {{
    var query = document.getElementById('search').value;
    var lang = langSelect.value;
    var list = document.getElementById('list');
    while (list.firstChild) {{ list.removeChild(list.firstChild); }}

    var visible = data.filter(function(s) {{ return matches(s, query, lang); }});
    document.getElementById('empty').style.display = visible.length ? 'none' : 'block';
    visible.forEach(function(s) {{ list.appendChild(buildCard(s)); }});
  }}

  document.getElementById('search').addEventListener('input', render);
  langSelect.addEventListener('change', render);
  render();
}})();
</script>
</body>
</html>
"""
