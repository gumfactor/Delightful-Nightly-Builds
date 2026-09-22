"""Self-contained dark-mode HTML journal renderer.

Security contract: every string that could contain user- or forecast-derived
text (location name, narrative) is delivered as JSON inside a
`<script type="application/json">` block with `</` sequences neutralized so
a hostile payload can never prematurely close the tag, and the page's own
JavaScript builds the DOM exclusively via `createElement`/`textContent` --
never `innerHTML` -- so no fetched or stored string can execute as markup.
"""

from __future__ import annotations

import json
from typing import List

from .openmeteo import WindowAggregate
from .store import Entry

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


def _entry_to_dict(entry: Entry) -> dict:
    return {
        "id": entry.id,
        "created_at": entry.created_at,
        "location_name": entry.location_name,
        "target_date": entry.target_date,
        "window_label": entry.window_label,
        "score": entry.score,
        "beaufort_name": entry.beaufort_name,
        "wind_knots": entry.wind_knots,
        "gust_knots": entry.gust_knots,
        "temp_c": entry.temp_c,
        "precip_probability": entry.precip_probability,
        "cloud_cover": entry.cloud_cover,
        "narrative": entry.narrative,
        "ai_polished": entry.ai_polished,
    }


def _window_to_dict(window: WindowAggregate) -> dict:
    return {
        "date": window.date,
        "window": window.window,
        "score": window.score,
        "beaufort_name": window.beaufort_name,
        "wind_knots": window.wind_knots,
        "gust_knots": window.gust_knots,
        "temp_c": window.temp_c,
        "precip_probability": window.precip_probability,
        "cloud_cover": window.cloud_cover,
    }


def _safe_json(data: dict) -> str:
    """JSON-encode and neutralize any '</' sequence so the payload can never
    break out of its containing <script> tag."""
    return json.dumps(data).replace("</", "<\\/")


