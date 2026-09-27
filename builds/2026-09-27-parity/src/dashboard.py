"""Renders the self-contained Parity dashboard as a single HTML file.

All dynamic data is delivered as one JSON payload embedded in a
`<script type="application/json">` block, read back via `textContent`
and `JSON.parse`, and built into the DOM with `createElement`/
`textContent` only — never `innerHTML` — so item titles pulled from
Teamwork or Coda can never execute as markup.
"""
from __future__ import annotations

import json

from store import SyncRun

BUCKET_LABELS = {
    "matched_ok": "Matched",
    "status_conflict": "Status Conflicts",
    "teamwork_only": "Teamwork Only",
    "coda_only": "Coda Only",
}


def _escape_for_script_tag(payload: dict) -> str:
    """json.dumps output is safe HTML text except for a literal `</script>` sequence."""
    return json.dumps(payload).replace("</", "<\\/")


def build_payload(runs: list[SyncRun], items: list[dict]) -> dict:
    latest = runs[-1] if runs else None
    return {
        "generated": True,
        "hero": {
            "matched_ok": latest.matched_ok if latest else 0,
            "status_conflict": latest.status_conflict if latest else 0,
            "teamwork_only": latest.teamwork_only if latest else 0,
            "coda_only": latest.coda_only if latest else 0,
        },
        "trend": [
            {"run_at": r.run_at, "gap_size": r.gap_size} for r in runs
        ],
        "items": items,
    }


def render_dashboard(runs: list[SyncRun], items: list[dict]) -> str:
    payload = build_payload(runs, items)
    payload_json = _escape_for_script_tag(payload)

    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Parity — Teamwork &amp; Coda Sync</title>
