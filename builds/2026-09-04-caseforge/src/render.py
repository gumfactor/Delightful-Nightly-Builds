"""Self-contained dark-mode HTML dashboard for the CaseForge case library.

All case data is delivered as an escaped JSON payload inside a
<script type="application/json"> tag and read back via .textContent; every
DOM node the front-end builds from that data uses createElement/
textContent only — never innerHTML — so a case whose title or vignette
contains an injection payload (a real risk, since abstracts are fetched
from a public external source) can never execute as markup.
"""
import json
from typing import List

from .db import Case

_PLACEHOLDER_CASES = "__CASEFORGE_CASES_JSON__"
_PLACEHOLDER_COURSES = "__CASEFORGE_COURSES_JSON__"
_PLACEHOLDER_COUNT = "__CASEFORGE_COUNT__"


def _case_to_dict(case: Case) -> dict:
    return {
        "pmid": case.pmid,
        "course": case.course,
        "title": case.title,
        "citation": case.citation,
        "sampleSize": case.sample_size,
        "population": case.population,
        "methodology": case.methodology,
        "effectSize": case.effect_size_text,
        "pValue": case.p_value_text,
        "vignette": case.vignette_text,
        "vignetteSource": case.vignette_source,
        "questions": case.discussion_questions,
    }


def _safe_json(value) -> str:
    """JSON-encode a value for embedding inside a <script> tag body.

    HTML parses <script> content as raw text up to the literal sequence
    "</", so a title containing "</script>" could otherwise break out of
    the data script and inject a sibling <script> element. Escaping every
    "</" occurrence as "<\\/" (a JSON-legal escape that decodes back to
    "</") neutralizes that without touching any other character.
    """
    return json.dumps(value).replace("</", "<\\/")


def render_dashboard(cases: List[Case]) -> str:
    payload = _safe_json([_case_to_dict(c) for c in cases])
    courses = _safe_json(sorted({c.course for c in cases}))
    html = _TEMPLATE
    html = html.replace(_PLACEHOLDER_CASES, payload)
    html = html.replace(_PLACEHOLDER_COURSES, courses)
    html = html.replace(_PLACEHOLDER_COUNT, str(len(cases)))
    return html


