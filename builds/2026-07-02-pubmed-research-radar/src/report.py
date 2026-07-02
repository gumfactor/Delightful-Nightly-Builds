"""Render the dark-mode HTML 'radar' report from the current database state."""

from __future__ import annotations

import html
import sqlite3

from src.db import get_articles_by_topic, list_topics

_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PubMed Research Radar</title>
<style>
  :root {{
    --bg: #0f1117;
    --panel: #171a24;
    --border: #2a2e3a;
    --text: #e6e8ef;
    --muted: #9099ab;
    --accent: #7aa2f7;
    --high: #4caf7d;
    --mid: #d9a441;
    --low: #6b7280;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }}
  header {{
    padding: 1.25rem 1rem;
    border-bottom: 1px solid var(--border);
  }}
  header h1 {{ margin: 0 0 0.25rem; font-size: 1.4rem; }}
  header p {{ margin: 0; color: var(--muted); font-size: 0.9rem; }}
  #search {{
    width: 100%;
    max-width: 420px;
    margin-top: 0.75rem;
    padding: 0.5rem 0.75rem;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-size: 0.95rem;
  }}
  nav.tabs {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 1rem;
    border-bottom: 1px solid var(--border);
  }}
  .tab-btn {{
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 0.4rem 0.9rem;
    border-radius: 999px;
    cursor: pointer;
    font-size: 0.85rem;
  }}
  .tab-btn.active {{ color: var(--text); border-color: var(--accent); }}
  main {{ padding: 1rem; max-width: 900px; margin: 0 auto; }}
  .topic-panel {{ display: none; flex-direction: column; gap: 0.75rem; }}
  .topic-panel.active {{ display: flex; }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.9rem 1rem;
  }}
  .card.hidden-by-search {{ display: none; }}
  .card-top {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 0.75rem;
  }}
  .card h3 {{ margin: 0 0 0.35rem; font-size: 1rem; }}
  .card h3 a {{ color: var(--text); text-decoration: none; }}
  .card h3 a:hover {{ color: var(--accent); }}
  .meta {{ color: var(--muted); font-size: 0.8rem; margin-bottom: 0.5rem; }}
  .summary {{ font-size: 0.9rem; }}
  .badge {{
    flex-shrink: 0;
    font-weight: 600;
    font-size: 0.85rem;
    border-radius: 6px;
    padding: 0.15rem 0.5rem;
  }}
  .badge.high {{ background: color-mix(in srgb, var(--high) 25%, transparent); color: var(--high); }}
  .badge.mid {{ background: color-mix(in srgb, var(--mid) 25%, transparent); color: var(--mid); }}
  .badge.low {{ background: color-mix(in srgb, var(--low) 35%, transparent); color: var(--low); }}
  .tag {{
    display: inline-block;
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: var(--accent);
    border: 1px solid var(--accent);
    border-radius: 6px;
    padding: 0.05rem 0.4rem;
  }}
  .actions {{ margin-top: 0.6rem; display: flex; gap: 0.5rem; }}
  .actions button {{
    background: none;
    border: 1px solid var(--border);
    color: var(--muted);
    border-radius: 6px;
    padding: 0.2rem 0.6rem;
    font-size: 0.8rem;
    cursor: pointer;
  }}
  .actions button.on {{ color: var(--accent); border-color: var(--accent); }}
  .empty {{ color: var(--muted); font-style: italic; padding: 1rem 0; }}
</style>
</head>
<body>
<header>
  <h1>PubMed Research Radar</h1>
  <p>{article_count} articles across {topic_count} topics</p>
  <input id="search" type="text" placeholder="Search titles and summaries...">
</header>
<nav class="tabs">
{tab_buttons}
</nav>
<main>
{topic_panels}
</main>
<script>
document.querySelectorAll('.tab-btn').forEach(function (btn) {{
  btn.addEventListener('click', function () {{
    document.querySelectorAll('.tab-btn').forEach(function (b) {{ b.classList.remove('active'); }});
    document.querySelectorAll('.topic-panel').forEach(function (p) {{ p.classList.remove('active'); }});
    btn.classList.add('active');
    document.getElementById('panel-' + btn.dataset.topicId).classList.add('active');
  }});
}});

