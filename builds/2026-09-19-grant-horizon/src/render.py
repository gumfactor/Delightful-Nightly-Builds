"""Dashboard HTML + CSV rendering.

The dashboard embeds all data as a single JSON block inside a
`<script type="application/json">` element. Every "</" in the JSON text is
replaced with the JSON-legal escape "<\\/" before embedding, which is a
no-op for `JSON.parse` (backslash-escaped forward slash is valid JSON and
decodes back to a plain "/") but stops the HTML tokenizer from ever matching
a literal `</script` sequence inside attacker-controlled data, so a hostile
project title can never terminate the script block early. The client-side
JS then renders every value via `textContent` (never `innerHTML`), so even
markup-shaped strings are always displayed as inert text.
"""
from __future__ import annotations

import csv
import io
import json
from typing import Optional

import aggregate
from slug import slugify

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


def _embed_json(data: dict) -> str:
    return json.dumps(data).replace("</", "<\\/")


def build_dashboard_data(
    projects: list,
    topics: list,
    fiscal_year_start: int,
    fiscal_year_end: int,
    generated_at: str,
    briefings: Optional[dict] = None,
) -> dict:
    """Assemble the full data payload the dashboard's JS reads."""
    briefings = briefings or {}
    per_topic_years = aggregate.funding_by_year_per_topic(projects)

    topic_rows = []
    for topic in topics:
        topic_projects = [p for p in projects if p.topic == topic]
        year_totals = per_topic_years.get(topic, {})
        years_sorted = sorted(year_totals.keys())
        topic_rows.append({
            "topic": topic,
            "slug": slugify(topic),
            "total_funding": aggregate.total_funding(topic_projects),
            "project_count": len(topic_projects),
            "years": [
                {"year": year, "total": round(year_totals[year]["total_amount"], 2),
                 "count": year_totals[year]["count"]}
                for year in years_sorted
            ],
            "briefing": briefings.get(topic),
        })

    # Cross-topic aggregates must dedupe first: a single award that matched more
    # than one configured topic is stored once per topic (correct for the
    # per-topic totals above), but would otherwise have its funding counted
    # once per topic here too. See aggregate.dedupe_by_project.
    deduped_projects = aggregate.dedupe_by_project(projects)

    institutions = aggregate.top_institutions(deduped_projects, n=10)
    agencies = aggregate.agency_breakdown(deduped_projects)
    agency_rows = sorted(
        ({"agency": name, "total": round(data["total_amount"], 2), "count": data["count"]}
         for name, data in agencies.items()),
        key=lambda row: (-row["total"], row["agency"]),
    )

    # Deliberately NOT deduped: the project table shows one row per topic an
    # award matched (labeled by that topic), which is informative on its own,
    # unlike the summed totals above. So its row count can exceed hero.total_projects
    # whenever an award matched more than one configured topic.
    project_rows = [
        {
            "topic": p.topic,
            "title": p.title,
            "fiscal_year": p.fiscal_year,
            "award_amount": round(p.award_amount, 2),
            "org_name": p.org_name,
            "org_state": p.org_state,
            "org_country": p.org_country,
            "agency_ic": p.agency_ic,
            "pi_names": p.pi_names,
        }
        for p in projects
    ]

    return {
        "generated_at": generated_at,
        "hero": {
            "total_funding": round(aggregate.total_funding(deduped_projects), 2),
            "total_projects": len(deduped_projects),
            "topic_count": len(topics),
            "fiscal_year_start": fiscal_year_start,
            "fiscal_year_end": fiscal_year_end,
        },
        "topics": topic_rows,
        "top_institutions": [
            {"name": name, "total": round(total, 2), "count": count}
            for name, total, count in institutions
        ],
        "agency_breakdown": agency_rows,
        "projects": project_rows,
    }


def render_dashboard(data: dict) -> str:
    """Render the full self-contained dashboard HTML from a data payload."""
    embedded = _embed_json(data)
    html = _TEMPLATE.replace("__DATA_JSON__", embedded)
    html = html.replace("__CHART_JS_CDN__", CHART_JS_CDN)
    return html


_FORMULA_LEADING_CHARS = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value: str) -> str:
    """Neutralize spreadsheet formula injection.

    Excel, Google Sheets, and LibreOffice Calc all evaluate a cell as a
    formula if it starts with `=`, `+`, `-`, `@`, or a leading tab/CR, even
    when the source file is plain CSV. NIH-supplied text (project titles,
    institution names) is free text from a public database, not guaranteed
    formula-safe, so every string cell is checked before being written.
    Prefixing with a single quote is the standard neutralizer: spreadsheet
    software displays the cell as literal text instead of evaluating it.
    """
    if value and value[0] in _FORMULA_LEADING_CHARS:
        return "'" + value
    return value


