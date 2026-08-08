"""Terminal and self-contained HTML rendering for Panel Prep."""

from __future__ import annotations

import json
from typing import Any

from .reviewer import SECTION_LABELS


def render_terminal(project_name: str, latest: dict) -> str:
    review = latest["review"]
    checklist_result = latest["checklist"]

    lines = [
        f"Panel Prep — {project_name}",
        "=" * 40,
        f"Version {latest['version_num']} — submitted {latest['submitted_at']}",
        f"Checklist pass rate: {checklist_result['overall_pass_rate'] * 100:.0f}%",
        f"Overall Impact estimate: {review['overall_impact']} (1=exceptional, 9=poor)",
        "",
        "Reviewer scores:",
    ]
    for persona in review["personas"]:
        lines.append(f"  {persona['name']:<20} score {persona['score']}  ({persona['source']})")
        for bullet in persona["rationale"]:
            lines.append(f"      - {bullet}")

    if checklist_result["missing_sections"]:
        missing = ", ".join(SECTION_LABELS[key] for key in checklist_result["missing_sections"])
        lines.append(f"\nMissing sections entirely: {missing}")

    lines.append(f"\nResume of discussion: {review['resume']}")
    return "\n".join(lines)


def _safe_json_for_script(data: Any) -> str:
    """Serialize for embedding inside a <script type="application/json"> element.

    <script> content is HTML "raw text" -- character references are NOT
    decoded by the browser, so html.escape()-ing the quotes would corrupt
    the JSON itself once read back via .textContent. Instead, only the
    substrings that could break out of the script element are neutralized
    using JSON's own \\uXXXX escapes, which remain valid JSON.
    """
    raw = json.dumps(data)
    return raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _build_payload(project_name: str, history: list[dict]) -> dict:
    latest = history[-1]
    return {
        "project": project_name,
        "versions": [
            {
                "version_num": v["version_num"],
                "submitted_at": v["submitted_at"],
                "overall_impact": v["overall_impact"],
                "checklist_pass_rate": round(v["checklist_pass_rate"] * 100, 1),
                "ai_used": v["ai_used"],
            }
            for v in history
        ],
        "latest": {
            "version_num": latest["version_num"],
            "submitted_at": latest["submitted_at"],
            "missing_sections": [SECTION_LABELS[k] for k in latest["checklist"]["missing_sections"]],
            "checklist_sections": [
                {
                    "label": SECTION_LABELS[key],
                    "present": section["present"],
                    "pass_rate": round(section["pass_rate"] * 100, 1),
                    "excerpt": latest["sections"].get(key, "")[:500],
                    "checks": [
                        {"description": check["description"], "passed": check["passed"]}
                        for check in section["checks"].values()
                    ],
                }
                for key, section in latest["checklist"]["sections"].items()
            ],
            "personas": latest["review"]["personas"],
            "overall_impact": latest["review"]["overall_impact"],
            "resume": latest["review"]["resume"],
            "ai_used": latest["review"]["ai_used"],
        },
    }


def render_html(project_name: str, history: list[dict]) -> str:
    if not history:
        raise ValueError("Cannot render a report with no submitted versions")

    payload = _build_payload(project_name, history)
    data_json = _safe_json_for_script(payload)

    version_labels = [f"v{v['version_num']}" for v in payload["versions"]]
    impact_series = [v["overall_impact"] for v in payload["versions"]]
    pass_rate_series = [v["checklist_pass_rate"] for v in payload["versions"]]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Panel Prep — {project_name}</title>
<style>
  :root {{
    --bg: #0f1117; --panel: #1a1d27; --text: #e6e8ef; --muted: #8b90a3;
    --accent: #6ea8fe; --good: #57d38c; --bad: #ff6b6b; --border: #2a2e3d;
  }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system, system-ui, sans-serif;
          margin: 0; padding: 24px; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 4px; }}
  h2 {{ font-size: 1.05rem; margin: 0 0 12px; color: var(--text); }}
  .subtitle {{ color: var(--muted); margin-bottom: 24px; }}
  .hero {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px; }}
  .tile {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
           padding: 12px 16px; min-width: 140px; }}
  .tile .value {{ font-size: 1.6rem; font-weight: 600; }}
  .tile .label {{ color: var(--muted); font-size: 0.85rem; }}
  section {{ margin-bottom: 28px; }}
  .persona-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }}
  .persona-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }}
  .persona-card .score {{ font-size: 1.4rem; font-weight: 600; }}
  .persona-card .source {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }}
  .persona-card ul {{ margin: 8px 0 0; padding-left: 18px; font-size: 0.88rem; color: var(--text); }}
  table {{ width: 100%; border-collapse: collapse; background: var(--panel); border-radius: 8px; overflow: hidden; }}
  th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); font-size: 0.88rem; }}
  th {{ color: var(--muted); font-weight: 500; }}
  .pass {{ color: var(--good); }}
  .fail {{ color: var(--bad); }}
  .resume {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; line-height: 1.5; }}
  .section-block {{ margin-bottom: 16px; }}
  .section-block h3 {{ font-size: 0.95rem; margin: 0 0 6px; }}
  #chart-fallback {{ display: none; }}
</style>
</head>
<body>
<h1>Panel Prep</h1>
<div class="subtitle" id="subtitle"></div>

<section>
  <div class="hero" id="hero"></div>
</section>

<section>
  <h2>Resume of Discussion</h2>
  <div class="resume" id="resume"></div>
</section>

<section>
  <h2>Reviewer Panel</h2>
  <div class="persona-grid" id="persona-grid"></div>
</section>

<section>
  <h2>Completeness &amp; Rigor Checklist</h2>
  <div id="checklist"></div>
</section>