document.getElementById('search').addEventListener('input', function (evt) {{
  var q = evt.target.value.trim().toLowerCase();
  document.querySelectorAll('.card').forEach(function (card) {{
    var haystack = card.dataset.searchText || '';
    card.classList.toggle('hidden-by-search', q.length > 0 && haystack.indexOf(q) === -1);
  }});
}});

function applyStoredState(card) {{
  var pmid = card.dataset.pmid;
  var starBtn = card.querySelector('.star-btn');
  var readBtn = card.querySelector('.read-btn');
  if (localStorage.getItem('radar-star-' + pmid) === '1') {{ starBtn.classList.add('on'); }}
  if (localStorage.getItem('radar-read-' + pmid) === '1') {{ readBtn.classList.add('on'); }}
  starBtn.addEventListener('click', function () {{
    var on = starBtn.classList.toggle('on');
    localStorage.setItem('radar-star-' + pmid, on ? '1' : '0');
  }});
  readBtn.addEventListener('click', function () {{
    var on = readBtn.classList.toggle('on');
    localStorage.setItem('radar-read-' + pmid, on ? '1' : '0');
  }});
}}
document.querySelectorAll('.card').forEach(applyStoredState);
</script>
</body>
</html>
"""


def _relevance_class(score: float | None) -> str:
    if score is None:
        return "low"
    if score >= 7:
        return "high"
    if score >= 4:
        return "mid"
    return "low"


def _render_card(article: sqlite3.Row) -> str:
    title = html.escape(article["title"] or "(untitled)")
    url = html.escape(article["url"] or "#")
    authors = html.escape(article["authors"] or "Unknown")
    journal = html.escape(article["journal"] or "Unknown journal")
    pub_date = html.escape(article["pub_date"] or "Unknown date")
    body_text = article["ai_summary"] or article["abstract"] or "(no abstract available)"
    body = html.escape(body_text)
    score = article["relevance_score"]
    score_label = f"{score:.1f}" if score is not None else "?"
    tag = article["methodology_tag"]
    tag_html = f'<span class="tag">{html.escape(tag)}</span>' if tag else ""
    search_text = html.escape(f"{title} {body}".lower())

    return f"""
    <article class="card" data-pmid="{html.escape(article['pmid'])}" data-search-text="{search_text}">
      <div class="card-top">
        <h3><a href="{url}" target="_blank" rel="noopener">{title}</a></h3>
        <span class="badge {_relevance_class(score)}">{score_label}</span>
      </div>
      <div class="meta">{authors} &middot; {journal} &middot; {pub_date}</div>
      <div class="summary">{body}</div>
      {tag_html}
      <div class="actions">
        <button class="star-btn">&#9733; Star</button>
        <button class="read-btn">&#10003; Read</button>
      </div>
    </article>
    """


def render_report(conn: sqlite3.Connection) -> str:
    topics = list_topics(conn)
    tab_buttons = []
    topic_panels = []
    total_articles = 0

    for index, topic in enumerate(topics):
        articles = get_articles_by_topic(conn, topic["id"])
        total_articles += len(articles)
        active_class = " active" if index == 0 else ""
        tab_buttons.append(
            f'<button class="tab-btn{active_class}" data-topic-id="{topic["id"]}">'
            f'{html.escape(topic["name"])} ({len(articles)})</button>'
        )
        if articles:
            cards = "".join(_render_card(article) for article in articles)
        else:
            cards = '<p class="empty">No articles yet for this topic. Run `fetch` to pull new results.</p>'
        topic_panels.append(
            f'<section class="topic-panel{active_class}" id="panel-{topic["id"]}">{cards}</section>'
        )

    if not topics:
        tab_buttons.append('<span class="empty">No topics configured yet.</span>')
        topic_panels.append('<p class="empty">Add a topic with `topics add` and run `fetch`.</p>')

    return _PAGE_TEMPLATE.format(
        article_count=total_articles,
        topic_count=len(topics),
        tab_buttons="\n".join(tab_buttons),
        topic_panels="\n".join(topic_panels),
    )


def write_report(conn: sqlite3.Connection, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(render_report(conn))
