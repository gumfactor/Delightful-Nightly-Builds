"""HTML dashboard generator: analytics payload → self-contained HTML file."""

import json
from pathlib import Path
from typing import Any


# Language colours for the chart — a stable, readable palette
LANG_COLORS = [
    "#58a6ff", "#f78166", "#56d364", "#d2a8ff",
    "#ffa657", "#79c0ff", "#ff7b72", "#3dc9b0",
]


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def render_dashboard(data: dict[str, Any], output_path: str) -> None:
    """Write a self-contained HTML dashboard to output_path."""
    data_json = json.dumps(data, ensure_ascii=False)
    generated_at = data.get("generated_at", "")

    lang_colors_json = json.dumps(LANG_COLORS)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GitHub Developer Analytics</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0d1117;
    --surface: #161b22;
    --border: #30363d;
    --text: #c9d1d9;
    --muted: #8b949e;
    --accent: #58a6ff;
    --green: #3fb950;
    --heat-0: #161b22;
    --heat-1: #033a16;
    --heat-2: #196127;
    --heat-3: #239a3b;
    --heat-4: #2ac854;
    --radius: 8px;
    --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    min-height: 100vh;
    padding-bottom: 2rem;
  }}

  header {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
  }}

  header h1 {{
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--text);
  }}

  header span {{
    font-size: 0.8rem;
    color: var(--muted);
  }}

  .tabs {{
    display: flex;
    border-bottom: 1px solid var(--border);
    padding: 0 2rem;
    background: var(--surface);
    overflow-x: auto;
  }}

  .tab {{
    padding: 0.75rem 1.25rem;
    cursor: pointer;
    font-size: 0.9rem;
    color: var(--muted);
    border-bottom: 2px solid transparent;
    white-space: nowrap;
    transition: color 0.15s, border-color 0.15s;
    background: none;
    border-top: none;
    border-left: none;
    border-right: none;
    font-family: var(--font);
  }}

  .tab:hover {{ color: var(--text); }}
  .tab.active {{ color: var(--accent); border-bottom-color: var(--accent); }}

  .panel {{ display: none; padding: 2rem; }}
  .panel.active {{ display: block; }}

  .hero-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }}

  .hero-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
  }}

  .hero-card .value {{
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent);
    line-height: 1;
  }}

  .hero-card .label {{
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 0.4rem;
  }}

  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    margin-bottom: 1.5rem;
  }}

  .card h2 {{
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 1rem;
  }}

  .top-repos-list {{
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }}

  .top-repo-row {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }}

  .top-repo-name {{
    font-size: 0.85rem;
    color: var(--accent);
    width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex-shrink: 0;
  }}

  .top-repo-bar-wrap {{
    flex: 1;
    background: var(--border);
    border-radius: 3px;
    height: 10px;
    overflow: hidden;
  }}

  .top-repo-bar {{
    background: var(--green);
    height: 10px;
    border-radius: 3px;
    transition: width 0.3s;
  }}

  .top-repo-count {{
    font-size: 0.8rem;
    color: var(--muted);
    width: 40px;
    text-align: right;
    flex-shrink: 0;
  }}

  /* Timeline heatmap */
  .heatmap-wrap {{
    overflow-x: auto;
  }}

  .heatmap-table {{
    border-collapse: collapse;
    min-width: 100%;
  }}

  .heatmap-table th {{
    font-size: 0.7rem;
    color: var(--muted);
    padding: 2px 4px;
    white-space: nowrap;
    font-weight: 400;
    text-align: center;
  }}

  .heatmap-table td.repo-label {{
    font-size: 0.75rem;
    color: var(--text);
    padding: 3px 8px 3px 0;
    white-space: nowrap;
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    vertical-align: middle;
  }}

  .heatmap-cell {{
    width: 28px;
    height: 20px;
    border-radius: 3px;
    margin: 1px;
    cursor: default;
    position: relative;
  }}

  .heatmap-cell:hover::after {{
    content: attr(data-tip);
    position: absolute;
    bottom: 120%;
    left: 50%;
    transform: translateX(-50%);
    background: #1f2937;
    color: #e5e7eb;
    font-size: 0.7rem;
    padding: 3px 6px;
    border-radius: 4px;
    white-space: nowrap;
    pointer-events: none;
    z-index: 10;
  }}

  /* Two column rhythm layout */
  .rhythm-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }}

  @media (max-width: 640px) {{
    .rhythm-grid {{ grid-template-columns: 1fr; }}
    header {{ padding: 0.75rem 1rem; }}
    .panel {{ padding: 1rem; }}
    .tabs {{ padding: 0 1rem; }}
  }}

  .chart-container {{
    position: relative;
    height: 280px;
  }}

  .chart-container-tall {{
    position: relative;
    height: 400px;
  }}
