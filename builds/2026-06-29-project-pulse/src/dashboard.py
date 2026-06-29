import html
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple


def _e(text: object) -> str:
    return html.escape(str(text), quote=True)


def _safe_json(obj: object) -> str:
    return json.dumps(obj).replace("<", "\\u003c").replace(">", "\\u003e")


def compute_staleness_days(last_activity_at: Optional[str]) -> Optional[int]:
    if not last_activity_at:
        return None
    try:
        normalized = last_activity_at.replace("Z", "+00:00")
        last = datetime.fromisoformat(normalized)
        now = datetime.now(timezone.utc)
        return max(0, (now - last).days)
    except (ValueError, TypeError):
        return None


def _staleness_badge(days: Optional[int]) -> Tuple[str, str]:
    if days is None:
        return ("No activity", "badge-grey")
    if days <= 2:
        return (f"{days}d ago", "badge-green")
    if days <= 7:
        return (f"{days}d ago", "badge-yellow")
    if days <= 14:
        return (f"{days}d ago", "badge-orange")
    return (f"{days}d ago", "badge-red")


def _build_timeline_data(all_activity: List[dict], projects: List[dict]) -> dict:
    now = datetime.now(timezone.utc)
    days_list = [
        (now - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(29, -1, -1)
    ]

    counts: Dict[str, Dict[str, int]] = {}
    for act in all_activity:
        slug = act.get("project_slug") or ""
        date_str = (act.get("occurred_at") or "")[:10]
        if not slug or date_str not in days_list:
            continue
        if slug not in counts:
            counts[slug] = {}
        counts[slug][date_str] = counts[slug].get(date_str, 0) + 1

    datasets = []
    for project in projects:
        slug = project["slug"]
        color = project.get("color") or "#4a9eff"
        data = [counts.get(slug, {}).get(day, 0) for day in days_list]
        datasets.append({
            "label": project["name"],
            "data": data,
            "backgroundColor": color + "99",
            "borderColor": color,
            "borderWidth": 1,
        })

    return {"labels": days_list, "datasets": datasets}


def render_dashboard(
    projects: List[dict],
    all_activity: List[dict],
    project_activities: Dict[str, List[dict]],
    last_activity_map: Dict[int, Optional[str]],
    generated_at: str,
) -> str:
    timeline_data = _build_timeline_data(all_activity, projects)

    type_icons = {
        "lab": "🔬",
        "code": "💻",
        "writing": "✍️",
        "business": "🏢",
        "personal": "🧠",
    }

    cards_html = ""
    for p in projects:
        slug = p["slug"]
        last_at = last_activity_map.get(p["id"])
        days_stale = compute_staleness_days(last_at)
        badge_label, badge_class = _staleness_badge(days_stale)

        acts = project_activities.get(slug) or []
        act_count = len(acts)
        icon = type_icons.get(p.get("type") or "code", "📁")
        color = p.get("color") or "#4a9eff"

        repo_list = p.get("github_repos") or []
        repos_html = ""
        if repo_list:
            tags = " ".join(
                f'<span class="repo-tag">{_e(r)}</span>' for r in repo_list
            )
            repos_html = f'<div class="repos">{tags}</div>'

        if acts:
            items = ""
            for act in acts[:5]:
                date_str = (act.get("occurred_at") or "")[:10]
                src_icon = "⑆" if act.get("source") == "github" else "✎"
                items += (
                    f'<li>'
                    f'<span class="act-date">{_e(date_str)}</span>'
                    f'<span class="act-icon">{src_icon}</span>'
                    f'<span class="act-title">{_e((act.get("title") or "")[:80])}</span>'
                    f'</li>'
                )
            activity_html = f'<ul class="activity-list">{items}</ul>'
        else:
            activity_html = '<p class="no-activity">No recent activity — run sync or log a note</p>'

        cards_html += f"""
    <div class="project-card" data-slug="{_e(slug)}" data-type="{_e(p.get('type') or 'code')}">
      <div class="card-header" style="border-left:4px solid {_e(color)}">
        <div class="card-title-row">
          <span class="type-icon">{icon}</span>
          <h2 class="project-name">{_e(p['name'])}</h2>
          <span class="badge {_e(badge_class)}">{_e(badge_label)}</span>
        </div>
        <p class="description">{_e(p.get('description') or '')}</p>
        {repos_html}
      </div>
      <div class="card-stats"><span class="stat-item">{act_count} activities (30d)</span></div>
      {activity_html}
    </div>"""

    if not cards_html.strip():
        cards_html = (
            '<div class="empty-state">No active projects. '
            'Run <code>python src/main.py add "My Project" --type code</code> to get started.</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Project Pulse — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0d1117;
    --surface: #161b22;
    --surface2: #21262d;
    --border: #30363d;
    --text: #e6edf3;
    --muted: #8b949e;
    --green: #3fb950;
    --yellow: #d29922;
    --orange: #f0883e;
    --red: #f85149;
    --blue: #4a9eff;
    --gap: 1.25rem;
  }}
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    padding: var(--gap);
  }}
  header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: var(--gap);
    border-bottom: 1px solid var(--border);
    margin-bottom: var(--gap);
    flex-wrap: wrap;
    gap: 0.5rem;
  }}
  header h1 {{ font-size: 1.4rem; font-weight: 700; color: var(--blue); }}
  .gen-at {{ color: var(--muted); font-size: 0.8rem; }}
  .filter-row {{
    display: flex; gap: 0.5rem; margin-bottom: var(--gap); flex-wrap: wrap;
  }}
  .filter-btn {{
    padding: 0.3rem 0.75rem; border-radius: 20px;
    border: 1px solid var(--border); background: var(--surface2);
    color: var(--muted); cursor: pointer; font-size: 0.8rem;
  }}
  .filter-btn.active {{ background: var(--blue); border-color: var(--blue); color: #fff; }}
  .chart-section {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: var(--gap); margin-bottom: var(--gap);
  }}
  .chart-section h2 {{
    font-size: 0.85rem; margin-bottom: var(--gap); color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.05em;
  }}
  .chart-container {{ height: 220px; position: relative; }}
  .projects-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: var(--gap);
  }}
  .project-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; overflow: hidden;
  }}
  .card-header {{ padding: var(--gap); padding-left: calc(var(--gap) + 4px); }}
  .card-title-row {{
    display: flex; align-items: center; gap: 0.5rem;
    margin-bottom: 0.4rem; flex-wrap: wrap;
  }}
  .type-icon {{ font-size: 1.1rem; }}
  .project-name {{ font-size: 1rem; font-weight: 600; flex: 1; min-width: 0; }}
  .description {{ color: var(--muted); font-size: 0.82rem; margin-bottom: 0.4rem; }}
  .repos {{ display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.4rem; }}
  .repo-tag {{
    font-size: 0.72rem; background: var(--surface2);
    border: 1px solid var(--border); border-radius: 4px;
    padding: 0.1rem 0.4rem; color: var(--muted); font-family: monospace;
  }}
  .badge {{
    font-size: 0.72rem; border-radius: 12px;
    padding: 0.15rem 0.5rem; white-space: nowrap;
  }}
  .badge-green  {{ background: rgba(63,185,80,0.15);  color: var(--green);  }}
  .badge-yellow {{ background: rgba(210,153,34,0.15); color: var(--yellow); }}
  .badge-orange {{ background: rgba(240,136,62,0.15); color: var(--orange); }}
  .badge-red    {{ background: rgba(248,81,73,0.15);  color: var(--red);    }}
  .badge-grey   {{ background: var(--surface2);       color: var(--muted);  }}
  .card-stats {{
    padding: 0.4rem var(--gap); background: var(--surface2);
    border-top: 1px solid var(--border); font-size: 0.78rem; color: var(--muted);
  }}
  .activity-list {{
    list-style: none; padding: 0.5rem var(--gap);
    border-top: 1px solid var(--border);
    display: flex; flex-direction: column; gap: 0.35rem;
  }}
  .activity-list li {{
    display: flex; gap: 0.4rem; font-size: 0.78rem; align-items: flex-start;
  }}
  .act-date  {{ color: var(--muted); white-space: nowrap; min-width: 5rem; }}
  .act-icon  {{ color: var(--muted); }}
  .act-title {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .no-activity {{
    color: var(--muted); font-size: 0.8rem; padding: 0.75rem var(--gap);
    border-top: 1px solid var(--border); font-style: italic;
  }}
  .empty-state {{
    color: var(--muted); text-align: center; padding: 3rem;
    font-size: 0.9rem; grid-column: 1/-1;
  }}
  .empty-state code {{
    background: var(--surface2); padding: 0.2rem 0.4rem; border-radius: 4px;
    font-size: 0.85rem;
  }}
  @media (max-width: 600px) {{
    .projects-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<header>
  <h1>⚡ Project Pulse</h1>
  <span class="gen-at">Generated {_e(generated_at)}</span>
</header>

<div class="filter-row">
  <button class="filter-btn active" onclick="filterType('all',this)">All</button>
  <button class="filter-btn" onclick="filterType('lab',this)">🔬 Lab</button>
  <button class="filter-btn" onclick="filterType('code',this)">💻 Code</button>
  <button class="filter-btn" onclick="filterType('writing',this)">✍️ Writing</button>
  <button class="filter-btn" onclick="filterType('business',this)">🏢 Business</button>
  <button class="filter-btn" onclick="filterType('personal',this)">🧠 Personal</button>
</div>

<div class="chart-section">
  <h2>Activity — Last 30 Days</h2>
  <div class="chart-container">
    <canvas id="timelineChart"></canvas>
  </div>
</div>

<div class="projects-grid" id="projectsGrid">
{cards_html}
</div>

<script>
(function() {{
  var data = {_safe_json(timeline_data)};
  var ctx = document.getElementById('timelineChart');
  if (ctx && data.datasets && data.datasets.length > 0) {{
    new Chart(ctx, {{
      type: 'bar',
      data: data,
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ labels: {{ color: '#8b949e', font: {{ size: 11 }} }} }},
          tooltip: {{ mode: 'index', intersect: false }},
        }},
        scales: {{
          x: {{
            stacked: true,
            ticks: {{ color: '#8b949e', maxTicksLimit: 8, font: {{ size: 10 }} }},
            grid: {{ color: '#21262d' }},
          }},
          y: {{
            stacked: true,
            beginAtZero: true,
            ticks: {{ color: '#8b949e', precision: 0, font: {{ size: 11 }} }},
            grid: {{ color: '#21262d' }},
          }},
        }},
      }},
    }});
  }}
}})();

function filterType(type, btn) {{
  document.querySelectorAll('.filter-btn').forEach(function(b) {{
    b.classList.remove('active');
  }});
  btn.classList.add('active');
  document.querySelectorAll('.project-card').forEach(function(card) {{
    card.style.display = (type === 'all' || card.dataset.type === type) ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""
