"""Renders the DigestOutline + DigestDraft as Markdown and self-contained HTML."""

from __future__ import annotations

import html
import json
import re

from ai_writer import DigestDraft
from outline_builder import DigestOutline

CHART_JS_URL = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js"

_SLUG_ALLOWED = re.compile(r"[^a-z0-9]+")


def slugify(text: str, max_length: int = 60) -> str:
    """Turn arbitrary text into a filesystem-safe slug.

    Only `[a-z0-9-]` characters ever appear in the result — this is the
    only function permitted to turn user-supplied text into a path
    component, specifically to prevent path traversal (`../`, absolute
    paths, null bytes, etc. are all stripped, not just "cleaned up").
    """
    lowered = text.strip().lower()
    slug = _SLUG_ALLOWED.sub("-", lowered).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug:
        slug = "topic"
    return slug[:max_length].strip("-") or "topic"


def safe_json_for_script(obj) -> str:
    """JSON-encode `obj` for embedding inside a <script type="application/json">
    block. Neutralizes `</` so a value containing "</script>" cannot break
    out of the tag, without relying on the surrounding markup for safety."""
    return json.dumps(obj).replace("</", "<\\/")


def render_markdown(outline: DigestOutline, draft: DigestDraft) -> str:
    lines = [
        f"# {outline.topic}: a research pulse check",
        "",
        f"*Generated {outline.generated_at} · {outline.total_papers} papers · "
        f"{outline.window_months}-month window · draft source: {draft.source}*",
        "",
        draft.intro,
        "",
        "## Trend",
        "",
        draft.trend_section,
        "",
        "## Notable figures",
        "",
        draft.facts_section,
        "",
        "## Takeaway",
        "",
        draft.takeaway,
        "",
        "## Sources",
        "",
    ]
    for paper in outline.top_papers:
        authors = ", ".join(paper.authors) if paper.authors else "Unknown authors"
        lines.append(f"- [{paper.title}]({paper.pdf_url}) — {authors} ({paper.published.isoformat()})")
    lines.append("")
    return "\n".join(lines)


def render_html(outline: DigestOutline, draft: DigestDraft) -> str:
    topic = html.escape(outline.topic)
    intro = html.escape(draft.intro)
    trend_section = html.escape(draft.trend_section)
    facts_section = html.escape(draft.facts_section).replace("\n", "<br>")
    takeaway = html.escape(draft.takeaway)
    source_label = "Claude Haiku" if draft.source == "ai" else "deterministic template (no AI key)"

    keyword_chips = "".join(
        f'<span class="chip">{html.escape(kw)}</span>' for kw in outline.rising_keywords
    ) or '<span class="muted">none detected</span>'

    paper_rows = "".join(
        f"<tr><td>{html.escape(p.title)}</td>"
        f"<td>{html.escape(', '.join(p.authors) or 'Unknown')}</td>"
        f"<td>{p.published.isoformat()}</td>"
        f'<td><a href="{html.escape(p.pdf_url)}" rel="noopener">PDF</a></td></tr>'
        for p in outline.top_papers
    ) or '<tr><td colspan="4" class="muted">No papers matched.</td></tr>'

    chart_labels = [b.period_label for b in outline.trend.buckets]
    chart_counts = [b.count for b in outline.trend.buckets]
    chart_data_json = safe_json_for_script({"labels": chart_labels, "counts": chart_counts})

    table_fallback_rows = "".join(
        f"<tr><td>{html.escape(label)}</td><td>{count}</td></tr>"
        for label, count in zip(chart_labels, chart_counts)
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Preprint Pulse — {topic}</title>
<style>
  :root {{
    --bg: #0f1115; --panel: #171a21; --text: #e8eaed; --muted: #9aa0a8;
    --accent: #7dc4ff; --border: #2a2e37;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    background: var(--bg); color: var(--text); margin: 0; padding: 24px 16px 48px;
    font: 15px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }}
  main {{ max-width: 760px; margin: 0 auto; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 4px; }}
  .meta {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }}
  section {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 18px 20px; margin-bottom: 18px;
  }}
  section h2 {{ margin-top: 0; font-size: 1.05rem; color: var(--accent); }}
  .chip {{
    display: inline-block; background: #1f2733; border: 1px solid var(--border);
    border-radius: 999px; padding: 3px 10px; margin: 2px 4px 2px 0; font-size: 0.85rem;
  }}
  .muted {{ color: var(--muted); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th, td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 600; }}
  a {{ color: var(--accent); }}
  canvas {{ max-width: 100%; }}
  .overflow {{ overflow-x: auto; }}
</style>
</head>
<body>
<main>
  <h1>{topic}: a research pulse check</h1>
  <div class="meta">
    Generated {html.escape(outline.generated_at)} · {outline.total_papers} papers ·
    {outline.window_months}-month window · draft source: {html.escape(source_label)}
  </div>

  <section>
    <h2>Overview</h2>
    <p>{intro}</p>
  </section>

  <section>
    <h2>Trend</h2>
    <p>{trend_section}</p>
    <p>Rising keywords: {keyword_chips}</p>
    <div id="chart-wrap">
      <canvas id="trend-chart" height="220" role="img" aria-label="Papers per month"></canvas>
    </div>
    <div id="chart-fallback" class="overflow" hidden>
      <table>
        <thead><tr><th>Month</th><th>Papers</th></tr></thead>
        <tbody>{table_fallback_rows}</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>Notable figures</h2>
    <p>{facts_section}</p>
  </section>

  <section>
    <h2>Takeaway</h2>
    <p>{takeaway}</p>
  </section>

  <section>
    <h2>Sources</h2>
    <div class="overflow">
      <table>
        <thead><tr><th>Title</th><th>Authors</th><th>Published</th><th></th></tr></thead>
        <tbody>{paper_rows}</tbody>
      </table>
    </div>
  </section>
</main>

<script type="application/json" id="chart-data">{chart_data_json}</script>
<script src="{CHART_JS_URL}"></script>
<script>
  (function () {{
    try {{
      var raw = document.getElementById('chart-data').textContent;
      var data = JSON.parse(raw);
      var canvas = document.getElementById('trend-chart');
      if (typeof Chart === 'undefined' || !canvas) {{ throw new Error('chart unavailable'); }}
      new Chart(canvas.getContext('2d'), {{
        type: 'bar',
        data: {{
          labels: data.labels,
          datasets: [{{
            label: 'Papers per month',
            data: data.counts,
            backgroundColor: '#7dc4ff'
          }}]
        }},
        options: {{
          scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }},
          plugins: {{ legend: {{ display: false }} }}
        }}
      }});
    }} catch (err) {{
      var fallback = document.getElementById('chart-fallback');
      var wrap = document.getElementById('chart-wrap');
      if (fallback) fallback.hidden = false;
      if (wrap) wrap.hidden = true;
    }}
  }})();
</script>
</body>
</html>
"""