</style>
</head>
<body>

<header>
  <h1>⬡ GitHub Developer Analytics</h1>
  <span>Generated {_escape_html(generated_at[:10])}</span>
</header>

<div class="tabs">
  <button class="tab active" data-panel="overview">Overview</button>
  <button class="tab" data-panel="timeline">Timeline</button>
  <button class="tab" data-panel="rhythm">Rhythm</button>
  <button class="tab" data-panel="languages">Languages</button>
</div>

<!-- Overview Panel -->
<div id="panel-overview" class="panel active">
  <div class="hero-grid" id="hero-grid"></div>
  <div class="card">
    <h2>Top Projects by Commits (Last 12 Months)</h2>
    <div class="top-repos-list" id="top-repos-list"></div>
  </div>
</div>

<!-- Timeline Panel -->
<div id="panel-timeline" class="panel">
  <div class="card">
    <h2>Project Activity Timeline — commits per month</h2>
    <div class="heatmap-wrap">
      <table class="heatmap-table" id="heatmap-table"></table>
    </div>
  </div>
</div>

<!-- Rhythm Panel -->
<div id="panel-rhythm" class="panel">
  <div class="rhythm-grid">
    <div class="card">
      <h2>Commits by Hour of Day (UTC)</h2>
      <div class="chart-container">
        <canvas id="chart-hour"></canvas>
      </div>
    </div>
    <div class="card">
      <h2>Commits by Day of Week</h2>
      <div class="chart-container">
        <canvas id="chart-weekday"></canvas>
      </div>
    </div>
  </div>
</div>

<!-- Languages Panel -->
<div id="panel-languages" class="panel">
  <div class="card">
    <h2>Language Distribution by Repository (bytes of code)</h2>
    <div class="chart-container-tall">
      <canvas id="chart-languages"></canvas>
    </div>
  </div>
</div>

<script>
const DATA = {data_json};
const LANG_COLORS = {lang_colors_json};

// Safe text insertion — prevents XSS from any data value
function esc(s) {{
  const d = document.createElement('div');
  d.textContent = String(s);
  return d.innerHTML;
}}

// ── Tab navigation ──────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('panel-' + btn.dataset.panel).classList.add('active');
  }});
}});

// ── Shared Chart.js defaults ────────────────────────────────────────────────
Chart.defaults.color = '#8b949e';
Chart.defaults.borderColor = '#30363d';
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif';

// ── Overview ─────────────────────────────────────────────────────────────────
(function buildOverview() {{
  const heroItems = [
    {{ value: DATA.total_commits.toLocaleString(), label: 'Total Commits (12 mo)' }},
    {{ value: DATA.active_repos, label: 'Active Repositories' }},
    {{ value: DATA.most_active_repo || '—', label: 'Most Active Project' }},
    {{ value: DATA.top_language || '—', label: 'Top Language' }},
  ];
  const grid = document.getElementById('hero-grid');
  heroItems.forEach(item => {{
    const card = document.createElement('div');
    card.className = 'hero-card';
    card.innerHTML = `<div class="value">${{esc(item.value)}}</div><div class="label">${{esc(item.label)}}</div>`;
    grid.appendChild(card);
  }});

  const maxCommits = DATA.top_repos.length ? DATA.top_repos[0].commits : 1;
  const list = document.getElementById('top-repos-list');
  DATA.top_repos.slice(0, 8).forEach(r => {{
    const row = document.createElement('div');
    row.className = 'top-repo-row';
    const pct = Math.round((r.commits / maxCommits) * 100);
    row.innerHTML = `
      <span class="top-repo-name" title="${{esc(r.name)}}">${{esc(r.name)}}</span>
      <div class="top-repo-bar-wrap"><div class="top-repo-bar" style="width:${{pct}}%"></div></div>
      <span class="top-repo-count">${{r.commits}}</span>`;
    list.appendChild(row);
  }});
}})();