def render_projects_csv(projects: list) -> str:
    """CSV export of every tracked project (uses csv.writer, so commas/quotes in
    titles or institution names are always correctly quoted, never hand-escaped;
    every string cell is also passed through `_csv_safe` against formula injection)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "topic", "project_num", "core_project_num", "title", "fiscal_year",
        "award_amount", "org_name", "org_city", "org_state", "org_country",
        "pi_names", "agency_ic", "start_date", "end_date",
    ])
    for p in projects:
        writer.writerow([
            _csv_safe(p.topic), _csv_safe(p.project_num), _csv_safe(p.core_project_num),
            _csv_safe(p.title), p.fiscal_year, f"{p.award_amount:.2f}",
            _csv_safe(p.org_name), _csv_safe(p.org_city), _csv_safe(p.org_state),
            _csv_safe(p.org_country), _csv_safe("; ".join(p.pi_names)), _csv_safe(p.agency_ic),
            _csv_safe(p.start_date or ""), _csv_safe(p.end_date or ""),
        ])
    return buffer.getvalue()


_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Grant Horizon</title>
<style>
  :root {
    --bg: #0f1115; --panel: #171a21; --panel-2: #1e222b; --border: #2a2f3a;
    --text: #e6e8ec; --text-dim: #9aa1ad; --accent: #5b9dff; --accent-2: #7ee787;
    --danger: #ff6b6b; --radius: 10px;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5; padding: 16px;
  }
  h1 { font-size: 1.5rem; margin: 0 0 4px; }
  h2 { font-size: 1.1rem; margin: 0 0 12px; color: var(--text); }
  .meta { color: var(--text-dim); font-size: 0.85rem; margin-bottom: 20px; }
  .hero { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 24px; }
  .stat { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; }
  .stat .value { font-size: 1.4rem; font-weight: 700; color: var(--accent); }
  .stat .label { font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.04em; }
  .panel { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin-bottom: 20px; }
  .topic-panel { background: var(--panel-2); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; margin-bottom: 14px; }
  .briefing { font-size: 0.9rem; color: var(--text-dim); border-left: 3px solid var(--accent); padding-left: 10px; margin-top: 10px; }
  canvas { max-width: 100%; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); }
  th { color: var(--text-dim); cursor: pointer; user-select: none; white-space: nowrap; }
  th.sorted::after { content: " \\25BE"; color: var(--accent); }
  tr:hover td { background: rgba(255,255,255,0.03); }
  input[type=search] {
    width: 100%; max-width: 320px; padding: 8px 10px; margin-bottom: 12px;
    background: var(--panel-2); border: 1px solid var(--border); border-radius: 8px; color: var(--text);
  }
  .fallback-table { display: none; }
  .fallback-table.active { display: block; }
  .table-wrap { overflow-x: auto; }
  @media (max-width: 600px) {
    .hero { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>
<h1>Grant Horizon</h1>
<div class="meta" id="generatedAt"></div>

<div class="hero" id="hero"></div>

<div class="panel">
  <h2>Funding by fiscal year, per topic</h2>
  <canvas id="trendChart" height="110"></canvas>
  <div class="fallback-table table-wrap" id="trendFallback"></div>
</div>

<div class="panel">
  <h2>Top funded institutions</h2>
  <canvas id="institutionsChart" height="110"></canvas>
  <div class="fallback-table table-wrap" id="institutionsFallback"></div>
</div>

<div class="panel">
  <h2>Agency / IC breakdown</h2>
  <div class="table-wrap" id="agencyTableWrap"></div>
</div>

<div class="panel" id="topicPanels"></div>

<div class="panel">
  <h2>Tracked projects</h2>
  <input type="search" id="searchBox" placeholder="Search title, institution, or PI...">
  <div class="table-wrap">
    <table id="projectsTable">
      <thead>
        <tr>
          <th data-key="topic" tabindex="0" role="button" aria-sort="none">Topic</th>
          <th data-key="fiscal_year" tabindex="0" role="button" aria-sort="none">FY</th>
          <th data-key="award_amount" tabindex="0" role="button" aria-sort="descending">Award</th>
          <th data-key="title" tabindex="0" role="button" aria-sort="none">Title</th>
          <th data-key="org_name" tabindex="0" role="button" aria-sort="none">Institution</th>
          <th data-key="agency_ic" tabindex="0" role="button" aria-sort="none">Agency</th>
        </tr>
      </thead>
      <tbody id="projectsBody"></tbody>
    </table>
  </div>
</div>

<script type="application/json" id="data-payload">__DATA_JSON__</script>
<script src="__CHART_JS_CDN__" onerror="window.__chartJsFailed = true;"></script>
<script>
(function () {
  "use strict";
  var data = JSON.parse(document.getElementById("data-payload").textContent);

  function fmtMoney(n) {
    return "$" + Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });
  }

  function el(tag, attrs, text) {
    var node = document.createElement(tag);
    if (attrs) {
      for (var key in attrs) { node.setAttribute(key, attrs[key]); }
    }
    if (text !== undefined && text !== null) { node.textContent = text; }
    return node;
  }

  // Generated-at line
  document.getElementById("generatedAt").textContent =
    "Generated " + data.generated_at + " · " + data.hero.topic_count + " topics · FY" +
    data.hero.fiscal_year_start + "–FY" + data.hero.fiscal_year_end;

  // Hero stats
  var hero = document.getElementById("hero");
  var heroStats = [
    ["Total tracked funding", fmtMoney(data.hero.total_funding)],
    ["Projects tracked", data.hero.total_projects],
    ["Topics", data.hero.topic_count],
    ["Fiscal years", data.hero.fiscal_year_start + "–" + data.hero.fiscal_year_end],
  ];
  heroStats.forEach(function (pair) {
    var card = el("div", { class: "stat" });
    card.appendChild(el("div", { class: "value" }, String(pair[1])));
    card.appendChild(el("div", { class: "label" }, pair[0]));
    hero.appendChild(card);
  });

  // Topic panels (with optional AI briefing)
  var topicPanels = document.getElementById("topicPanels");
  topicPanels.appendChild(el("h2", null, "Per-topic summary"));
  data.topics.forEach(function (topic) {
    var panel = el("div", { class: "topic-panel" });
    panel.appendChild(el("h2", null, topic.topic));
    panel.appendChild(el("div", { class: "meta" },
      topic.project_count + " projects · " + fmtMoney(topic.total_funding) + " tracked"));
    if (topic.briefing) {
      panel.appendChild(el("div", { class: "briefing" }, topic.briefing));
    }
    topicPanels.appendChild(panel);
  });

  // Agency table
  var agencyWrap = document.getElementById("agencyTableWrap");
  var agencyTable = el("table");
  var agencyHead = el("thead");
  var agencyHeadRow = el("tr");
  ["Agency", "Total", "Projects"].forEach(function (h) { agencyHeadRow.appendChild(el("th", null, h)); });
  agencyHead.appendChild(agencyHeadRow);
  agencyTable.appendChild(agencyHead);
  var agencyBody = el("tbody");
  data.agency_breakdown.forEach(function (row) {
    var tr = el("tr");
    tr.appendChild(el("td", null, row.agency));
    tr.appendChild(el("td", null, fmtMoney(row.total)));
    tr.appendChild(el("td", null, String(row.count)));
    agencyBody.appendChild(tr);
  });
  agencyTable.appendChild(agencyBody);
  agencyWrap.appendChild(agencyTable);

  // Projects table (search + sort)
  var projectsBody = document.getElementById("projectsBody");
  var currentSort = { key: "award_amount", dir: -1 };
  var currentFilter = "";

  function projectMatches(p, q) {
    if (!q) return true;
    var haystack = (p.title + " " + p.org_name + " " + p.pi_names.join(" ")).toLowerCase();
    return haystack.indexOf(q) !== -1;
  }

  function renderProjects() {
    var rows = data.projects.filter(function (p) { return projectMatches(p, currentFilter); });
    rows.sort(function (a, b) {
      var av = a[currentSort.key], bv = b[currentSort.key];
      if (typeof av === "string") { av = av.toLowerCase(); bv = bv.toLowerCase(); }
      if (av < bv) return -1 * currentSort.dir;
      if (av > bv) return 1 * currentSort.dir;
      return 0;
    });
    projectsBody.textContent = "";
    rows.forEach(function (p) {
      var tr = el("tr");
      tr.appendChild(el("td", null, p.topic));
      tr.appendChild(el("td", null, String(p.fiscal_year)));
      tr.appendChild(el("td", null, fmtMoney(p.award_amount)));
      tr.appendChild(el("td", null, p.title));
      tr.appendChild(el("td", null, p.org_name + (p.org_state ? ", " + p.org_state : "")));
      tr.appendChild(el("td", null, p.agency_ic));
      projectsBody.appendChild(tr);
    });
  }

  document.getElementById("searchBox").addEventListener("input", function (e) {
    currentFilter = e.target.value.trim().toLowerCase();
    renderProjects();
  });

  function applySort(th) {
    var key = th.getAttribute("data-key");
    if (currentSort.key === key) {
      currentSort.dir *= -1;
    } else {
      currentSort.key = key;
      currentSort.dir = -1;
    }
    document.querySelectorAll("#projectsTable th").forEach(function (h) {
      h.classList.remove("sorted");
      h.setAttribute("aria-sort", "none");
    });
    th.classList.add("sorted");
    th.setAttribute("aria-sort", currentSort.dir === -1 ? "descending" : "ascending");
    renderProjects();
  }

  document.querySelectorAll("#projectsTable th[data-key]").forEach(function (th) {
    th.addEventListener("click", function () { applySort(th); });
    // Keyboard-operable per WAI-ARIA button semantics: Enter and Space both activate.
    th.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") {
        e.preventDefault();
        applySort(th);
      }
    });
  });

  renderProjects();

  // Charts, with a DOM-table fallback if the Chart.js CDN was blocked
  function buildTrendFallback() {
    var wrap = document.getElementById("trendFallback");
    var table = el("table");
    var thead = el("thead");
    var headRow = el("tr");
    headRow.appendChild(el("th", null, "Topic"));
    headRow.appendChild(el("th", null, "Fiscal Year"));
    headRow.appendChild(el("th", null, "Total"));
    thead.appendChild(headRow);
    table.appendChild(thead);
    var tbody = el("tbody");
    data.topics.forEach(function (topic) {
      topic.years.forEach(function (y) {
        var tr = el("tr");
        tr.appendChild(el("td", null, topic.topic));
        tr.appendChild(el("td", null, String(y.year)));
        tr.appendChild(el("td", null, fmtMoney(y.total)));
        tbody.appendChild(tr);
      });
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    wrap.classList.add("active");
  }

  function buildInstitutionsFallback() {
    var wrap = document.getElementById("institutionsFallback");
    var table = el("table");
    var thead = el("thead");
    var headRow = el("tr");
    headRow.appendChild(el("th", null, "Institution"));
    headRow.appendChild(el("th", null, "Total"));
    headRow.appendChild(el("th", null, "Projects"));
    thead.appendChild(headRow);
    table.appendChild(thead);
    var tbody = el("tbody");
    data.top_institutions.forEach(function (row) {
      var tr = el("tr");
      tr.appendChild(el("td", null, row.name));
      tr.appendChild(el("td", null, fmtMoney(row.total)));
      tr.appendChild(el("td", null, String(row.count)));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    wrap.classList.add("active");
  }

  function chartJsAvailable() {
    return typeof window.Chart !== "undefined" && !window.__chartJsFailed;
  }

  function initCharts() {
    if (!chartJsAvailable()) {
      buildTrendFallback();
      buildInstitutionsFallback();
      return;
    }
    var allYears = [];
    data.topics.forEach(function (t) { t.years.forEach(function (y) { if (allYears.indexOf(y.year) === -1) allYears.push(y.year); }); });
    allYears.sort();

    var palette = ["#5b9dff", "#7ee787", "#ff6b6b", "#f0b429", "#c792ea", "#4dd0e1"];
    var datasets = data.topics.map(function (topic, i) {
      var byYear = {};
      topic.years.forEach(function (y) { byYear[y.year] = y.total; });
      return {
        label: topic.topic,
        data: allYears.map(function (y) { return byYear[y] || 0; }),
        borderColor: palette[i % palette.length],
        backgroundColor: palette[i % palette.length],
        fill: false,
        tension: 0.2,
      };
    });

    new window.Chart(document.getElementById("trendChart"), {
      type: "line",
      data: { labels: allYears, datasets: datasets },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: "#e6e8ec" } } },
        scales: {
          x: { ticks: { color: "#9aa1ad" }, grid: { color: "#2a2f3a" } },
          y: { ticks: { color: "#9aa1ad" }, grid: { color: "#2a2f3a" } },
        },
      },
    });

    new window.Chart(document.getElementById("institutionsChart"), {
      type: "bar",
      data: {
        labels: data.top_institutions.map(function (r) { return r.name; }),
        datasets: [{
          label: "Total funding",
          data: data.top_institutions.map(function (r) { return r.total; }),
          backgroundColor: "#5b9dff",
        }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#9aa1ad" }, grid: { color: "#2a2f3a" } },
          y: { ticks: { color: "#9aa1ad" }, grid: { color: "#2a2f3a" } },
        },
      },
    });
  }

  window.addEventListener("load", function () {
    setTimeout(initCharts, 50);
  });
})();
</script>
</body>
</html>
"""
