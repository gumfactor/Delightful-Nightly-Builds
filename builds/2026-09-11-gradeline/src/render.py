"""Self-contained dark-mode HTML batch report.

All dynamic data is delivered to the page as a JSON payload inside a
`<script type="application/json">` tag (with '</' escaped so an injected
student identifier can never prematurely close the tag) and built into the
DOM exclusively with `createElement`/`textContent` — never `innerHTML` —
so a script/img-tag payload in a filename-derived identifier can never
execute. The per-criterion class-average bar chart uses Chart.js 4.4.4 from
a CDN when reachable, with a verified DOM-table fallback when it is not.
"""

from __future__ import annotations

import json


def _escape_for_script_tag(json_text: str) -> str:
    return json_text.replace("</", "<\\/")


def _criterion_averages(submissions: list[dict]) -> list[dict]:
    totals: dict[str, dict] = {}
    for sub in submissions:
        for crit in sub["criteria"]:
            if crit["manual_only"] or crit["score"] is None:
                continue
            entry = totals.setdefault(
                crit["name"], {"name": crit["name"], "sum": 0.0, "count": 0, "max_points": crit["max_points"]}
            )
            entry["sum"] += crit["score"]
            entry["count"] += 1
    averages = []
    for entry in totals.values():
        avg = entry["sum"] / entry["count"] if entry["count"] else 0.0
        averages.append({"name": entry["name"], "avg_score": round(avg, 2), "max_points": entry["max_points"]})
    return averages


def build_payload(batch: dict, submissions: list[dict], similarity_pairs: list[dict]) -> dict:
    return {
        "batch": batch,
        "submissions": submissions,
        "similarity_pairs": similarity_pairs,
        "criterion_averages": _criterion_averages(submissions),
    }


