"""Renders a self-contained, dark-mode HTML dashboard for the deadline list.

No network calls, no external CDN dependencies, no server required — the
deadline data is inlined as JSON and all DOM insertion of user-entered text
uses textContent (never innerHTML), so a hostile title/notes value cannot
execute as script.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

CATEGORY_ORDER = (
    "Grant",
    "IRB/Ethics",
    "Course",
    "Student Evaluation",
    "Conference",
    "Manuscript",
    "Other",
)


def _bucket(deadline: dict, today: date) -> str:
    if deadline["completed"]:
        return "completed"
    due = date.fromisoformat(deadline["due_date"])
    days_out = (due - today).days
    if days_out < 0:
        return "overdue"
    if days_out <= 7:
        return "due_this_week"
    if days_out <= 30:
        return "due_this_month"
    return "upcoming"


def bucket_deadlines(deadlines: list[dict], today: date | None = None) -> dict[str, list[dict]]:
    today = today or date.today()
    buckets: dict[str, list[dict]] = {
        "overdue": [],
        "due_this_week": [],
        "due_this_month": [],
        "upcoming": [],
        "completed": [],
    }
    for deadline in deadlines:
        buckets[_bucket(deadline, today)].append(deadline)
    return buckets


def _embed_json(payload: dict) -> str:
    raw = json.dumps(payload, default=str)
    # Prevent a "</script>" sequence inside data from closing the tag early.
    return raw.replace("</", "<\\/")


_BUCKET_LABELS = {
    "overdue": "Overdue",
    "due_this_week": "Due This Week",
    "due_this_month": "Due This Month",
    "upcoming": "Upcoming",
    "completed": "Completed",
}


def render_dashboard(deadlines: list[dict], today: date | None = None) -> str:
    today = today or date.today()
    buckets = bucket_deadlines(deadlines, today)
    counts = {k: len(v) for k, v in buckets.items()}
    payload = {
        "generated_at": datetime.now().isoformat(),
        "today": today.isoformat(),
        "buckets": _BUCKET_LABELS,
        "bucket_order": ["overdue", "due_this_week", "due_this_month", "upcoming", "completed"],
        "categories": list(CATEGORY_ORDER),
        "deadlines": [
            {**d, "bucket": _bucket(d, today)} for d in deadlines
        ],
    }
    data_json = _embed_json(payload)
    total = len(deadlines)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Deadline Guardian</title>
<style>
  :root {{
    --bg: #0f1420;
    --panel: #171d2b;
    --panel-border: #262e42;
    --text: #e6e9f0;
    --muted: #8a92a6;
    --accent: #5b8def;
    --overdue: #e35d6a;
    --week: #e3a13d;
    --month: #d8c34c;
    --upcoming: #4caf82;
    --completed: #6b7280;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 24px;
  }}
  h1 {{ font-size: 1.5rem; margin: 0 0 4px 0; }}
  .subtitle {{ color: var(--muted); margin-bottom: 20px; font-size: 0.9rem; }}
  .summary {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 20px;
  }}
  .stat {{
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 10px;
    padding: 10px 16px;
    min-width: 110px;
  }}
  .stat .n {{ font-size: 1.4rem; font-weight: 700; }}
  .stat .label {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.03em; }}
  .stat.overdue .n {{ color: var(--overdue); }}
  .stat.due_this_week .n {{ color: var(--week); }}
  .stat.due_this_month .n {{ color: var(--month); }}
  .stat.upcoming .n {{ color: var(--upcoming); }}
  .stat.completed .n {{ color: var(--completed); }}
  .filters {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }}
  .chip {{
    background: var(--panel);
    border: 1px solid var(--panel-border);
    color: var(--text);
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 0.85rem;
    cursor: pointer;
  }}
  .chip.active {{ background: var(--accent); border-color: var(--accent); color: #08101f; }}
  section.bucket {{ margin-bottom: 26px; }}
  section.bucket h2 {{
    font-size: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
  .dot.overdue {{ background: var(--overdue); }}
  .dot.due_this_week {{ background: var(--week); }}
  .dot.due_this_month {{ background: var(--month); }}
  .dot.upcoming {{ background: var(--upcoming); }}
  .dot.completed {{ background: var(--completed); }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 10px;
    overflow: hidden;
  }}
  th, td {{
    text-align: left;
    padding: 10px 12px;
    border-bottom: 1px solid var(--panel-border);
    font-size: 0.9rem;
  }}
  th {{ color: var(--muted); font-weight: 600; cursor: pointer; user-select: none; }}
  tr:last-child td {{ border-bottom: none; }}
  .cat-badge {{
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 999px;
    background: #232b3f;
    color: var(--muted);
  }}
  .empty-state {{
    color: var(--muted);
    padding: 30px;
    text-align: center;
    background: var(--panel);
    border: 1px dashed var(--panel-border);
    border-radius: 10px;
  }}
  @media (max-width: 640px) {{
    body {{ padding: 14px; }}
    th:nth-child(4), td:nth-child(4) {{ display: none; }}
  }}
</style>
</head>
<body>
<h1>Deadline Guardian</h1>
<div class="subtitle">Generated {today.isoformat()} &middot; {total} deadline{"s" if total != 1 else ""} tracked</div>

<div class="summary" id="summary"></div>
<div class="filters" id="filters"></div>
<div id="buckets"></div>

<script id="deadline-data" type="application/json">{data_json}</script>
<script>
(function () {{
  const data = JSON.parse(document.getElementById('deadline-data').textContent);
  let activeCategory = 'All';

  function el(tag, props, children) {{
    const node = document.createElement(tag);
    Object.assign(node, props || {{}});
    (children || []).forEach(c => node.appendChild(c));
    return node;
  }}

  function renderSummary() {{
    const summary = document.getElementById('summary');
    summary.textContent = '';
    data.bucket_order.forEach(function (key) {{
      const count = data.deadlines.filter(d => d.bucket === key).length;
      const stat = el('div', {{ className: 'stat ' + key }}, [
        el('div', {{ className: 'n', textContent: String(count) }}),
        el('div', {{ className: 'label', textContent: data.buckets[key] }}),
      ]);
      summary.appendChild(stat);
    }});
  }}

  function renderFilters() {{
    const filters = document.getElementById('filters');
    filters.textContent = '';
    const cats = ['All'].concat(data.categories);
    cats.forEach(function (cat) {{
      const chip = el('button', {{
        className: 'chip' + (cat === activeCategory ? ' active' : ''),
        textContent: cat,
      }});
      chip.addEventListener('click', function () {{
        activeCategory = cat;
        renderFilters();
        renderBuckets();
      }});
      filters.appendChild(chip);
    }});
  }}

  function matches(d) {{
    return activeCategory === 'All' || d.category === activeCategory;
  }}

  function renderBuckets() {{
    const container = document.getElementById('buckets');
    container.textContent = '';
    const visible = data.deadlines.filter(matches);

    if (visible.length === 0) {{
      container.appendChild(el('div', {{
        className: 'empty-state',
        textContent: data.deadlines.length === 0
          ? 'No deadlines yet. Use "add" or "capture" to create one.'
          : 'No deadlines match this filter.',
      }}));
      return;
    }}

    data.bucket_order.forEach(function (key) {{
      const items = visible.filter(d => d.bucket === key)
        .slice()
        .sort((a, b) => a.due_date.localeCompare(b.due_date));
      if (items.length === 0) return;

      const section = el('section', {{ className: 'bucket' }});
      section.appendChild(el('h2', {{}}, [
        el('span', {{ className: 'dot ' + key }}),
        document.createTextNode(data.buckets[key] + ' (' + items.length + ')'),
      ]));

      const table = el('table');
      const thead = el('thead', {{}}, [
        el('tr', {{}}, ['Title', 'Category', 'Due Date', 'Notes'].map(h => el('th', {{ textContent: h }}))),
      ]);
      const tbody = el('tbody');
      items.forEach(function (d) {{
        tbody.appendChild(el('tr', {{}}, [
          el('td', {{ textContent: d.title }}),
          el('td', {{}}, [el('span', {{ className: 'cat-badge', textContent: d.category }})]),
          el('td', {{ textContent: d.due_date }}),
          el('td', {{ textContent: d.notes || '—' }}),
        ]));
      }});
      table.appendChild(thead);
      table.appendChild(tbody);
      section.appendChild(table);
      container.appendChild(section);
    }});
  }}

  renderSummary();
  renderFilters();
  renderBuckets();
}})();
</script>
</body>
</html>
"""
