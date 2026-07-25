"""Self-contained dark-mode HTML dashboard.

All commit-derived text (messages, explanations, repo names) is inserted
via textContent/createElement in the client-side JS below — never via
innerHTML or string-interpolated markup — so a hostile commit message
cannot execute as HTML/JS in the rendered report.
"""

import json

from . import store
from .ai_classify import ai_coaching_summary
from .classify import CATEGORY_LABELS

_CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


def _deterministic_coaching(counts):
    if not counts:
        return "No fix commits recorded yet — run `sync` to get started."
    top = counts[0]
    total = sum(c["count"] for c in counts)
    pct = (top["count"] / total * 100) if total else 0.0
    label = CATEGORY_LABELS.get(top["category"], top["category"])
    return (
        f"Your most common recurring fix pattern is '{label}' "
        f"({top['count']} of {total} fixes, {pct:.0f}%). Consider adding a targeted check for it — "
        "a linter rule, a code review habit, or a small test helper aimed at this specific pattern."
    )


def render_html(conn, ai_api_key=None, ai_request_fn=None):
    fixes = store.get_all_fixes(conn)
    counts = store.category_counts(conn)
    monthly = store.monthly_counts(conn)
    repos = store.repo_counts(conn)

    coaching = None
    if ai_api_key:
        coaching = ai_coaching_summary(ai_api_key, counts, request_fn=ai_request_fn)
    if not coaching:
        coaching = _deterministic_coaching(counts)

    data = {
        "fixes": fixes,
        "counts": [{"label": CATEGORY_LABELS.get(c["category"], c["category"]), **c} for c in counts],
        "monthly": monthly,
        "repos": repos,
        "coaching": coaching,
        "total": sum(c["count"] for c in counts),
    }
    # Safe to embed inside a <script type="application/json"> block: escape
    # any literal "</" so a crafted commit message can't close the tag early.
    json_blob = json.dumps(data).replace("</", "<\\/")

    return _TEMPLATE.replace("__BUGTRACE_DATA__", json_blob).replace("__CHART_CDN__", _CHART_JS_CDN)