def render(batch: dict, submissions: list[dict], similarity_pairs: list[dict]) -> str:
    payload = build_payload(batch, submissions, similarity_pairs)
    payload_json = _escape_for_script_tag(json.dumps(payload))
    html = _TEMPLATE
    html = html.replace("__PAYLOAD_JSON__", payload_json)
    html = html.replace("__RUBRIC_NAME__", _html_escape(batch["rubric_name"]))
    html = html.replace("__COUNT__", str(len(submissions)))
    return html


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GradeLine Report — __RUBRIC_NAME__</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0f1115; --panel: #1a1d24; --border: #2a2e37; --text: #e6e8eb;
    --muted: #9aa1ac; --accent: #6ea8fe; --ok: #5fc98d; --warn: #f5c065; --bad: #f27878;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 24px; line-height: 1.5;
  }
  h1 { font-size: 1.4rem; margin: 0 0 4px; }
  .subtitle { color: var(--muted); margin-bottom: 20px; font-size: 0.9rem; }
  input#search {
    width: 100%; max-width: 480px; padding: 10px 12px; margin-bottom: 20px;
    background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
    color: var(--text); font-size: 0.95rem;
  }
  .panel {
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 18px; margin-bottom: 20px;
  }
  .panel h2 { font-size: 1.05rem; margin: 0 0 12px; }
  .chart-wrap { max-width: 720px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
  th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 600; }
  .card {
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 18px; margin-bottom: 16px;
  }
  .card h3 { margin: 0 0 8px; font-size: 1.0rem; }
  .badge {
    display: inline-block; font-size: 0.72rem; padding: 2px 8px; border-radius: 6px;
    margin-left: 6px; vertical-align: middle;
  }
  .badge.ok { background: #14351f; color: var(--ok); }
  .badge.bad { background: #3a1a1a; color: var(--bad); }
  .meta { color: var(--muted); font-size: 0.85rem; margin-bottom: 10px; }
  .criterion-row { display: flex; justify-content: space-between; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--border); }
  .criterion-row:last-child { border-bottom: none; }
  .crit-name { font-weight: 600; }
  .crit-score { color: var(--accent); white-space: nowrap; }
  .feedback { color: var(--muted); font-size: 0.85rem; margin-top: 4px; white-space: pre-wrap; }
  .sim-flag { background: #3a2f14; color: var(--warn); padding: 8px 10px; border-radius: 6px; margin-bottom: 8px; font-size: 0.88rem; }
  .empty { color: var(--muted); }
  @media (max-width: 480px) { body { padding: 14px; } }
</style>
</head>
<body>
<h1>GradeLine Report</h1>
<div class="subtitle">__RUBRIC_NAME__ — __COUNT__ submission(s)</div>
<input id="search" type="text" placeholder="Search by identifier...">

<div class="panel">
  <h2>Class-Level Criterion Averages</h2>
  <div class="chart-wrap"><canvas id="avg-chart" height="140"></canvas></div>
  <div id="avg-fallback" hidden></div>
</div>

<div class="panel">
  <h2>Possible Over-Similarity (review manually)</h2>
  <div id="sim-panel"></div>
</div>

<div id="cards"></div>

<script type="application/json" id="report-data">__PAYLOAD_JSON__</script>
<script>
(function () {
  var data = JSON.parse(document.getElementById('report-data').textContent);
  var cardsEl = document.getElementById('cards');
  var searchBox = document.getElementById('search');

  function el(tag, opts) {
    var node = document.createElement(tag);
    opts = opts || {};
    if (opts.className) node.className = opts.className;
    if (opts.text !== undefined) node.textContent = opts.text;
    return node;
  }

  function renderSimilarity() {
    var panel = document.getElementById('sim-panel');
    panel.textContent = '';
    if (!data.similarity_pairs.length) {
      panel.appendChild(el('div', { className: 'empty', text: 'No submission pairs above the similarity threshold.' }));
      return;
    }
    data.similarity_pairs.forEach(function (pair) {
      var flag = el('div', { className: 'sim-flag' });
      flag.textContent = pair.a + ' ↔ ' + pair.b + ' — similarity ' + (pair.score * 100).toFixed(1) + '%';
      panel.appendChild(flag);
    });
  }

  function renderAvgFallback() {
    var wrap = document.getElementById('avg-fallback');
    wrap.textContent = '';
    var table = el('table');
    var thead = el('thead');
    var headRow = el('tr');
    ['Criterion', 'Class Average', 'Max Points'].forEach(function (h) {
      headRow.appendChild(el('th', { text: h }));
    });
    thead.appendChild(headRow);
    table.appendChild(thead);
    var tbody = el('tbody');
    data.criterion_averages.forEach(function (row) {
      var tr = el('tr');
      tr.appendChild(el('td', { text: row.name }));
      tr.appendChild(el('td', { text: String(row.avg_score) }));
      tr.appendChild(el('td', { text: String(row.max_points) }));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    wrap.hidden = false;
  }

  function renderChart() {
    if (typeof Chart === 'undefined' || !data.criterion_averages.length) {
      renderAvgFallback();
      return;
    }
    try {
      var ctx = document.getElementById('avg-chart').getContext('2d');
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.criterion_averages.map(function (r) { return r.name; }),
          datasets: [{
            label: 'Class Average',
            data: data.criterion_averages.map(function (r) { return r.avg_score; }),
            backgroundColor: '#6ea8fe'
          }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
      });
    } catch (e) {
      renderAvgFallback();
    }
  }

  function buildCriterionRow(crit) {
    var row = el('div', { className: 'criterion-row' });
    var name = el('div');
    name.appendChild(el('span', { className: 'crit-name', text: crit.name }));
    if (crit.manual_only) {
      name.appendChild(el('span', { className: 'badge', text: ' manual review' }));
    }
    if (crit.feedback) {
      name.appendChild(el('div', { className: 'feedback', text: crit.feedback }));
    }
    row.appendChild(name);
    var scoreText = crit.manual_only || crit.score === null
      ? 'needs manual score'
      : crit.score + ' / ' + crit.max_points;
    row.appendChild(el('div', { className: 'crit-score', text: scoreText }));
    return row;
  }

  function buildCard(sub) {
    var card = el('div', { className: 'card' });
    var h3 = el('h3', { text: sub.identifier });
    card.appendChild(h3);

    var meta = el('div', { className: 'meta' });
    var complianceBits = [];
    complianceBits.push(sub.word_count + ' words');
    complianceBits.push(sub.citation_count + ' citations');
    if (sub.flesch_score !== null) complianceBits.push('Flesch ' + sub.flesch_score);
    meta.textContent = complianceBits.join(' · ');
    var wcBadge = el('span', { className: 'badge ' + (sub.compliance.word_count_ok ? 'ok' : 'bad'), text: sub.compliance.word_count_ok ? 'word count OK' : 'word count out of range' });
    meta.appendChild(wcBadge);
    var secBadge = el('span', { className: 'badge ' + (sub.compliance.sections_ok ? 'ok' : 'bad'), text: sub.compliance.sections_ok ? 'sections OK' : 'missing section(s)' });
    meta.appendChild(secBadge);
    var citeBadge = el('span', { className: 'badge ' + (sub.compliance.citations_ok ? 'ok' : 'bad'), text: sub.compliance.citations_ok ? 'citations OK' : 'below min citations' });
    meta.appendChild(citeBadge);
    card.appendChild(meta);

    if (!sub.compliance.sections_ok) {
      var missing = Object.keys(sub.compliance.sections_found).filter(function (k) { return !sub.compliance.sections_found[k]; });
      card.appendChild(el('div', { className: 'meta', text: 'Missing sections: ' + missing.join(', ') }));
    }

    sub.criteria.forEach(function (crit) {
      card.appendChild(buildCriterionRow(crit));
    });

    return card;
  }

  function renderCards(filterText) {
    cardsEl.textContent = '';
    var q = (filterText || '').toLowerCase();
    var matches = data.submissions.filter(function (sub) {
      return !q || sub.identifier.toLowerCase().indexOf(q) !== -1;
    });
    if (!matches.length) {
      cardsEl.appendChild(el('div', { className: 'empty', text: 'No submissions match your search.' }));
      return;
    }
    matches.forEach(function (sub) { cardsEl.appendChild(buildCard(sub)); });
  }

  searchBox.addEventListener('input', function () { renderCards(searchBox.value); });
  renderSimilarity();
  renderChart();
  renderCards('');
})();
</script>
</body>
</html>
"""