_TEMPLATE = """<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CaseForge — Teaching Case Library</title>
<style>
  :root {
    --bg: #0f1115;
    --panel: #171a21;
    --panel-alt: #1e222b;
    --border: #2a2f3a;
    --text: #e6e9ef;
    --text-dim: #9aa3b2;
    --accent: #7ab8ff;
    --accent-strong: #4f8fe0;
    --badge-bg: #263042;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
  }
  header {
    padding: 24px 20px 12px;
    border-bottom: 1px solid var(--border);
  }
  h1 { margin: 0 0 4px; font-size: 1.5rem; }
  .subtitle { color: var(--text-dim); font-size: 0.9rem; }
  .controls {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
  }
  input[type="search"] {
    flex: 1;
    min-width: 200px;
    padding: 8px 12px;
    background: var(--panel-alt);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-size: 0.95rem;
  }
  .tab-btn {
    padding: 8px 14px;
    background: var(--panel-alt);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-dim);
    cursor: pointer;
    font-size: 0.85rem;
  }
  .tab-btn.active {
    background: var(--accent-strong);
    color: #0b0e13;
    border-color: var(--accent-strong);
    font-weight: 600;
  }
  main { padding: 16px 20px 60px; max-width: 900px; margin: 0 auto; }
  .case-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 16px;
  }
  .case-title { font-size: 1.1rem; font-weight: 600; margin: 0 0 4px; }
  .case-citation { color: var(--text-dim); font-size: 0.85rem; margin: 0 0 10px; font-style: italic; }
  .badges { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
  .badge {
    background: var(--badge-bg);
    color: var(--accent);
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 0.75rem;
  }
  .vignette { margin: 0 0 12px; }
  .questions { margin: 0; padding-left: 20px; }
  .questions li { margin-bottom: 6px; }
  .source-tag {
    font-size: 0.7rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .empty-state { text-align: center; color: var(--text-dim); padding: 60px 20px; }
  @media print {
    .controls { display: none; }
    body { background: #fff; color: #000; }
    .case-card { border: 1px solid #999; break-inside: avoid; }
  }
</style>
</head>
<body>
<header>
  <h1>CaseForge — Teaching Case Library</h1>
  <div class="subtitle"><span id="case-count">__CASEFORGE_COUNT__</span> case(s) grounded in real, live PubMed literature.</div>
</header>
<div class="controls">
  <input type="search" id="search-box" placeholder="Search title, course, or vignette...">
  <div id="course-tabs"></div>
</div>
<main id="case-list"></main>

<script id="case-data" type="application/json">__CASEFORGE_CASES_JSON__</script>
<script id="course-data" type="application/json">__CASEFORGE_COURSES_JSON__</script>
<script>
(function () {
  "use strict";

  var allCases = JSON.parse(document.getElementById("case-data").textContent);
  var allCourses = JSON.parse(document.getElementById("course-data").textContent);
  var state = { course: "All", query: "" };

  var tabsEl = document.getElementById("course-tabs");
  var listEl = document.getElementById("case-list");
  var searchEl = document.getElementById("search-box");

  function makeBadge(text) {
    var span = document.createElement("span");
    span.className = "badge";
    span.textContent = text;
    return span;
  }

  function renderTabs() {
    tabsEl.textContent = "";
    var names = ["All"].concat(allCourses);
    names.forEach(function (name) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "tab-btn" + (name === state.course ? " active" : "");
      btn.textContent = name;
      btn.addEventListener("click", function () {
        state.course = name;
        renderTabs();
        renderList();
      });
      tabsEl.appendChild(btn);
    });
  }

  function matchesFilter(item) {
    if (state.course !== "All" && item.course !== state.course) return false;
    if (!state.query) return true;
    var haystack = (item.title + " " + item.course + " " + item.vignette).toLowerCase();
    return haystack.indexOf(state.query.toLowerCase()) !== -1;
  }

  function renderCase(item) {
    var card = document.createElement("article");
    card.className = "case-card";

    var title = document.createElement("h2");
    title.className = "case-title";
    title.textContent = item.title;
    card.appendChild(title);

    var citation = document.createElement("p");
    citation.className = "case-citation";
    citation.textContent = item.citation;
    card.appendChild(citation);

    var badges = document.createElement("div");
    badges.className = "badges";
    badges.appendChild(makeBadge(item.course));
    if (item.methodology) badges.appendChild(makeBadge(item.methodology));
    if (item.population) badges.appendChild(makeBadge(item.population));
    if (item.sampleSize) badges.appendChild(makeBadge("N=" + item.sampleSize));
    if (item.effectSize) badges.appendChild(makeBadge(item.effectSize));
    if (item.pValue) badges.appendChild(makeBadge(item.pValue));
    card.appendChild(badges);

    var vignette = document.createElement("p");
    vignette.className = "vignette";
    vignette.textContent = item.vignette;
    card.appendChild(vignette);

    var sourceTag = document.createElement("div");
    sourceTag.className = "source-tag";
    sourceTag.textContent = "Vignette source: " + item.vignetteSource;
    card.appendChild(sourceTag);

    var questionsHeading = document.createElement("p");
    questionsHeading.style.margin = "12px 0 4px";
    questionsHeading.style.fontWeight = "600";
    questionsHeading.textContent = "Discussion Questions";
    card.appendChild(questionsHeading);

    var list = document.createElement("ol");
    list.className = "questions";
    (item.questions || []).forEach(function (question) {
      var li = document.createElement("li");
      li.textContent = question;
      list.appendChild(li);
    });
    card.appendChild(list);

    return card;
  }

  function renderList() {
    listEl.textContent = "";
    var filtered = allCases.filter(matchesFilter);
    if (filtered.length === 0) {
      var empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No cases match the current filter.";
      listEl.appendChild(empty);
      return;
    }
    filtered.forEach(function (item) {
      listEl.appendChild(renderCase(item));
    });
  }

  searchEl.addEventListener("input", function (event) {
    state.query = event.target.value;
    renderList();
  });

  renderTabs();
  renderList();
})();
</script>
</body>
</html>
"""