// ── Timeline heatmap ─────────────────────────────────────────────────────────
(function buildTimeline() {{
  const tl = DATA.timeline;
  if (!tl.repos.length) return;

  const table = document.getElementById('heatmap-table');
  const maxVal = tl.max_val || 1;

  function heatColor(count) {{
    if (count === 0) return 'var(--heat-0)';
    const frac = Math.min(count / maxVal, 1);
    if (frac < 0.25) return 'var(--heat-1)';
    if (frac < 0.5)  return 'var(--heat-2)';
    if (frac < 0.75) return 'var(--heat-3)';
    return 'var(--heat-4)';
  }}

  // Header row
  const thead = document.createElement('thead');
  const hRow = document.createElement('tr');
  const thLabel = document.createElement('th');
  thLabel.textContent = '';
  hRow.appendChild(thLabel);
  tl.months.forEach(m => {{
    const th = document.createElement('th');
    th.textContent = m.slice(5); // MM
    hRow.appendChild(th);
  }});
  thead.appendChild(hRow);
  table.appendChild(thead);

  // Data rows
  const tbody = document.createElement('tbody');
  tl.repos.forEach((repo, ri) => {{
    const tr = document.createElement('tr');
    const tdLabel = document.createElement('td');
    tdLabel.className = 'repo-label';
    tdLabel.textContent = repo;
    tdLabel.title = repo;
    tr.appendChild(tdLabel);
    tl.data[ri].forEach((count, mi) => {{
      const td = document.createElement('td');
      const cell = document.createElement('div');
      cell.className = 'heatmap-cell';
      cell.style.background = heatColor(count);
      cell.setAttribute('data-tip', `${{repo}} · ${{tl.months[mi]}}: ${{count}} commit${{count !== 1 ? 's' : ''}}`);
      td.appendChild(cell);
      tr.appendChild(td);
    }});
    tbody.appendChild(tr);
  }});
  table.appendChild(tbody);
}})();

// ── Rhythm charts ────────────────────────────────────────────────────────────
(function buildRhythm() {{
  const hourLabels = Array.from({{length: 24}}, (_, i) => `${{String(i).padStart(2, '0')}}:00`);
  new Chart(document.getElementById('chart-hour'), {{
    type: 'bar',
    data: {{
      labels: hourLabels,
      datasets: [{{
        label: 'Commits',
        data: DATA.hour_counts,
        backgroundColor: '#238636',
        borderRadius: 3,
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ grid: {{ color: '#21262d' }} }},
        y: {{ grid: {{ color: '#21262d' }}, beginAtZero: true }},
      }}
    }}
  }});

  const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  new Chart(document.getElementById('chart-weekday'), {{
    type: 'bar',
    data: {{
      labels: dayLabels,
      datasets: [{{
        label: 'Commits',
        data: DATA.weekday_counts,
        backgroundColor: '#1f6feb',
        borderRadius: 3,
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ grid: {{ color: '#21262d' }} }},
        y: {{ grid: {{ color: '#21262d' }}, beginAtZero: true }},
      }}
    }}
  }});
}})();

// ── Language chart ────────────────────────────────────────────────────────────
(function buildLanguages() {{
  const lg = DATA.languages;
  if (!lg.repos.length) return;

  const datasets = lg.langs.map((lang, i) => ({{
    label: lang,
    data: lg.data.map(row => row[i]),
    backgroundColor: LANG_COLORS[i % LANG_COLORS.length],
    borderRadius: 3,
  }}));

  new Chart(document.getElementById('chart-languages'), {{
    type: 'bar',
    data: {{
      labels: lg.repos,
      datasets,
    }},
    options: {{
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{
          display: true,
          position: 'top',
          labels: {{ boxWidth: 12, padding: 12 }},
        }},
        tooltip: {{
          callbacks: {{
            label: ctx => {{
              const val = ctx.raw;
              if (val === 0) return null;
              const kb = val > 1024 ? (val / 1024).toFixed(1) + ' KB' : val + ' B';
              return ` ${{ctx.dataset.label}}: ${{kb}}`;
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          stacked: true,
          grid: {{ color: '#21262d' }},
          ticks: {{
            callback: v => v > 1024 ? (v/1024).toFixed(0)+'K' : v,
          }}
        }},
        y: {{ stacked: true, grid: {{ color: '#21262d' }} }},
      }}
    }}
  }});
}})();
</script>
</body>
</html>"""

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)
