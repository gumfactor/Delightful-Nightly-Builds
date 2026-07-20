"""Self-contained dark-mode HTML index renderer for CanFile knowledge cards.

All dynamic text (company names, assessment text, Wikipedia summaries,
Wikidata fact labels) is passed through `html.escape` before being placed
into the page. Nothing is ever assigned via a raw/unescaped HTML sink.
"""
from __future__ import annotations

import html
import json
from typing import Any

VERDICT_LABELS = {
    "canadian": "Canadian-owned",
    "foreign": "Foreign-owned",
    "uncertain": "Uncertain",
    "insufficient-data": "Insufficient data",
}


def _esc(value: Any) -> str:
    return html.escape(str(value) if value is not None else "", quote=True)


def _render_facts(facts: dict[str, Any]) -> str:
    labels = {
        "country_labels": "Country",
        "headquarters_labels": "Headquarters",
        "parent_organization_labels": "Parent organization",
        "owned_by_labels": "Owned by",
        "parent_country_labels": "Parent/owner country",
    }
    items = []
    for key, title in labels.items():
        values = facts.get(key) or []
        if values:
            items.append(f"<li><strong>{_esc(title)}:</strong> {_esc(', '.join(values))}</li>")
    if not items:
        return "<p class=\"muted\">No structured Wikidata facts on record.</p>"
    return f"<ul class=\"facts\">{''.join(items)}</ul>"


def _render_history(history: list[dict[str, Any]]) -> str:
    if len(history) <= 1:
        return ""
    rows = []
    for card in reversed(history):
        rows.append(
            "<li>"
            f"<span class=\"version-badge\">v{_esc(card['version'])}</span> "
            f"{_esc(card['created_at'])} — {_esc(VERDICT_LABELS.get(card['verdict'], card['verdict']))} "
            f"({_esc(card['confidence'])})"
            "</li>"
        )
    return (
        "<details class=\"history\"><summary>Version history "
        f"({_esc(len(history))} versions)</summary><ul>{''.join(rows)}</ul></details>"
    )


def _render_sources(source_urls: list[str]) -> str:
    if not source_urls:
        return ""
    links = " · ".join(
        f'<a href="{_esc(url)}" target="_blank" rel="noopener noreferrer">source</a>'
        for url in source_urls
    )
    return f"<p class=\"sources\">{links}</p>"


def _render_card(card: dict[str, Any], history: list[dict[str, Any]]) -> str:
    verdict = card["verdict"]
    verdict_label = VERDICT_LABELS.get(verdict, verdict)
    summary = card.get("wikipedia_summary") or ""
    return f"""
    <article class="card" data-verdict="{_esc(verdict)}" data-name="{_esc(card['company_name'].lower())}">
      <header>
        <h2>{_esc(card['company_name'])}</h2>
        <span class="badge badge-{_esc(verdict)}">{_esc(verdict_label)}</span>
        <span class="confidence confidence-{_esc(card['confidence'])}">{_esc(card['confidence'])} confidence</span>
      </header>
      <p class="assessment">{_esc(card['assessment_text'])}</p>
      {_render_facts(card['wikidata_facts'])}
      {f'<p class="wiki-summary">{_esc(summary)}</p>' if summary else ''}
      {_render_sources(card['source_urls'])}
      {_render_history(history)}
      <footer class="meta">Card v{_esc(card['version'])} · updated {_esc(card['created_at'])}</footer>
    </article>
    """


