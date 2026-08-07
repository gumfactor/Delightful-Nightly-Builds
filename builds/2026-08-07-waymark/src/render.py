"""Renders the indexed commit history into a single self-contained HTML dashboard."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def _commit_to_dict(row: Any) -> dict[str, Any]:
    return {
        "repo": row["repo_label"],
        "hash": row["commit_hash"],
        "shortHash": row["commit_hash"][:8],
        "author": row["author"],
        "date": row["committed_at"],
        "subject": row["subject"],
        "body": row["body"],
        "filesChanged": row["files_changed"],
        "insertions": row["insertions"],
        "deletions": row["deletions"],
        "score": row["decision_score"],
        "tags": json.loads(row["tags"]) if row["tags"] else [],
        "summary": row["ai_summary"] or row["summary"],
        "hasAiSummary": bool(row["ai_summary"]),
    }


def _safe_json_embed(payload: Any) -> str:
    """Serialize to JSON and neutralize sequences that could break out of a <script> block."""
    raw = json.dumps(payload)
    return raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render_dashboard(commits: list[Any], output_path: Path) -> Path:
    records = [_commit_to_dict(c) for c in commits]
    repos = sorted({r["repo"] for r in records})
    all_tags = sorted({tag for r in records for tag in r["tags"]})

    data_json = _safe_json_embed(records)
    repos_json = _safe_json_embed(repos)
    tags_json = _safe_json_embed(all_tags)

    generated_count = len(records)

    html_doc = f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Waymark — Project Decision Memory</title>
<style>
:root {{
  --bg: #0f1216;
  --bg-elevated: #171b21;
  --border: #262c35;
  --text: #e6e9ef;
  --text-dim: #9aa4b2;
  --accent: #5eb0ff;
  --accent-dim: #2c6a9e;
  --score-high: #ff8a5b;
  --score-mid: #e8c468;
  --score-low: #6b7484;
  --radius: 8px;
  --space: 1rem;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
}}
header {{
  padding: var(--space) 1.5rem;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  background: var(--bg);
  z-index: 10;
}}
header h1 {{
  margin: 0 0 0.25rem 0;
  font-size: 1.4rem;
}}
header p {{
  margin: 0;
  color: var(--text-dim);
  font-size: 0.9rem;
}}
main {{
  max-width: 1000px;
  margin: 0 auto;
  padding: var(--space) 1rem 3rem;
}}
.controls {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-bottom: var(--space);
}}
.controls input[type="search"],
.controls select {{
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 0.5rem 0.7rem;
  border-radius: var(--radius);
  font-size: 0.95rem;
}}
.controls input[type="search"] {{
  flex: 1 1 220px;
}}
.controls label {{
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--text-dim);
  font-size: 0.85rem;
}}
#count {{
  color: var(--text-dim);
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
}}
ul#timeline {{
  list-style: none;
  margin: 0;
  padding: 0;
}}
.commit {{
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.9rem 1rem;
  margin-bottom: 0.6rem;
  cursor: pointer;
}}
.commit-head {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.6rem;
}}
.commit-summary {{
  font-size: 0.98rem;
  flex: 1;
}}
.score {{
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  border-radius: 4px;
  padding: 0.1rem 0.5rem;
  font-size: 0.8rem;
  white-space: nowrap;
}}
.score-high {{ background: color-mix(in srgb, var(--score-high) 25%, transparent); color: var(--score-high); }}
.score-mid {{ background: color-mix(in srgb, var(--score-mid) 25%, transparent); color: var(--score-mid); }}
.score-low {{ background: color-mix(in srgb, var(--score-low) 25%, transparent); color: var(--score-low); }}
.commit-meta {{
  margin-top: 0.35rem;
  font-size: 0.8rem;
  color: var(--text-dim);
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}}
.tag {{
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.05rem 0.4rem;
}}
.commit-detail {{
  display: none;
  margin-top: 0.7rem;
  padding-top: 0.7rem;
  border-top: 1px solid var(--border);
  font-size: 0.88rem;
  color: var(--text-dim);
  white-space: pre-wrap;
}}
.commit.expanded .commit-detail {{ display: block; }}
.empty {{
  color: var(--text-dim);
  text-align: center;
  padding: 2rem;
}}
@media (max-width: 600px) {{
  .controls {{ flex-direction: column; }}
  .controls input[type="search"], .controls select {{ width: 100%; }}
}}
</style>
</head>
<body>
<header>
  <h1>Waymark</h1>
  <p>{generated_count} indexed commits across {len(repos)} repo{'s' if len(repos) != 1 else ''} — project decision memory</p>
</header>
<main>
  <div class="controls">
    <input type="search" id="search" placeholder="Search summaries, messages, tags..." aria-label="Search commits">
    <select id="repoFilter" aria-label="Filter by repo">
      <option value="">All repos</option>
    </select>
    <select id="tagFilter" aria-label="Filter by tag">
      <option value="">All tags</option>
    </select>
    <label>Min score
      <select id="minScore" aria-label="Minimum decision score">
        <option value="0">0</option>
        <option value="3">3</option>
        <option value="5" selected>5</option>
        <option value="7">7</option>
      </select>
    </label>
  </div>
  <div id="count"></div>
  <ul id="timeline"></ul>
</main>
<script id="waymark-data" type="application/json">{data_json}</script>
<script>
(function () {{
  "use strict";
  var COMMITS = JSON.parse(document.getElementById("waymark-data").textContent);
  var REPOS = {repos_json};
  var TAGS = {tags_json};

  var repoSelect = document.getElementById("repoFilter");
  REPOS.forEach(function (r) {{
    var opt = document.createElement("option");
    opt.value = r;
    opt.textContent = r;
    repoSelect.appendChild(opt);
  }});

  var tagSelect = document.getElementById("tagFilter");
  TAGS.forEach(function (t) {{
    var opt = document.createElement("option");
    opt.value = t;
    opt.textContent = t;
    tagSelect.appendChild(opt);
  }});

  function scoreClass(score) {{
    if (score >= 7) return "score-high";
    if (score >= 4) return "score-mid";
    return "score-low";
  }}

  function render() {{
    var query = document.getElementById("search").value.trim().toLowerCase();
    var repo = repoSelect.value;
    var tag = tagSelect.value;
    var minScore = parseInt(document.getElementById("minScore").value, 10);

    var filtered = COMMITS.filter(function (c) {{
      if (repo && c.repo !== repo) return false;
      if (tag && c.tags.indexOf(tag) === -1) return false;
      if (c.score < minScore) return false;
      if (query) {{
        var haystack = (c.summary + " " + c.subject + " " + c.body + " " + c.tags.join(" ")).toLowerCase();
        if (haystack.indexOf(query) === -1) return false;
      }}
      return true;
    }});

    var countEl = document.getElementById("count");
    countEl.textContent = filtered.length + " of " + COMMITS.length + " commits";

    var list = document.getElementById("timeline");
    list.innerHTML = "";

    if (filtered.length === 0) {{
      var empty = document.createElement("li");
      empty.className = "empty";
      empty.textContent = "No commits match the current filters.";
      list.appendChild(empty);
      return;
    }}

    filtered.forEach(function (c) {{
      var li = document.createElement("li");
      li.className = "commit";

      var head = document.createElement("div");
      head.className = "commit-head";

      var summary = document.createElement("div");
      summary.className = "commit-summary";
      summary.textContent = c.summary;
      head.appendChild(summary);

      var score = document.createElement("span");
      score.className = "score " + scoreClass(c.score);
      score.textContent = c.score;
      head.appendChild(score);

      li.appendChild(head);

      var meta = document.createElement("div");
      meta.className = "commit-meta";
      var metaBits = [c.repo, c.shortHash, c.date ? c.date.slice(0, 10) : "", c.author || ""];
      metaBits.filter(Boolean).forEach(function (bit) {{
        var span = document.createElement("span");
        span.textContent = bit;
        meta.appendChild(span);
      }});
      c.tags.forEach(function (t) {{
        var tagEl = document.createElement("span");
        tagEl.className = "tag";
        tagEl.textContent = t;
        meta.appendChild(tagEl);
      }});
      li.appendChild(meta);

      var detail = document.createElement("div");
      detail.className = "commit-detail";
      detail.textContent = c.subject + (c.body ? "\\n\\n" + c.body : "") +
        "\\n\\n+" + c.insertions + "/-" + c.deletions + " across " + c.filesChanged + " file(s)" +
        (c.hasAiSummary ? "\\n\\n(AI-enriched summary)" : "");
      li.appendChild(detail);

      li.addEventListener("click", function () {{
        li.classList.toggle("expanded");
      }});

      list.appendChild(li);
    }});
  }}

  document.getElementById("search").addEventListener("input", render);
  repoSelect.addEventListener("change", render);
  tagSelect.addEventListener("change", render);
  document.getElementById("minScore").addEventListener("change", render);

  render();
}})();
</script>
</body>
</html>
"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_doc, encoding="utf-8")
    return output_path
