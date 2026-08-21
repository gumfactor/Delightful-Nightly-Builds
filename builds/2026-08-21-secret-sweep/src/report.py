"""Terminal, JSON, and self-contained HTML report renderers.

The HTML renderer never uses innerHTML on scanned-repo content: the finding
list is embedded as a JSON payload inside a <script type="application/json">
tag and read back via .textContent, then every visible node is built with
createElement/textContent so a malicious file path, commit message, or
masked context can never execute as markup.
"""

from __future__ import annotations

import json
import sqlite3

ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_DIM = "\033[2m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


def row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def remediation_snippet(finding: dict) -> str:
    file_path = finding["file_path"]
    if finding["severity"] == "critical":
        return (
            f"git rm --cached '{file_path}'\n"
            f"echo '{file_path}' >> .gitignore\n"
            "# Then rotate/revoke this credential with its provider immediately."
        )
    return (
        f"git filter-repo --path '{file_path}' --invert-paths\n"
        "# Rewrites history — force-push and have every collaborator re-clone.\n"
        "# History rewriting does not undo exposure: treat this credential as\n"
        "# compromised and rotate it, since anyone who already cloned still has it."
    )


def render_terminal(findings: list[dict]) -> str:
    if not findings:
        return "No findings. Nothing looks like a committed secret in the scanned repo(s)."

    lines = []
    critical = [f for f in findings if f["severity"] == "critical" and f["status"] != "acknowledged"]
    high = [f for f in findings if f["severity"] == "high" and f["status"] != "acknowledged"]
    acknowledged = [f for f in findings if f["status"] == "acknowledged"]

    lines.append(f"{ANSI_BOLD}Secret Sweep report{ANSI_RESET}")
    lines.append(
        f"{len(critical)} critical, {len(high)} high, {len(acknowledged)} acknowledged "
        f"({len(findings)} total)"
    )
    lines.append("")

    for label, color, group in (
        ("CRITICAL (live now — rotate immediately)", ANSI_RED, critical),
        ("HIGH (history only — still exposed to anyone with a clone)", ANSI_YELLOW, high),
    ):
        if not group:
            continue
        lines.append(f"{color}{ANSI_BOLD}{label}{ANSI_RESET}")
        for f in group:
            location = f["file_path"]
            if f["line_number"]:
                location += f":{f['line_number']}"
            if f["commit_sha"]:
                location += f" ({f['commit_sha'][:8]})"
            lines.append(
                f"  {color}[{f['id']}]{ANSI_RESET} {f['repo_name']}/{location} — "
                f"{f['pattern_name']} — {f['masked_preview']}"
            )
            if f.get("ai_verdict"):
                lines.append(f"      {ANSI_DIM}AI review: {f['ai_verdict']} — {f['ai_rationale']}{ANSI_RESET}")
        lines.append("")

    if acknowledged:
        lines.append(f"{ANSI_DIM}Acknowledged ({len(acknowledged)}) — suppressed from new-finding counts:{ANSI_RESET}")
        for f in acknowledged:
            lines.append(f"  {ANSI_DIM}[{f['id']}] {f['repo_name']}/{f['file_path']} — {f['pattern_name']}{ANSI_RESET}")

    return "\n".join(lines)