def render_html(
    entries: List[Entry],
    upcoming_windows: List[WindowAggregate],
    location_name: str,
) -> str:
    data = {
        "location_name": location_name,
        "entries": [_entry_to_dict(e) for e in entries],
        "upcoming": [_window_to_dict(w) for w in upcoming_windows],
    }
    payload = _safe_json(data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wake Log</title>
<style>
  :root {{
    --bg: #0f1620;
    --surface: #161f2c;
    --surface-alt: #1e2937;
    --border: #2a3644;
    --text: #e6edf3;
    --text-dim: #9aa8b6;
    --accent: #4fb0e0;
    --good: #4caf7d;
    --warn: #d9a441;
    --bad: #d9534f;
    --space: 1rem;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 0;
    padding: var(--space);
    line-height: 1.5;
  }}
  h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
  .subtitle {{ color: var(--text-dim); margin-bottom: 1.5rem; }}
  section {{ margin-bottom: 2rem; }}
  h2 {{ font-size: 1.1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }}
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
  }}
  .card-header {{ display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; }}
  .score {{ font-weight: 700; font-size: 1.1rem; }}
  .score.good {{ color: var(--good); }}
  .score.warn {{ color: var(--warn); }}
  .score.bad {{ color: var(--bad); }}
  .meta {{ color: var(--text-dim); font-size: 0.85rem; margin-top: 0.35rem; }}
  .narrative {{ margin-top: 0.5rem; }}
  input[type="search"] {{
    width: 100%;
    max-width: 400px;
    padding: 0.5rem;
    background: var(--surface-alt);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    margin-bottom: 1rem;
  }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
  .empty {{ color: var(--text-dim); font-style: italic; }}
  canvas {{ max-width: 100%; }}
  @media (max-width: 480px) {{
    .card-header {{ flex-direction: column; }}
  }}
</style>
</head>
<body>
  <h1>Wake Log</h1>
  <div class="subtitle" id="location-subtitle"></div>

  <section>
    <h2>Upcoming Windows</h2>
    <canvas id="upcoming-chart" height="120" aria-label="Upcoming boating comfort scores" role="img"></canvas>
    <div id="upcoming-fallback"></div>
  </section>

  <section>
    <h2>Journal</h2>
    <input type="search" id="search-box" placeholder="Search entries by text or location...">
    <div id="entries-container"></div>
  </section>

<script type="application/json" id="wake-log-data">{payload}</script>
<script src="{CHART_JS_CDN}"></script>
<script>
(function() {{
  var data = JSON.parse(document.getElementById('wake-log-data').textContent);

  var subtitle = document.getElementById('location-subtitle');
  subtitle.textContent = data.location_name + ' — ' + data.entries.length + ' logged trip' +
    (data.entries.length === 1 ? '' : 's');

  function scoreClass(score) {{
    if (score >= 70) return 'good';
    if (score >= 40) return 'warn';
    return 'bad';
  }}

  function renderUpcoming() {{
    var labels = data.upcoming.map(function(w) {{ return w.date + ' ' + w.window; }});
    var scores = data.upcoming.map(function(w) {{ return w.score; }});

    if (typeof Chart !== 'undefined' && data.upcoming.length > 0) {{
      var canvas = document.getElementById('upcoming-chart');
      new Chart(canvas, {{
        type: 'bar',
        data: {{
          labels: labels,
          datasets: [{{
            label: 'Comfort score',
            data: scores,
            backgroundColor: scores.map(function(s) {{
              if (s >= 70) return '#4caf7d';
              if (s >= 40) return '#d9a441';
              return '#d9534f';
            }})
          }}]
        }},
        options: {{
          scales: {{ y: {{ beginAtZero: true, max: 100 }} }},
          plugins: {{ legend: {{ display: false }} }}
        }}
      }});
    }} else {{
      var container = document.getElementById('upcoming-fallback');
      document.getElementById('upcoming-chart').style.display = 'none';
      if (data.upcoming.length === 0) {{
        var empty = document.createElement('p');
        empty.className = 'empty';
        empty.textContent = 'No upcoming forecast loaded.';
        container.appendChild(empty);
        return;
      }}
      var table = document.createElement('table');
      var thead = document.createElement('thead');
      var headRow = document.createElement('tr');
      ['Date', 'Window', 'Score', 'Beaufort'].forEach(function(h) {{
        var th = document.createElement('th');
        th.textContent = h;
        headRow.appendChild(th);
      }});
      thead.appendChild(headRow);
      table.appendChild(thead);
      var tbody = document.createElement('tbody');
      data.upcoming.forEach(function(w) {{
        var row = document.createElement('tr');
        [w.date, w.window, String(w.score), w.beaufort_name].forEach(function(val) {{
          var td = document.createElement('td');
          td.textContent = val;
          row.appendChild(td);
        }});
        tbody.appendChild(row);
      }});
      table.appendChild(tbody);
      container.appendChild(table);
    }}
  }}

  function buildEntryCard(entry) {{
    var card = document.createElement('div');
    card.className = 'card';

    var header = document.createElement('div');
    header.className = 'card-header';

    var title = document.createElement('strong');
    title.textContent = entry.target_date + ' (' + entry.window_label + ') — ' + entry.location_name;
    header.appendChild(title);

    var score = document.createElement('span');
    score.className = 'score ' + scoreClass(entry.score);
    score.textContent = entry.score.toFixed(1) + ' / 100';
    header.appendChild(score);

    card.appendChild(header);

    var meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = entry.beaufort_name + ' · ' + entry.wind_knots + ' kn (gusts ' + entry.gust_knots +
      ' kn) · ' + entry.temp_c + 'C · ' + entry.precip_probability + '% rain · ' +
      entry.cloud_cover + '% cloud' + (entry.ai_polished ? ' · AI-polished' : '');
    card.appendChild(meta);

    var narrative = document.createElement('p');
    narrative.className = 'narrative';
    narrative.textContent = entry.narrative;
    card.appendChild(narrative);

    return card;
  }}

  function renderEntries(filterText) {{
    var container = document.getElementById('entries-container');
    while (container.firstChild) {{
      container.removeChild(container.firstChild);
    }}
    var filtered = data.entries;
    if (filterText) {{
      var needle = filterText.toLowerCase();
      filtered = data.entries.filter(function(e) {{
        return e.narrative.toLowerCase().indexOf(needle) !== -1 ||
          e.location_name.toLowerCase().indexOf(needle) !== -1;
      }});
    }}
    if (filtered.length === 0) {{
      var empty = document.createElement('p');
      empty.className = 'empty';
      empty.textContent = data.entries.length === 0 ?
        'No trips logged yet. Run "generate" to add one.' : 'No entries match your search.';
      container.appendChild(empty);
      return;
    }}
    filtered.forEach(function(entry) {{
      container.appendChild(buildEntryCard(entry));
    }});
  }}

  document.getElementById('search-box').addEventListener('input', function(e) {{
    renderEntries(e.target.value);
  }});

  renderUpcoming();
  renderEntries('');
}})();
</script>
</body>
</html>
"""


def render_to_file(
    entries: List[Entry],
    upcoming_windows: List[WindowAggregate],
    location_name: str,
    output_path: str,
) -> None:
    html = render_html(entries, upcoming_windows, location_name)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