def render_html(entries: list[dict[str, Any]]) -> str:
    """Render the full report. `entries` is a list of
    {"card": latest_card_dict, "history": [all versions for that company]}.
    """
    cards_html = "".join(_render_card(entry["card"], entry["history"]) for entry in entries)
    card_count = len(entries)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CanFile — Canadian Ownership Knowledge Cards</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{
    --bg: #0f1115; --panel: #171a21; --border: #2a2f3a; --text: #e8eaed;
    --muted: #9aa2af; --accent: #4f8cff;
    --canadian: #2ecc71; --foreign: #e67e22; --uncertain: #f1c40f; --insufficient: #7f8c8d;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 2rem; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  h1 {{ margin: 0 0 0.25rem; font-size: 1.6rem; }}
  .subtitle {{ color: var(--muted); margin: 0 0 1.5rem; }}
  .controls {{ display: flex; gap: 0.75rem; margin-bottom: 1.5rem; flex-wrap: wrap; }}
  .controls input, .controls select {{
    background: var(--panel); color: var(--text); border: 1px solid var(--border);
    border-radius: 6px; padding: 0.5rem 0.75rem; font-size: 0.95rem;
  }}
  .controls input {{ flex: 1; min-width: 200px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; }}
  .card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 1.1rem; display: flex; flex-direction: column; gap: 0.5rem;
  }}
  .card header {{ display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }}
  .card h2 {{ font-size: 1.1rem; margin: 0; flex: 1; }}
  .badge {{ font-size: 0.75rem; padding: 0.2rem 0.55rem; border-radius: 999px; font-weight: 600; }}
  .badge-canadian {{ background: rgba(46,204,113,0.15); color: var(--canadian); }}
  .badge-foreign {{ background: rgba(230,126,34,0.15); color: var(--foreign); }}
  .badge-uncertain {{ background: rgba(241,196,15,0.15); color: var(--uncertain); }}
  .badge-insufficient-data {{ background: rgba(127,140,141,0.15); color: var(--insufficient); }}
  .confidence {{ font-size: 0.75rem; color: var(--muted); }}
  .assessment {{ font-size: 0.92rem; line-height: 1.4; }}
  .facts {{ list-style: none; padding: 0; margin: 0; font-size: 0.85rem; color: var(--muted); }}
  .facts li {{ margin-bottom: 0.2rem; }}
  .facts strong {{ color: var(--text); }}
  .wiki-summary {{ font-size: 0.85rem; color: var(--muted); font-style: italic; }}
  .sources a {{ color: var(--accent); font-size: 0.8rem; text-decoration: none; }}
  .sources a:hover {{ text-decoration: underline; }}
  .history summary {{ cursor: pointer; font-size: 0.8rem; color: var(--muted); }}
  .history ul {{ list-style: none; padding-left: 0.5rem; font-size: 0.78rem; color: var(--muted); }}
  .version-badge {{ background: var(--border); border-radius: 4px; padding: 0 0.35rem; }}
  .meta {{ font-size: 0.72rem; color: var(--muted); border-top: 1px solid var(--border); padding-top: 0.4rem; }}
  .empty-state {{ color: var(--muted); text-align: center; padding: 3rem 1rem; }}
</style>
</head>
<body>
  <h1>CanFile</h1>
  <p class="subtitle">Canadian Ownership Knowledge Cards — {_esc(card_count)} companies tracked</p>
  <div class="controls">
    <input type="text" id="search-box" placeholder="Search company or assessment..." data-testid="search-box">
    <select id="verdict-filter" data-testid="verdict-filter">
      <option value="">All verdicts</option>
      <option value="canadian">Canadian-owned</option>
      <option value="foreign">Foreign-owned</option>
      <option value="uncertain">Uncertain</option>
      <option value="insufficient-data">Insufficient data</option>
    </select>
  </div>
  <div class="grid" id="card-grid" data-testid="card-grid">
    {cards_html if cards_html else '<p class="empty-state">No knowledge cards yet. Run <code>add "Company Name"</code>.</p>'}
  </div>
  <p class="empty-state" id="no-results" style="display:none;">No cards match your search.</p>
<script>
(function() {{
  const searchBox = document.getElementById('search-box');
  const verdictFilter = document.getElementById('verdict-filter');
  const cards = Array.from(document.querySelectorAll('.card'));
  const noResults = document.getElementById('no-results');

  function applyFilters() {{
    const term = searchBox.value.trim().toLowerCase();
    const verdict = verdictFilter.value;
    let visibleCount = 0;
    cards.forEach(function(card) {{
      const matchesTerm = !term || card.dataset.name.includes(term) ||
        card.querySelector('.assessment').textContent.toLowerCase().includes(term);
      const matchesVerdict = !verdict || card.dataset.verdict === verdict;
      const visible = matchesTerm && matchesVerdict;
      card.style.display = visible ? '' : 'none';
      if (visible) visibleCount += 1;
    }});
    noResults.style.display = visibleCount === 0 ? 'block' : 'none';
  }}

  searchBox.addEventListener('input', applyFilters);
  verdictFilter.addEventListener('change', applyFilters);
}})();
</script>
</body>
</html>
"""