def render_json(findings: list[dict]) -> str:
    return json.dumps(findings, indent=2, sort_keys=True)


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<title>Secret Sweep Report</title>
<style>
  :root {
    --bg: #0f1117; --panel: #161923; --border: #262b3a; --text: #e6e8ee;
    --dim: #8b92a8; --critical: #ff5c72; --high: #f5b942; --ok: #4ade80;
    --mono: 'SF Mono', Consolas, monospace;
  }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--text); font-family: -apple-system, Segoe UI, sans-serif;
         margin: 0; padding: 24px; }
  h1 { font-size: 1.4rem; margin-bottom: 4px; }
  .subtitle { color: var(--dim); margin-bottom: 20px; font-size: 0.9rem; }
  .stats { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
  .stat { background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
          padding: 10px 16px; min-width: 100px; }
  .stat .num { font-size: 1.6rem; font-weight: 700; }
  .stat .label { color: var(--dim); font-size: 0.75rem; text-transform: uppercase; }
  .controls { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
  input, select { background: var(--panel); border: 1px solid var(--border); color: var(--text);
                  padding: 8px 10px; border-radius: 6px; font-size: 0.9rem; }
  input { flex: 1; min-width: 200px; }
  .repo-panel { background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
                margin-bottom: 16px; overflow: hidden; }
  .repo-header { padding: 12px 16px; border-bottom: 1px solid var(--border); font-weight: 600; }
  .finding { padding: 12px 16px; border-bottom: 1px solid var(--border); }
  .finding:last-child { border-bottom: none; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 100px; font-size: 0.7rem;
           font-weight: 700; text-transform: uppercase; margin-right: 8px; }
  .badge.critical { background: rgba(255,92,114,0.15); color: var(--critical); }
  .badge.high { background: rgba(245,185,66,0.15); color: var(--high); }
  .badge.acknowledged { background: rgba(139,146,168,0.15); color: var(--dim); }
  .location { font-family: var(--mono); font-size: 0.85rem; color: var(--dim); margin-top: 4px; }
  .preview { font-family: var(--mono); background: #0a0c12; padding: 2px 6px; border-radius: 4px; }
  .ai-note { color: var(--dim); font-size: 0.82rem; margin-top: 6px; font-style: italic; }
  pre.remediation { background: #0a0c12; border: 1px solid var(--border); border-radius: 6px;
                     padding: 10px; margin-top: 8px; font-size: 0.8rem; overflow-x: auto; white-space: pre-wrap; }
  .copy-btn { background: var(--border); color: var(--text); border: none; border-radius: 4px;
              padding: 4px 10px; font-size: 0.75rem; cursor: pointer; margin-top: 6px; }
  .empty { color: var(--dim); padding: 40px; text-align: center; }
</style>
</head>
<body>
<h1>Secret Sweep Report</h1>
<div class="subtitle" id="generated-at"></div>
<div class="stats" id="stats"></div>
<div class="controls">
  <input id="search" type="text" placeholder="Search file, repo, pattern...">
  <select id="severity-filter">
    <option value="all">All severities</option>
    <option value="critical">Critical only</option>
    <option value="high">High only</option>
  </select>
  <select id="status-filter">
    <option value="active">New + Acknowledged</option>
    <option value="new">New only</option>
    <option value="acknowledged">Acknowledged only</option>
  </select>
</div>
<div id="panels"></div>
<script type="application/json" id="findings-data">__FINDINGS_JSON__</script>
<script type="application/json" id="meta-data">__META_JSON__</script>
<script>
(function () {
  var findings = JSON.parse(document.getElementById('findings-data').textContent);
  var meta = JSON.parse(document.getElementById('meta-data').textContent);
  document.getElementById('generated-at').textContent = 'Generated ' + meta.generated_at;

  function statTile(num, label) {
    var d = document.createElement('div');
    d.className = 'stat';
    var n = document.createElement('div'); n.className = 'num'; n.textContent = String(num);
    var l = document.createElement('div'); l.className = 'label'; l.textContent = label;
    d.appendChild(n); d.appendChild(l);
    return d;
  }

  function renderStats(list) {
    var statsEl = document.getElementById('stats');
    while (statsEl.firstChild) statsEl.removeChild(statsEl.firstChild);
    var crit = list.filter(function (f) { return f.severity === 'critical' && f.status !== 'acknowledged'; }).length;
    var high = list.filter(function (f) { return f.severity === 'high' && f.status !== 'acknowledged'; }).length;
    var ack = list.filter(function (f) { return f.status === 'acknowledged'; }).length;
    statsEl.appendChild(statTile(crit, 'Critical'));
    statsEl.appendChild(statTile(high, 'High'));
    statsEl.appendChild(statTile(ack, 'Acknowledged'));
    statsEl.appendChild(statTile(list.length, 'Total'));
  }

  function buildFindingNode(f) {
    var el = document.createElement('div');
    el.className = 'finding';

    var badge = document.createElement('span');
    badge.className = 'badge ' + (f.status === 'acknowledged' ? 'acknowledged' : f.severity);
    badge.textContent = f.status === 'acknowledged' ? 'acknowledged' : f.severity;
    el.appendChild(badge);

    var patternSpan = document.createElement('strong');
    patternSpan.textContent = f.pattern_name;
    el.appendChild(patternSpan);

    var previewSpan = document.createElement('span');
    previewSpan.className = 'preview';
    previewSpan.style.marginLeft = '8px';
    previewSpan.textContent = f.masked_preview;
    el.appendChild(previewSpan);

    var loc = document.createElement('div');
    loc.className = 'location';
    var locText = f.file_path;
    if (f.line_number) locText += ':' + f.line_number;
    if (f.commit_sha) locText += ' (' + f.commit_sha.slice(0, 8) + ')';
    loc.textContent = locText;
    el.appendChild(loc);

    if (f.ai_verdict) {
      var ai = document.createElement('div');
      ai.className = 'ai-note';
      ai.textContent = 'AI review: ' + f.ai_verdict + ' — ' + f.ai_rationale;
      el.appendChild(ai);
    }

    if (f.status !== 'acknowledged') {
      var pre = document.createElement('pre');
      pre.className = 'remediation';
      pre.textContent = f.remediation;
      el.appendChild(pre);

      var btn = document.createElement('button');
      btn.className = 'copy-btn';
      btn.textContent = 'Copy remediation';
      btn.addEventListener('click', function () {
        if (navigator.clipboard) { navigator.clipboard.writeText(f.remediation); }
        btn.textContent = 'Copied!';
        setTimeout(function () { btn.textContent = 'Copy remediation'; }, 1500);
      });
      el.appendChild(btn);
    }

    return el;
  }

  function render() {
    var query = document.getElementById('search').value.toLowerCase();
    var sevFilter = document.getElementById('severity-filter').value;
    var statusFilter = document.getElementById('status-filter').value;

    var filtered = findings.filter(function (f) {
      if (sevFilter !== 'all' && f.severity !== sevFilter) return false;
      if (statusFilter === 'new' && f.status !== 'new') return false;
      if (statusFilter === 'acknowledged' && f.status !== 'acknowledged') return false;
      if (query) {
        var haystack = (f.repo_name + ' ' + f.file_path + ' ' + f.pattern_name).toLowerCase();
        if (haystack.indexOf(query) === -1) return false;
      }
      return true;
    });

    renderStats(findings);

    var panelsEl = document.getElementById('panels');
    while (panelsEl.firstChild) panelsEl.removeChild(panelsEl.firstChild);

    if (filtered.length === 0) {
      var empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = 'No findings match the current filters.';
      panelsEl.appendChild(empty);
      return;
    }

    var byRepo = {};
    filtered.forEach(function (f) {
      (byRepo[f.repo_name] = byRepo[f.repo_name] || []).push(f);
    });

    Object.keys(byRepo).sort().forEach(function (repoName) {
      var panel = document.createElement('div');
      panel.className = 'repo-panel';
      var header = document.createElement('div');
      header.className = 'repo-header';
      header.textContent = repoName + ' (' + byRepo[repoName].length + ')';
      panel.appendChild(header);
      byRepo[repoName].forEach(function (f) { panel.appendChild(buildFindingNode(f)); });
      panelsEl.appendChild(panel);
    });
  }

  document.getElementById('search').addEventListener('input', render);
  document.getElementById('severity-filter').addEventListener('change', render);
  document.getElementById('status-filter').addEventListener('change', render);
  render();
})();
</script>
</body>
</html>
"""


def _json_for_script_tag(value) -> str:
    """json.dumps, with '<' escaped so a value like '</script>' can never terminate
    the enclosing <script> element early — <script> content is HTML raw text and is
    never HTML-entity-decoded, so this must be done at the JSON-string level."""
    return json.dumps(value).replace("<", "\\u003c")


def render_html(findings: list[dict], generated_at: str) -> str:
    enriched = []
    for f in findings:
        f = dict(f)
        f["remediation"] = remediation_snippet(f)
        enriched.append(f)
    findings_json = _json_for_script_tag(enriched)
    meta_json = _json_for_script_tag({"generated_at": generated_at})
    return (
        _HTML_TEMPLATE
        .replace("__FINDINGS_JSON__", findings_json)
        .replace("__META_JSON__", meta_json)
    )