_TEMPLATE = """<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>BugTrace — Personal Bug-Pattern Report</title>
<style>
  :root {
    --bg: #0f1117; --panel: #171a23; --border: #2a2f3d; --text: #e6e8ef;
    --muted: #9aa1b4; --accent: #7c9cff; --good: #4ade80;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--text); font-family: -apple-system, Segoe UI, Roboto, sans-serif; }
  header { padding: 24px clamp(16px, 4vw, 48px); border-bottom: 1px solid var(--border); }
  header h1 { margin: 0 0 4px 0; font-size: 1.5rem; }
  header p { margin: 0; color: var(--muted); }
  main { padding: 24px clamp(16px, 4vw, 48px); display: grid; gap: 20px; max-width: 1100px; margin: 0 auto; }
  .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 18px; }
  .panel h2 { margin-top: 0; font-size: 1.05rem; }
  .coaching { border-left: 3px solid var(--accent); }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 700px) { .grid-2 { grid-template-columns: 1fr; } }
  canvas { max-height: 280px; }
  .fallback-table { width: 100%; border-collapse: collapse; }
  .fallback-table td, .fallback-table th { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); }
  input[type="search"] {
    width: 100%; padding: 8px 10px; border-radius: 6px; border: 1px solid var(--border);
    background: #10131b; color: var(--text); margin-bottom: 12px;
  }
  .category-group { margin-bottom: 14px; }
  .category-group summary { cursor: pointer; font-weight: 600; padding: 6px 0; }
  .fix-row { padding: 8px 10px; border-radius: 6px; margin: 4px 0; background: #10131b; font-size: 0.9rem; }
  .fix-row .meta { color: var(--muted); font-size: 0.8rem; }
  .fix-row a { color: var(--accent); text-decoration: none; }
  .badge { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 0.72rem; margin-left: 6px; }
  .badge.ai { background: #2d2450; color: #c7b8ff; }
  .badge.keyword { background: #1f2a3a; color: #9fc8ff; }
  .empty { color: var(--muted); font-style: italic; }
</style>
</head>
<body>
<header>
  <h1>BugTrace</h1>
  <p>Personal bug-pattern report — <span id="total-count">0</span> classified fix commit(s)</p>
</header>
<main>
  <section class="panel coaching">
    <h2>Coaching summary</h2>
    <p id="coaching-text"></p>
  </section>

  <section class="grid-2">
    <div class="panel">
      <h2>By category</h2>
      <canvas id="category-chart"></canvas>
      <table class="fallback-table" id="category-fallback" style="display:none"></table>
    </div>
    <div class="panel">
      <h2>Over time</h2>
      <canvas id="monthly-chart"></canvas>
      <table class="fallback-table" id="monthly-fallback" style="display:none"></table>
    </div>
  </section>

  <section class="panel">
    <h2>Fix commits</h2>
    <input type="search" id="search-box" placeholder="Search messages, repos, categories..." />
    <div id="fix-list"></div>
  </section>
</main>

<script type="application/json" id="bugtrace-data">__BUGTRACE_DATA__</script>
<script src="__CHART_CDN__" onerror="window.__chartLoadFailed = true"></script>
<script>
(function () {
  var data = JSON.parse(document.getElementById("bugtrace-data").textContent);

  document.getElementById("total-count").textContent = String(data.total);
  document.getElementById("coaching-text").textContent = data.coaching;

  function renderFallbackTable(el, rows, headers) {
    el.innerHTML = "";
    var thead = document.createElement("tr");
    headers.forEach(function (h) {
      var th = document.createElement("th");
      th.textContent = h;
      thead.appendChild(th);
    });
    el.appendChild(thead);
    rows.forEach(function (r) {
      var tr = document.createElement("tr");
      r.forEach(function (cell) {
        var td = document.createElement("td");
        td.textContent = String(cell);
        tr.appendChild(td);
      });
      el.appendChild(tr);
    });
    el.style.display = "";
  }

  function renderCharts() {
    var chartsOk = typeof window.Chart !== "undefined" && !window.__chartLoadFailed;

    if (!chartsOk) {
      renderFallbackTable(
        document.getElementById("category-fallback"),
        data.counts.map(function (c) { return [c.label, c.count]; }),
        ["Category", "Count"]
      );
      renderFallbackTable(
        document.getElementById("monthly-fallback"),
        data.monthly.map(function (m) { return [m.month, m.count]; }),
        ["Month", "Count"]
      );
      document.getElementById("category-chart").style.display = "none";
      document.getElementById("monthly-chart").style.display = "none";
      return;
    }

    new Chart(document.getElementById("category-chart"), {
      type: "bar",
      data: {
        labels: data.counts.map(function (c) { return c.label; }),
        datasets: [{ label: "Fix commits", data: data.counts.map(function (c) { return c.count; }), backgroundColor: "#7c9cff" }],
      },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: "#9aa1b4" } }, y: { ticks: { color: "#9aa1b4" } } } },
    });

    new Chart(document.getElementById("monthly-chart"), {
      type: "line",
      data: {
        labels: data.monthly.map(function (m) { return m.month; }),
        datasets: [{ label: "Fixes per month", data: data.monthly.map(function (m) { return m.count; }), borderColor: "#4ade80", tension: 0.25 }],
      },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: "#9aa1b4" } }, y: { ticks: { color: "#9aa1b4" } } } },
    });
  }

  // Give the CDN script a moment to either load or fail before deciding.
  setTimeout(renderCharts, 50);

  function commitUrl(repo, sha) {
    if (!repo || repo.indexOf("/") === -1) return null;
    return "https://github.com/" + repo + "/commit/" + sha;
  }

  function renderFixList(filterText) {
    var container = document.getElementById("fix-list");
    container.innerHTML = "";
    var needle = (filterText || "").toLowerCase();

    var byCategory = {};
    data.fixes.forEach(function (f) {
      if (needle) {
        var haystack = (f.message + " " + f.repo + " " + f.category).toLowerCase();
        if (haystack.indexOf(needle) === -1) return;
      }
      (byCategory[f.category] = byCategory[f.category] || []).push(f);
    });

    var categories = Object.keys(byCategory);
    if (categories.length === 0) {
      var empty = document.createElement("p");
      empty.className = "empty";
      empty.textContent = "No matching fix commits.";
      container.appendChild(empty);
      return;
    }

    categories.forEach(function (cat) {
      var details = document.createElement("details");
      details.className = "category-group";
      details.open = true;
      var summary = document.createElement("summary");
      summary.textContent = cat + " (" + byCategory[cat].length + ")";
      details.appendChild(summary);

      byCategory[cat].forEach(function (f) {
        var row = document.createElement("div");
        row.className = "fix-row";

        var msgLine = document.createElement("div");
        var firstLine = (f.message || "").split("\\n")[0];
        msgLine.textContent = firstLine;

        var badge = document.createElement("span");
        badge.className = "badge " + f.source;
        badge.textContent = f.source;
        msgLine.appendChild(badge);
        row.appendChild(msgLine);

        var meta = document.createElement("div");
        meta.className = "meta";
        var url = commitUrl(f.repo, f.sha);
        if (url) {
          var link = document.createElement("a");
          link.href = url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          link.textContent = f.sha.slice(0, 8);
          meta.appendChild(link);
          meta.appendChild(document.createTextNode(" · " + f.repo + " · " + f.author_date.slice(0, 10)));
        } else {
          meta.textContent = f.sha.slice(0, 8) + " · " + f.repo + " · " + f.author_date.slice(0, 10);
        }
        row.appendChild(meta);

        if (f.explanation) {
          var expl = document.createElement("div");
          expl.className = "meta";
          expl.textContent = f.explanation;
          row.appendChild(expl);
        }

        details.appendChild(row);
      });

      container.appendChild(details);
    });
  }

  renderFixList("");
  document.getElementById("search-box").addEventListener("input", function (e) {
    renderFixList(e.target.value);
  });
})();
</script>
</body>
</html>
"""
