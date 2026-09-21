"""Self-contained dark-mode HTML dashboard for Star Atlas.

Repo data is embedded as JSON inside a <script type="application/json">
block. The page's own JavaScript reads that JSON and builds DOM nodes
exclusively via createElement/textContent -- never innerHTML -- so an
arbitrary (possibly hostile) repo description can never execute as
markup. The JSON blob itself has "</script" escaped so a description
containing that literal substring can't prematurely close the data
block either.
"""
from __future__ import annotations

import json


def _escape_json_for_script_tag(payload: dict) -> str:
    raw = json.dumps(payload)
    return raw.replace("</script", "<\\/script").replace("<!--", "<\\!--")


def render_html(repos: list, stats: dict) -> str:
    data = {"repos": repos, "stats": stats}
    embedded_json = _escape_json_for_script_tag(data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Star Atlas</title>
<style>
  :root {{
    --bg: #0d1117;
    --bg-card: #161b22;
    --border: #30363d;
    --text: #e6edf3;
    --text-dim: #8b949e;
    --accent: #58a6ff;
    --chip-bg: #21262d;
    --chip-active: #1f6feb;
    --gap: 12px;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    padding: 16px;
  }}
  header {{ margin-bottom: 16px; }}
  h1 {{ margin: 0 0 4px 0; font-size: 1.6rem; }}
  .subtitle {{ color: var(--text-dim); font-size: 0.9rem; }}
  #search {{
    width: 100%;
    padding: 10px 12px;
    margin: 12px 0;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--chip-bg);
    color: var(--text);
    font-size: 1rem;
  }}
  .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }}
  .chip {{
    padding: 6px 12px;
    border-radius: 999px;
    background: var(--chip-bg);
    border: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 0.85rem;
    cursor: pointer;
    user-select: none;
  }}
  .chip.active {{ background: var(--chip-active); color: white; border-color: var(--chip-active); }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--gap);
  }}
  .card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
  }}
  .card h3 {{ margin: 0 0 6px 0; font-size: 1rem; }}
  .card a {{ color: var(--accent); text-decoration: none; }}
  .card a:hover {{ text-decoration: underline; }}
  .card p {{ margin: 6px 0; color: var(--text-dim); font-size: 0.88rem; }}
  .meta {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; font-size: 0.78rem; }}
  .tag {{
    background: var(--chip-active);
    color: white;
    padding: 2px 8px;
    border-radius: 6px;
  }}
  .lang, .stars {{ color: var(--text-dim); }}
  #empty {{ color: var(--text-dim); padding: 24px 0; display: none; }}
  @media (max-width: 640px) {{
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Star Atlas</h1>
  <div class="subtitle" id="summary"></div>
</header>
<input id="search" type="text" placeholder="Search name, description, topics...">
<div class="chips" id="tagChips"></div>
<div class="grid" id="grid"></div>
<div id="empty">No repos match your filters.</div>

<script type="application/json" id="star-atlas-data">{embedded_json}</script>
<script>
(function () {{
  var raw = document.getElementById('star-atlas-data').textContent;
  var data = JSON.parse(raw);
  var repos = data.repos;
  var stats = data.stats;

  document.getElementById('summary').textContent =
    stats.total + ' starred repos • last synced ' + (stats.latest_starred_at || 'never');

  var activeTag = null;
  var chipsEl = document.getElementById('tagChips');
  var allChip = document.createElement('span');
  allChip.className = 'chip active';
  allChip.textContent = 'All (' + stats.total + ')';
  allChip.addEventListener('click', function () {{ setActiveTag(null); }});
  chipsEl.appendChild(allChip);

  Object.keys(stats.by_tag).forEach(function (tag) {{
    var chip = document.createElement('span');
    chip.className = 'chip';
    chip.textContent = tag + ' (' + stats.by_tag[tag] + ')';
    chip.dataset.tag = tag;
    chip.addEventListener('click', function () {{ setActiveTag(tag); }});
    chipsEl.appendChild(chip);
  }});

  function setActiveTag(tag) {{
    activeTag = tag;
    Array.prototype.forEach.call(chipsEl.children, function (chip, i) {{
      chip.classList.toggle('active', (i === 0 && tag === null) || chip.dataset.tag === tag);
    }});
    render();
  }}

  function matches(repo, query) {{
    if (activeTag && repo.tag !== activeTag) return false;
    if (!query) return true;
    var haystack = (repo.full_name + ' ' + (repo.description || '') + ' ' +
      (repo.topics || []).join(' ')).toLowerCase();
    return haystack.indexOf(query.toLowerCase()) !== -1;
  }}

  function makeCard(repo) {{
    var card = document.createElement('div');
    card.className = 'card';

    var h3 = document.createElement('h3');
    var link = document.createElement('a');
    link.href = repo.html_url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = repo.full_name;
    h3.appendChild(link);
    card.appendChild(h3);

    var p = document.createElement('p');
    p.textContent = repo.note || repo.description || 'No description.';
    card.appendChild(p);

    var meta = document.createElement('div');
    meta.className = 'meta';

    var tag = document.createElement('span');
    tag.className = 'tag';
    tag.textContent = repo.tag;
    meta.appendChild(tag);

    if (repo.language) {{
      var lang = document.createElement('span');
      lang.className = 'lang';
      lang.textContent = repo.language;
      meta.appendChild(lang);
    }}

    var stars = document.createElement('span');
    stars.className = 'stars';
    stars.textContent = '★ ' + repo.stargazers_count;
    meta.appendChild(stars);

    card.appendChild(meta);
    return card;
  }}

  function render() {{
    var query = document.getElementById('search').value;
    var grid = document.getElementById('grid');
    grid.textContent = '';
    var visible = repos.filter(function (r) {{ return matches(r, query); }});
    visible.forEach(function (r) {{ grid.appendChild(makeCard(r)); }});
    document.getElementById('empty').style.display = visible.length ? 'none' : 'block';
  }}

  document.getElementById('search').addEventListener('input', render);
  render();
}})();
</script>
</body>
</html>
"""
