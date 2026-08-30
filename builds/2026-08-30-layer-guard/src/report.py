"""Render an analysis result as a terminal summary, JSON, or a
self-contained dark-mode HTML dashboard."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from src.graph import Cycle, Edge, Evidence, ModuleMetrics
from src.layers import LayerAssignment, Violation


@dataclass(frozen=True)
class AnalysisResult:
    root: str
    modules: list[str]
    edges: list[Edge]
    cycles: list[Cycle]
    metrics: list[ModuleMetrics]
    layer_assignment: LayerAssignment | None
    violations: list[Violation]
    ai_note: str | None
    warnings: list[str]


def _evidence_dicts(evidence: tuple[Evidence, ...]) -> list[dict]:
    return [{"file": e.file, "line": e.line, "statement": e.statement} for e in evidence]


def to_dict(result: AnalysisResult) -> dict:
    return {
        "root": result.root,
        "generated_via": "static AST analysis, no code executed",
        "modules": list(result.modules),
        "edges": [
            {"importer": e.importer, "importee": e.importee, "evidence": _evidence_dicts(e.evidence)}
            for e in result.edges
        ],
        "cycles": [
            {"modules": list(c.modules), "edges": [
                {"importer": e.importer, "importee": e.importee, "evidence": _evidence_dicts(e.evidence)}
                for e in c.edges
            ]}
            for c in result.cycles
        ],
        "metrics": [
            {
                "module": m.module,
                "afferent": m.afferent,
                "efferent": m.efferent,
                "instability": m.instability,
                "structural_risk": m.structural_risk,
            }
            for m in result.metrics
        ],
        "layers": (
            {
                "order": list(result.layer_assignment.order),
                "assigned": dict(result.layer_assignment.assigned),
                "unassigned": list(result.layer_assignment.unassigned),
            }
            if result.layer_assignment is not None
            else None
        ),
        "violations": [
            {
                "importer": v.importer,
                "importer_layer": v.importer_layer,
                "importee": v.importee,
                "importee_layer": v.importee_layer,
                "evidence": _evidence_dicts(v.evidence),
            }
            for v in result.violations
        ],
        "ai_note": result.ai_note,
        "warnings": list(result.warnings),
    }


def render_json(result: AnalysisResult) -> str:
    return json.dumps(to_dict(result), indent=2)


def _color(text: str, code: str, enabled: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if enabled else text


def render_terminal(result: AnalysisResult, use_color: bool | None = None) -> str:
    if use_color is None:
        use_color = os.environ.get("NO_COLOR") is None
    lines = []
    lines.append(f"Layer Guard — {result.root}")
    lines.append(f"  Modules: {len(result.modules)}   Edges: {len(result.edges)}")
    risk_count = sum(1 for m in result.metrics if m.structural_risk)

    if result.cycles:
        lines.append(_color(f"\nCycles found: {len(result.cycles)}", "31", use_color))
        for c in result.cycles:
            lines.append("  " + _color(" -> ".join(c.modules), "31", use_color))
    else:
        lines.append(_color("\nCycles found: 0", "32", use_color))

    if result.layer_assignment is not None:
        if result.violations:
            lines.append(_color(f"\nLayering violations: {len(result.violations)}", "33", use_color))
            for v in result.violations:
                lines.append(
                    f"  {v.importer} ({v.importer_layer}) -> {v.importee} ({v.importee_layer})"
                )
        else:
            lines.append(_color("\nLayering violations: 0", "32", use_color))
        if result.layer_assignment.unassigned:
            lines.append(f"  Unassigned modules: {len(result.layer_assignment.unassigned)}")

    lines.append(f"\nStructurally risky modules: {risk_count}")
    for m in sorted((m for m in result.metrics if m.structural_risk), key=lambda m: -(m.instability or 0))[:5]:
        lines.append(f"  {m.module}  (afferent={m.afferent}, instability={m.instability:.2f})")

    if result.ai_note:
        lines.append("\nNote:")
        lines.append(f"  {result.ai_note}")

    if result.warnings:
        lines.append(f"\nWarnings ({len(result.warnings)}):")
        for w in result.warnings:
            lines.append(f"  - {w}")

    return "\n".join(lines) + "\n"


_LAYER_COLORS = ["#7dd3fc", "#a5b4fc", "#fca5a5", "#fcd34d", "#86efac", "#f0abfc", "#fdba74"]


def render_html(result: AnalysisResult) -> str:
    payload_json = json.dumps(to_dict(result))
    # HTML "raw text" script elements end at the literal sequence "</script"
    # regardless of JSON-string quoting, so every "<" is escaped to a JSON
    # escape sequence that JSON.parse still decodes correctly.
    safe_payload = payload_json.replace("<", "\\u003c")

    layer_colors_json = json.dumps(_LAYER_COLORS)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Layer Guard Report</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ background: #0f1115; color: #e6e6e6; font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; padding: 24px; }}
  h1, h2 {{ font-weight: 600; }}
  .hero {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 16px 0 24px; }}
  .stat {{ background: #171a21; border: 1px solid #2a2e37; border-radius: 10px; padding: 14px 20px; min-width: 140px; }}
  .stat .n {{ font-size: 28px; font-weight: 700; }}
  .stat.bad .n {{ color: #f87171; }}
  .stat.good .n {{ color: #4ade80; }}
  .stat .label {{ color: #9aa1ac; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
  section {{ margin-bottom: 32px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #22252c; }}
  th {{ cursor: pointer; color: #9aa1ac; user-select: none; }}
  tr:hover {{ background: #171a21; }}
  input[type="search"] {{ background: #171a21; border: 1px solid #2a2e37; color: #e6e6e6; padding: 8px 10px; border-radius: 8px; width: 260px; }}
  .cycle, .violation {{ background: #171a21; border: 1px solid #2a2e37; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; }}
  .chain {{ color: #f87171; font-weight: 600; }}
  .evidence {{ color: #9aa1ac; font-size: 12px; margin-top: 4px; }}
  code {{ background: #22252c; padding: 1px 5px; border-radius: 4px; }}
  #graph {{ background: #171a21; border: 1px solid #2a2e37; border-radius: 10px; max-width: 100%; }}
  .empty {{ color: #6b7280; font-style: italic; }}
  @media (max-width: 600px) {{ input[type="search"] {{ width: 100%; }} table {{ font-size: 12px; }} }}
</style>
</head>
<body>

<h1>Layer Guard</h1>
<div id="root-label" class="empty"></div>

<div class="hero" id="hero"></div>

<section>
  <h2>Dependency Graph</h2>
  <canvas id="graph" width="900" height="560"></canvas>
</section>

<section>
  <h2>Cycles</h2>
  <div id="cycles"></div>
</section>

<section>
  <h2>Layering Violations</h2>
  <div id="violations"></div>
</section>

<section>
  <h2>AI Note</h2>
  <p id="ai-note" class="empty"></p>
</section>

<section>
  <h2>Modules</h2>
  <input type="search" id="search" placeholder="Filter modules...">
  <table id="metrics-table">
    <thead>
      <tr>
        <th data-key="module">Module</th>
        <th data-key="afferent">Afferent (Ca)</th>
        <th data-key="efferent">Efferent (Ce)</th>
        <th data-key="instability">Instability</th>
        <th data-key="layer">Layer</th>
        <th data-key="structural_risk">Risk</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>
</section>

<script type="application/json" id="lg-data">{safe_payload}</script>
<script>
(function () {{
  var DATA = JSON.parse(document.getElementById('lg-data').textContent);
  var LAYER_COLORS = {layer_colors_json};

  document.getElementById('root-label').textContent = 'Scan root: ' + DATA.root;

  function statEl(label, value, cls) {{
    var div = document.createElement('div');
    div.className = 'stat' + (cls ? ' ' + cls : '');
    var n = document.createElement('div');
    n.className = 'n';
    n.textContent = String(value);
    var l = document.createElement('div');
    l.className = 'label';
    l.textContent = label;
    div.appendChild(n);
    div.appendChild(l);
    return div;
  }}

  var hero = document.getElementById('hero');
  hero.appendChild(statEl('Modules', DATA.modules.length));
  hero.appendChild(statEl('Edges', DATA.edges.length));
  hero.appendChild(statEl('Cycles', DATA.cycles.length, DATA.cycles.length ? 'bad' : 'good'));
  hero.appendChild(statEl('Violations', DATA.violations.length, DATA.violations.length ? 'bad' : 'good'));
  var riskCount = DATA.metrics.filter(function (m) {{ return m.structural_risk; }}).length;
  hero.appendChild(statEl('Structural Risk', riskCount, riskCount ? 'bad' : 'good'));

  function evidenceBlock(evidence) {{
    var div = document.createElement('div');
    div.className = 'evidence';
    evidence.forEach(function (e) {{
      var line = document.createElement('div');
      var codeEl = document.createElement('code');
      codeEl.textContent = e.file + ':' + e.line;
      line.appendChild(codeEl);
      line.appendChild(document.createTextNode('  ' + e.statement));
      div.appendChild(line);
    }});
    return div;
  }}

  var cyclesDiv = document.getElementById('cycles');
  if (DATA.cycles.length === 0) {{
    var none = document.createElement('p');
    none.className = 'empty';
    none.textContent = 'No import cycles found.';
    cyclesDiv.appendChild(none);
  }} else {{
    DATA.cycles.forEach(function (c) {{
      var box = document.createElement('div');
      box.className = 'cycle';
      var chain = document.createElement('div');
      chain.className = 'chain';
      chain.textContent = c.modules.join(' -> ');
      box.appendChild(chain);
      c.edges.forEach(function (e) {{ box.appendChild(evidenceBlock(e.evidence)); }});
      cyclesDiv.appendChild(box);
    }});
  }}

  var violationsDiv = document.getElementById('violations');
  if (!DATA.layers) {{
    var noLayers = document.createElement('p');
    noLayers.className = 'empty';
    noLayers.textContent = 'No layer configuration supplied — run with --layers to check layering rules.';
    violationsDiv.appendChild(noLayers);
  }} else if (DATA.violations.length === 0) {{
    var noneV = document.createElement('p');
    noneV.className = 'empty';
    noneV.textContent = 'No layering violations found.';
    violationsDiv.appendChild(noneV);
  }} else {{
    DATA.violations.forEach(function (v) {{
      var box = document.createElement('div');
      box.className = 'violation';
      var chain = document.createElement('div');
      chain.className = 'chain';
      chain.textContent = v.importer + ' (' + v.importer_layer + ')  ->  ' + v.importee + ' (' + v.importee_layer + ')';
      box.appendChild(chain);
      box.appendChild(evidenceBlock(v.evidence));
      violationsDiv.appendChild(box);
    }});
  }}

  var aiNoteEl = document.getElementById('ai-note');
  if (DATA.ai_note) {{
    aiNoteEl.textContent = DATA.ai_note;
    aiNoteEl.classList.remove('empty');
  }} else {{
    aiNoteEl.textContent = 'No AI note generated.';
  }}

  var cycleEdgeSet = {{}};
  DATA.cycles.forEach(function (c) {{
    c.edges.forEach(function (e) {{ cycleEdgeSet[e.importer + '|' + e.importee] = true; }});
  }});
  var violationEdgeSet = {{}};
  DATA.violations.forEach(function (v) {{ violationEdgeSet[v.importer + '|' + v.importee] = true; }});
  var layerOf = (DATA.layers && DATA.layers.assigned) || {{}};
  var layerOrder = (DATA.layers && DATA.layers.order) || [];

  var canvas = document.getElementById('graph');
  var ctx = canvas.getContext('2d');
  var cx = canvas.width / 2, cy = canvas.height / 2, radius = Math.min(cx, cy) - 60;
  var positions = {{}};
  DATA.modules.forEach(function (m, i) {{
    var angle = (2 * Math.PI * i) / Math.max(DATA.modules.length, 1);
    positions[m] = {{ x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) }};
  }});

  DATA.edges.forEach(function (e) {{
    var a = positions[e.importer], b = positions[e.importee];
    if (!a || !b) return;
    var key = e.importer + '|' + e.importee;
    ctx.strokeStyle = cycleEdgeSet[key] ? '#f87171' : (violationEdgeSet[key] ? '#fb923c' : '#3a3f4b');
    ctx.lineWidth = cycleEdgeSet[key] || violationEdgeSet[key] ? 2 : 1;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
  }});

  DATA.modules.forEach(function (m) {{
    var p = positions[m];
    var layer = layerOf[m];
    var colorIndex = layer ? layerOrder.indexOf(layer) : -1;
    ctx.fillStyle = colorIndex >= 0 ? LAYER_COLORS[colorIndex % LAYER_COLORS.length] : '#6b7280';
    ctx.beginPath();
    ctx.arc(p.x, p.y, 5, 0, 2 * Math.PI);
    ctx.fill();
  }});

  var metricsByModule = {{}};
  DATA.metrics.forEach(function (m) {{ metricsByModule[m.module] = m; }});

  var tbody = document.querySelector('#metrics-table tbody');
  var sortKey = 'module', sortAsc = true;

  function renderTable(filterText) {{
    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
    var rows = DATA.metrics.map(function (m) {{
      return {{
        module: m.module,
        afferent: m.afferent,
        efferent: m.efferent,
        instability: m.instability,
        layer: layerOf[m.module] || '(unassigned)',
        structural_risk: m.structural_risk,
      }};
    }});
    if (filterText) {{
      var needle = filterText.toLowerCase();
      rows = rows.filter(function (r) {{ return r.module.toLowerCase().indexOf(needle) !== -1; }});
    }}
    rows.sort(function (a, b) {{
      var av = a[sortKey], bv = b[sortKey];
      if (av == null) av = -1;
      if (bv == null) bv = -1;
      if (av < bv) return sortAsc ? -1 : 1;
      if (av > bv) return sortAsc ? 1 : -1;
      return 0;
    }});
    rows.forEach(function (r) {{
      var tr = document.createElement('tr');
      [r.module, r.afferent, r.efferent, r.instability == null ? 'n/a' : r.instability.toFixed(2), r.layer, r.structural_risk ? 'yes' : ''].forEach(function (val) {{
        var td = document.createElement('td');
        td.textContent = String(val);
        tr.appendChild(td);
      }});
      tbody.appendChild(tr);
    }});
  }}

  document.querySelectorAll('#metrics-table th').forEach(function (th) {{
    th.addEventListener('click', function () {{
      var key = th.getAttribute('data-key');
      if (sortKey === key) {{ sortAsc = !sortAsc; }} else {{ sortKey = key; sortAsc = true; }}
      renderTable(document.getElementById('search').value);
    }});
  }});

  document.getElementById('search').addEventListener('input', function (e) {{
    renderTable(e.target.value);
  }});

  renderTable('');
}})();
</script>
</body>
</html>
"""