<style>
  :root {{
    --bg: #0f1216;
    --surface: #171b21;
    --border: #2a2f37;
    --text: #e6e9ee;
    --muted: #9aa4b2;
    --accent: #6ea8fe;
    --ok: #3fb950;
    --warn: #d29922;
    --bad: #f85149;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 16px;
  }}
  h1 {{ font-size: 1.4rem; margin: 0 0 4px; }}
  .subtitle {{ color: var(--muted); margin: 0 0 20px; font-size: 0.9rem; }}
  .hero {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }}
  .stat {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
  }}
  .stat .value {{ font-size: 1.8rem; font-weight: 700; }}
  .stat .label {{ color: var(--muted); font-size: 0.8rem; margin-top: 4px; }}
  .stat.ok .value {{ color: var(--ok); }}
  .stat.warn .value {{ color: var(--warn); }}
  .stat.bad .value {{ color: var(--bad); }}
  canvas {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    max-width: 100%;
    margin-bottom: 24px;
  }}
  section {{ margin-bottom: 28px; }}
  section h2 {{ font-size: 1.05rem; margin-bottom: 10px; }}
  input[type="search"] {{
    width: 100%;
    max-width: 320px;
    padding: 8px 10px;
    margin-bottom: 10px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th, td {{
    text-align: left;
    padding: 8px 10px;
    border-bottom: 1px solid var(--border);
  }}
  th {{ cursor: pointer; color: var(--muted); user-select: none; white-space: nowrap; }}
  th:hover {{ color: var(--text); }}
  .empty {{ color: var(--muted); font-style: italic; padding: 10px 0; }}
  @media (max-width: 480px) {{
    table, thead, tbody, th, td, tr {{ display: block; }}
    th {{ display: none; }}
    td {{
      border: none;
      padding: 4px 0;
    }}
    td::before {{ content: attr(data-label) ": "; color: var(--muted); }}
    tr {{ border-bottom: 1px solid var(--border); padding: 8px 0; }}
  }}
</style>
</head>
<body>
  <h1>Parity</h1>
  <p class="subtitle">Teamwork.com &harr; Coda sync reconciliation</p>

  <div class="hero" id="hero"></div>

  <section>
    <h2>Gap Over Time</h2>
    <canvas id="trend-chart" width="600" height="200" role="img" aria-label="Gap size over successive syncs"></canvas>
  </section>

  <section>
    <h2>Status Conflicts</h2>
    <input type="search" data-table="status_conflict" placeholder="Search status conflicts&hellip;">
    <div data-container="status_conflict"></div>
  </section>

  <section>
    <h2>Teamwork Only</h2>
    <input type="search" data-table="teamwork_only" placeholder="Search Teamwork-only items&hellip;">
    <div data-container="teamwork_only"></div>
  </section>

  <section>
    <h2>Coda Only</h2>
    <input type="search" data-table="coda_only" placeholder="Search Coda-only items&hellip;">
    <div data-container="coda_only"></div>
  </section>

  <script type="application/json" id="parity-data">{payload_json}</script>
  <script>
  (function () {{
    "use strict";
    var data = JSON.parse(document.getElementById("parity-data").textContent);

    function renderHero() {{
      var hero = document.getElementById("hero");
      var stats = [
        {{ key: "matched_ok", label: "Matched", cls: "ok" }},
        {{ key: "status_conflict", label: "Status Conflicts", cls: "warn" }},
        {{ key: "teamwork_only", label: "Teamwork Only", cls: "warn" }},
        {{ key: "coda_only", label: "Coda Only", cls: "bad" }}
      ];
      stats.forEach(function (s) {{
        var card = document.createElement("div");
        card.className = "stat " + s.cls;
        var value = document.createElement("div");
        value.className = "value";
        value.textContent = String(data.hero[s.key]);
        var label = document.createElement("div");
        label.className = "label";
        label.textContent = s.label;
        card.appendChild(value);
        card.appendChild(label);
        hero.appendChild(card);
      }});
    }}

    function renderTrendChart() {{
      var canvas = document.getElementById("trend-chart");
      var ctx = canvas.getContext("2d");
      var trend = data.trend;
      var w = canvas.width, h = canvas.height, pad = 30;
      ctx.clearRect(0, 0, w, h);
      ctx.strokeStyle = "#2a2f37";
      ctx.strokeRect(pad, 10, w - pad - 10, h - pad - 10);

      if (trend.length === 0) {{
        ctx.fillStyle = "#9aa4b2";
        ctx.font = "13px sans-serif";
        ctx.fillText("No sync history yet", pad + 10, h / 2);
        return;
      }}

      var maxGap = Math.max.apply(null, trend.map(function (t) {{ return t.gap_size; }}).concat([1]));
      var innerW = w - pad - 20;
      var innerH = h - pad - 20;
      var stepX = trend.length > 1 ? innerW / (trend.length - 1) : 0;

      ctx.strokeStyle = "#f85149";
      ctx.lineWidth = 2;
      ctx.beginPath();
      trend.forEach(function (t, i) {{
        var x = pad + 10 + i * stepX;
        var y = 10 + innerH - (t.gap_size / maxGap) * innerH;
        if (i === 0) {{ ctx.moveTo(x, y); }} else {{ ctx.lineTo(x, y); }}
      }});
      ctx.stroke();

      ctx.fillStyle = "#f85149";
      trend.forEach(function (t, i) {{
        var x = pad + 10 + i * stepX;
        var y = 10 + innerH - (t.gap_size / maxGap) * innerH;
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      }});
    }}

    function buildTable(bucket, columns) {{
      var container = document.querySelector('[data-container="' + bucket + '"]');
      var rows = data.items.filter(function (item) {{ return item.bucket === bucket; }});
      container.innerHTML = "";

      if (rows.length === 0) {{
        var empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = "Nothing in this bucket.";
        container.appendChild(empty);
        return;
      }}

      var table = document.createElement("table");
      var thead = document.createElement("thead");
      var headRow = document.createElement("tr");
      columns.forEach(function (col) {{
        var th = document.createElement("th");
        th.textContent = col.label;
        th.dataset.key = col.key;
        headRow.appendChild(th);
      }});
      thead.appendChild(headRow);
      table.appendChild(thead);

      var tbody = document.createElement("tbody");
      table.appendChild(tbody);
      container.appendChild(table);

      var sortState = {{ key: null, asc: true }};

      function draw(filterText) {{
        tbody.textContent = "";
        var filtered = rows.filter(function (item) {{
          if (!filterText) return true;
          var haystack = columns.map(function (c) {{ return item[c.key] || ""; }}).join(" ").toLowerCase();
          return haystack.indexOf(filterText.toLowerCase()) !== -1;
        }});
        if (sortState.key) {{
          filtered.sort(function (a, b) {{
            var av = (a[sortState.key] || "").toString().toLowerCase();
            var bv = (b[sortState.key] || "").toString().toLowerCase();
            if (av < bv) return sortState.asc ? -1 : 1;
            if (av > bv) return sortState.asc ? 1 : -1;
            return 0;
          }});
        }}
        filtered.forEach(function (item) {{
          var tr = document.createElement("tr");
          columns.forEach(function (col) {{
            var td = document.createElement("td");
            td.dataset.label = col.label;
            td.textContent = item[col.key] || "—";
            tr.appendChild(td);
          }});
          tbody.appendChild(tr);
        }});
      }}

      headRow.querySelectorAll("th").forEach(function (th) {{
        th.addEventListener("click", function () {{
          var key = th.dataset.key;
          sortState.asc = sortState.key === key ? !sortState.asc : true;
          sortState.key = key;
          draw(searchInput ? searchInput.value : "");
        }});
      }});

      var searchInput = document.querySelector('input[data-table="' + bucket + '"]');
      if (searchInput) {{
        searchInput.addEventListener("input", function () {{ draw(searchInput.value); }});
      }}

      draw("");
    }}

    renderHero();
    renderTrendChart();
    buildTable("status_conflict", [
      {{ key: "teamwork_title", label: "Teamwork Title" }},
      {{ key: "coda_title", label: "Coda Title" }},
      {{ key: "detail", label: "Conflict" }}
    ]);
    buildTable("teamwork_only", [
      {{ key: "teamwork_title", label: "Title" }},
      {{ key: "teamwork_url", label: "URL" }}
    ]);
    buildTable("coda_only", [
      {{ key: "coda_title", label: "Title" }},
      {{ key: "coda_url", label: "URL" }}
    ]);
  }})();
  </script>
</body>
</html>
"""