<section>
  <h2>Score Trend Across Versions</h2>
  <canvas id="trend-chart" height="80"></canvas>
  <div id="chart-fallback"></div>
</section>

<script id="panel-data" type="application/json">{data_json}</script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<script>
(function () {{
  const raw = document.getElementById('panel-data').textContent;
  const data = JSON.parse(raw);
  const latest = data.latest;

  document.getElementById('subtitle').textContent =
    data.project + ' — version ' + latest.version_num + ' (' + latest.submitted_at + ')';

  function tile(value, label) {{
    const div = document.createElement('div');
    div.className = 'tile';
    const v = document.createElement('div');
    v.className = 'value';
    v.textContent = String(value);
    const l = document.createElement('div');
    l.className = 'label';
    l.textContent = label;
    div.appendChild(v);
    div.appendChild(l);
    return div;
  }}

  const hero = document.getElementById('hero');
  hero.appendChild(tile(latest.overall_impact, 'Overall Impact (1=best, 9=poor)'));
  hero.appendChild(tile(data.versions.length, 'Versions submitted'));
  hero.appendChild(tile(
    (latest.checklist_sections.reduce((sum, s) => sum + s.pass_rate, 0) / latest.checklist_sections.length).toFixed(0) + '%',
    'Checklist coverage'
  ));
  hero.appendChild(tile(latest.ai_used ? 'AI-assisted' : 'Deterministic only', 'Review source'));

  document.getElementById('resume').textContent = latest.resume +
    (latest.missing_sections.length ? ' Sections not found in the draft: ' + latest.missing_sections.join(', ') + '.' : '');

  const grid = document.getElementById('persona-grid');
  latest.personas.forEach(persona => {{
    const card = document.createElement('div');
    card.className = 'persona-card';

    const name = document.createElement('div');
    name.textContent = persona.name;
    name.style.fontWeight = '600';

    const source = document.createElement('div');
    source.className = 'source';
    source.textContent = persona.source;

    const score = document.createElement('div');
    score.className = 'score';
    score.textContent = 'Score: ' + persona.score;

    const ul = document.createElement('ul');
    persona.rationale.forEach(bullet => {{
      const li = document.createElement('li');
      li.textContent = bullet;
      ul.appendChild(li);
    }});

    card.appendChild(name);
    card.appendChild(source);
    card.appendChild(score);
    card.appendChild(ul);
    grid.appendChild(card);
  }});

  const checklistEl = document.getElementById('checklist');
  latest.checklist_sections.forEach(section => {{
    const block = document.createElement('div');
    block.className = 'section-block';

    const h3 = document.createElement('h3');
    h3.textContent = section.label + ' — ' + section.pass_rate.toFixed(0) + '% ' + (section.present ? '' : '(section not found)');
    block.appendChild(h3);

    if (section.excerpt) {{
      const excerpt = document.createElement('p');
      excerpt.style.color = 'var(--muted)';
      excerpt.style.fontSize = '0.82rem';
      excerpt.style.whiteSpace = 'pre-wrap';
      excerpt.textContent = section.excerpt;
      block.appendChild(excerpt);
    }}

    const table = document.createElement('table');
    const tbody = document.createElement('tbody');
    section.checks.forEach(check => {{
      const tr = document.createElement('tr');
      const tdIcon = document.createElement('td');
      tdIcon.className = check.passed ? 'pass' : 'fail';
      tdIcon.textContent = check.passed ? 'PASS' : 'FAIL';
      tdIcon.style.width = '60px';
      const tdDesc = document.createElement('td');
      tdDesc.textContent = check.description;
      tr.appendChild(tdIcon);
      tr.appendChild(tdDesc);
      tbody.appendChild(tr);
    }});
    table.appendChild(tbody);
    block.appendChild(table);
    checklistEl.appendChild(block);
  }});

  const versionLabels = {json.dumps(version_labels)};
  const impactSeries = {json.dumps(impact_series)};
  const passRateSeries = {json.dumps(pass_rate_series)};

  function drawFallbackTable() {{
    const fallback = document.getElementById('chart-fallback');
    fallback.style.display = 'block';
    const table = document.createElement('table');
    const header = document.createElement('tr');
    ['Version', 'Overall Impact', 'Checklist Pass Rate'].forEach(text => {{
      const th = document.createElement('th');
      th.textContent = text;
      header.appendChild(th);
    }});
    table.appendChild(header);
    versionLabels.forEach((label, i) => {{
      const tr = document.createElement('tr');
      [label, String(impactSeries[i]), passRateSeries[i] + '%'].forEach(text => {{
        const td = document.createElement('td');
        td.textContent = text;
        tr.appendChild(td);
      }});
      table.appendChild(tr);
    }});
    fallback.appendChild(table);
  }}

  if (typeof Chart === 'undefined') {{
    document.getElementById('trend-chart').style.display = 'none';
    drawFallbackTable();
  }} else {{
    const ctx = document.getElementById('trend-chart');
    new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: versionLabels,
        datasets: [
          {{ label: 'Overall Impact (lower=better)', data: impactSeries, borderColor: '#ff6b6b', yAxisID: 'y' }},
          {{ label: 'Checklist Pass Rate (%)', data: passRateSeries, borderColor: '#57d38c', yAxisID: 'y1' }}
        ]
      }},
      options: {{
        scales: {{
          y: {{ position: 'left', min: 1, max: 9, reverse: true, title: {{ display: true, text: 'Impact score' }} }},
          y1: {{ position: 'right', min: 0, max: 100, grid: {{ drawOnChartArea: false }}, title: {{ display: true, text: 'Pass rate %' }} }}
        }}
      }}
    }});
  }}
}})();
</script>
</body>
</html>
"""
