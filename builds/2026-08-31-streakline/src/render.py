"""Builds the self-contained HTML dashboard.

All dynamic data is delivered as a single JSON payload inside a
``<script type="application/json">`` tag (with ``</`` escaped so a hostile
value in a manual check-in note can never terminate the tag early), and the
page's own script builds the DOM exclusively via ``createElement`` /
``textContent`` — never ``innerHTML`` — so no value from the database can
ever execute as markup.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from src.coach import CoachNote
from src.db import StreakDB
from src.streaks import completion_rate, daily_streak, weekly_streak


def build_dashboard_data(
    habits: list[dict],
    db: StreakDB,
    as_of: date,
    coach_note: CoachNote,
) -> dict:
    all_rows = db.get_all()
    habit_payload = []
    for habit in habits:
        dates = db.get_dates(habit["id"])
        cadence = habit.get("cadence", "daily")

        if cadence == "weekly":
            info = weekly_streak(dates, as_of)
        else:
            info = daily_streak(dates, as_of)

        rate_30d = completion_rate(dates, as_of - timedelta(days=29), as_of, cadence)

        by_date = {row["date"]: row for row in all_rows if row["habit_id"] == habit["id"]}
        completions = [
            {
                "date": d.isoformat(),
                "source": by_date[d.isoformat()]["source"],
                "detail": by_date[d.isoformat()]["detail"],
            }
            for d in sorted(dates)
        ]

        habit_payload.append(
            {
                "id": habit["id"],
                "name": habit["name"],
                "cadence": cadence,
                "current_streak": info.current,
                "longest_streak": info.longest,
                "completion_rate_30d": round(rate_30d, 4),
                "completions": completions,
            }
        )

    return {
        "generated_at": as_of.isoformat(),
        "as_of": as_of.isoformat(),
        "habits": habit_payload,
        "coach_note": {"text": coach_note.text, "source": coach_note.source},
    }


def _safe_json(data: dict) -> str:
    return json.dumps(data).replace("</", "<\\/")


def render_html(data: dict) -> str:
    payload = _safe_json(data)
    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Streakline</title>
<style>
  :root {{
    --bg: #0f1115;
    --panel: #171a21;
    --panel-border: #262b36;
    --text: #e6e9f0;
    --text-dim: #8b93a7;
    --accent: #5eead4;
    --accent-dim: #1c3f3a;
    --warn: #f59e0b;
    --cell-off: #1e232c;
    --cell-on: #2dd4bf;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    padding: 24px 16px 64px;
  }}
  h1 {{ font-size: 1.4rem; margin: 0 0 4px; }}
  .subtitle {{ color: var(--text-dim); margin: 0 0 24px; font-size: 0.9rem; }}
  .hero {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }}
  .stat {{
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 10px;
    padding: 14px;
  }}
  .stat .value {{ font-size: 1.6rem; font-weight: 600; }}
  .stat .label {{ color: var(--text-dim); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }}
  .coach {{
    background: var(--accent-dim);
    border: 1px solid var(--accent);
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 24px;
    font-size: 0.92rem;
  }}
  .coach .tag {{
    display: inline-block;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--accent);
    margin-bottom: 6px;
  }}
  .controls {{ margin-bottom: 16px; display: flex; gap: 8px; align-items: center; }}
  .controls span {{ color: var(--text-dim); font-size: 0.82rem; margin-right: 4px; }}
  button.range-btn {{
    background: var(--panel);
    border: 1px solid var(--panel-border);
    color: var(--text);
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.82rem;
  }}
  button.range-btn.active {{
    background: var(--accent);
    color: #06201c;
    border-color: var(--accent);
    font-weight: 600;
  }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 16px;
  }}
  .card h2 {{ margin: 0 0 4px; font-size: 1.05rem; }}
  .card .meta {{ color: var(--text-dim); font-size: 0.8rem; margin-bottom: 10px; }}
  .heatmap {{ display: grid; grid-auto-flow: column; grid-template-rows: repeat(7, 12px); gap: 3px; overflow-x: auto; padding-bottom: 4px; }}
  .cell {{ width: 12px; height: 12px; border-radius: 3px; background: var(--cell-off); cursor: pointer; }}
  .cell.on {{ background: var(--cell-on); }}
  .combined-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }}
  .combined-row .row-label {{ width: 120px; font-size: 0.78rem; color: var(--text-dim); flex-shrink: 0; }}
  .combined-cells {{ display: flex; gap: 3px; overflow-x: auto; }}
  .detail {{ margin-top: 12px; font-size: 0.85rem; color: var(--text-dim); min-height: 20px; }}
  footer {{ color: var(--text-dim); font-size: 0.75rem; margin-top: 32px; }}
</style>
</head>
<body>
<h1>Streakline</h1>
<p class="subtitle" id="subtitle"></p>

<div class="hero" id="hero"></div>
<div class="coach" id="coach"></div>

<div class="controls" id="controls">
  <span>Range:</span>
</div>

<div id="habit-cards"></div>

<div class="card">
  <h2>All Habits</h2>
  <div class="meta">Every day a completion was recorded, across all habits.</div>
  <div id="combined"></div>
  <div class="detail" id="detail">Click a day to see what happened.</div>
</div>

<footer>Generated for <span id="as-of"></span>. Data stays local — nothing on this page is sent anywhere.</footer>

<script type="application/json" id="streakline-data">{payload}</script>
<script>
(function () {{
  var data = JSON.parse(document.getElementById('streakline-data').textContent);
  var RANGES = [30, 90, 180, 365];
  var currentRange = 90;
  var asOf = new Date(data.as_of + 'T00:00:00Z');

  function el(tag, attrs, text) {{
    var node = document.createElement(tag);
    if (attrs) {{
      for (var key in attrs) {{
        if (key === 'class') node.className = attrs[key];
        else node.setAttribute(key, attrs[key]);
      }}
    }}
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }}

  function dateRangeEnding(endDate, days) {{
    var out = [];
    for (var i = days - 1; i >= 0; i--) {{
      var d = new Date(endDate);
      d.setUTCDate(d.getUTCDate() - i);
      out.push(d.toISOString().slice(0, 10));
    }}
    return out;
  }}

  function renderSubtitle() {{
    document.getElementById('subtitle').textContent =
      data.habits.length + ' habit' + (data.habits.length === 1 ? '' : 's') + ' tracked as of ' + data.as_of;
    document.getElementById('as-of').textContent = data.as_of;
  }}

  function renderHero() {{
    var hero = document.getElementById('hero');
    hero.innerHTML = '';
    var active = data.habits.filter(function (h) {{ return h.current_streak > 0; }});
    var longestCurrent = data.habits.reduce(function (best, h) {{
      return h.current_streak > (best ? best.current_streak : -1) ? h : best;
    }}, null);
    var bestEver = data.habits.reduce(function (best, h) {{
      return h.longest_streak > (best ? best.longest_streak : -1) ? h : best;
    }}, null);

    var stats = [
      ['Habits Tracked', String(data.habits.length)],
      ['Active Streaks', active.length + ' / ' + data.habits.length],
      ['Longest Streak Now', longestCurrent ? longestCurrent.current_streak + ' (' + longestCurrent.name + ')' : '—'],
      ['Best Ever', bestEver ? bestEver.longest_streak + ' (' + bestEver.name + ')' : '—'],
    ];
    stats.forEach(function (s) {{
      var box = el('div', {{ class: 'stat' }});
      box.appendChild(el('div', {{ class: 'value' }}, s[1]));
      box.appendChild(el('div', {{ class: 'label' }}, s[0]));
      hero.appendChild(box);
    }});
  }}

  function renderCoach() {{
    var coach = document.getElementById('coach');
    coach.innerHTML = '';
    coach.appendChild(el('div', {{ class: 'tag' }}, data.coach_note.source === 'ai' ? 'AI Coach Note' : 'Coach Note'));
    coach.appendChild(el('div', {{}}, data.coach_note.text));
  }}

  function renderControls() {{
    var controls = document.getElementById('controls');
    RANGES.forEach(function (days) {{
      var btn = el('button', {{ class: 'range-btn' + (days === currentRange ? ' active' : ''), 'data-days': String(days) }}, days + 'd');
      btn.addEventListener('click', function () {{
        currentRange = days;
        renderAll();
      }});
      controls.appendChild(btn);
    }});
  }}

  function showDetail(dateStr) {{
    var panel = document.getElementById('detail');
    panel.innerHTML = '';
    panel.appendChild(el('div', {{}}, dateStr + ':'));
    var any = false;
    data.habits.forEach(function (h) {{
      var match = h.completions.filter(function (c) {{ return c.date === dateStr; }})[0];
      if (match) {{
        any = true;
        var line = h.name + ' — ' + match.source + (match.detail ? ': ' + match.detail : '');
        panel.appendChild(el('div', {{}}, line));
      }}
    }});
    if (!any) panel.appendChild(el('div', {{}}, 'Nothing recorded.'));
  }}

  function renderHeatmapInto(container, doneDates, days) {{
    container.innerHTML = '';
    var grid = el('div', {{ class: 'heatmap' }});
    var range = dateRangeEnding(asOf, days);
    var doneSet = {{}};
    doneDates.forEach(function (d) {{ doneSet[d] = true; }});
    range.forEach(function (dateStr) {{
      var cls = 'cell' + (doneSet[dateStr] ? ' on' : '');
      var cell = el('div', {{ class: cls, title: dateStr }});
      cell.addEventListener('click', function () {{ showDetail(dateStr); }});
      grid.appendChild(cell);
    }});
    container.appendChild(grid);
  }}

  function renderHabitCards() {{
    var wrap = document.getElementById('habit-cards');
    wrap.innerHTML = '';
    data.habits.forEach(function (h) {{
      var card = el('div', {{ class: 'card' }});
      card.appendChild(el('h2', {{}}, h.name));
      var meta = h.cadence + ' habit — current streak ' + h.current_streak +
        ', longest ' + h.longest_streak + ', 30-day consistency ' +
        Math.round(h.completion_rate_30d * 100) + '%';
      card.appendChild(el('div', {{ class: 'meta' }}, meta));
      var mapHost = el('div', {{}});
      card.appendChild(mapHost);
      wrap.appendChild(card);
      renderHeatmapInto(mapHost, h.completions.map(function (c) {{ return c.date; }}), currentRange);
    }});
  }}

  function renderCombined() {{
    var host = document.getElementById('combined');
    host.innerHTML = '';
    data.habits.forEach(function (h) {{
      var row = el('div', {{ class: 'combined-row' }});
      row.appendChild(el('div', {{ class: 'row-label' }}, h.name));
      var cellsHost = el('div', {{ class: 'combined-cells' }});
      row.appendChild(cellsHost);
      host.appendChild(row);
      renderHeatmapInto(cellsHost, h.completions.map(function (c) {{ return c.date; }}), currentRange);
    }});
  }}

  function renderAll() {{
    renderSubtitle();
    renderHero();
    renderCoach();
    document.querySelectorAll('.range-btn').forEach(function (btn) {{
      btn.classList.toggle('active', Number(btn.getAttribute('data-days')) === currentRange);
    }});
    renderHabitCards();
    renderCombined();
  }}

  renderControls();
  renderAll();

  window.__streakline = data;
}})();
</script>
</body>
</html>
"""
