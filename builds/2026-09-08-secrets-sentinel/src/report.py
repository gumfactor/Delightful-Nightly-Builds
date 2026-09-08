"""Terminal, JSON, and HTML rendering of scan findings."""

from __future__ import annotations

import json
from dataclasses import asdict
from html import escape
from pathlib import Path

from src.classifier import Finding

_TIER_ORDER = {"high": 0, "medium": 1, "low": 2}

_REMEDIATION_BY_HEAD_STATE = {
    True: "Still present in HEAD: rotate the credential immediately, then remove it from the current file.",
    False: "Removed from HEAD but still recoverable from git history: rotate the credential, then purge it "
    "from history (e.g. git filter-repo) — deleting the file alone is not enough.",
}


def _sorted(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda f: (_TIER_ORDER.get(f.tier, 99), f.repo, f.file, f.line))


def tier_counts(findings: list[Finding]) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for finding in findings:
        counts[finding.tier] = counts.get(finding.tier, 0) + 1
    return counts


def render_terminal(findings: list[Finding]) -> str:
    counts = tier_counts(findings)
    lines = [
        "Secrets Sentinel — scan summary",
        f"  high: {counts['high']}   medium: {counts['medium']}   low: {counts['low']}",
        "",
    ]
    for finding in _sorted(findings):
        head_flag = "STILL IN HEAD" if finding.still_in_head else "history only"
        ai = f" ai={finding.ai_verdict}" if finding.ai_verdict else ""
        lines.append(
            f"[{finding.tier.upper():6}] {finding.repo}:{finding.file}:{finding.line} "
            f"({finding.pattern_name}) [{head_flag}]{ai} commit={finding.commit[:8]}"
        )
    if not findings:
        lines.append("No findings.")
    return "\n".join(lines)


def render_json(findings: list[Finding], out_path: Path) -> None:
    payload = [asdict(finding) for finding in _sorted(findings)]
    Path(out_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def render_html(findings: list[Finding], out_path: Path) -> None:
    counts = tier_counts(findings)
    rows = []
    for finding in _sorted(findings):
        head_badge = (
            '<span class="badge badge-live">still in HEAD</span>'
            if finding.still_in_head
            else '<span class="badge badge-history">history only</span>'
        )
        ai_cell = escape(finding.ai_verdict) if finding.ai_verdict else "—"
        remediation = escape(_REMEDIATION_BY_HEAD_STATE[finding.still_in_head])
        rows.append(
            f"""<tr class="tier-{escape(finding.tier)}">
  <td>{escape(finding.repo)}</td>
  <td>{escape(finding.file)}:{finding.line}</td>
  <td>{escape(finding.pattern_name)}</td>
  <td>{escape(finding.tier)}</td>
  <td>{head_badge}</td>
  <td>{ai_cell}</td>
  <td><code>{escape(finding.redacted_snippet)}</code></td>
  <td>{finding.commit[:8]}</td>
  <td class="remediation">{remediation}</td>
</tr>"""
        )

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Secrets Sentinel Report</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ background: #0f1115; color: #e6e6e6; font-family: -apple-system, sans-serif; margin: 0; padding: 2rem; }}
  h1 {{ font-size: 1.4rem; }}
  .summary {{ display: flex; gap: 1rem; margin-bottom: 1.5rem; }}
  .stat {{ background: #1b1e27; padding: 0.75rem 1.25rem; border-radius: 8px; }}
  .stat .n {{ font-size: 1.5rem; font-weight: 700; display: block; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th, td {{ text-align: left; padding: 0.5rem 0.6rem; border-bottom: 1px solid #2a2e3a; vertical-align: top; }}
  th {{ color: #9aa4b2; font-weight: 600; }}
  tr.tier-high {{ background: rgba(220, 80, 80, 0.08); }}
  tr.tier-medium {{ background: rgba(220, 180, 60, 0.06); }}
  code {{ color: #9ecbff; word-break: break-all; }}
  .badge {{ padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; }}
  .badge-live {{ background: #4a1414; color: #ff9b9b; }}
  .badge-history {{ background: #2a2e3a; color: #9aa4b2; }}
  .remediation {{ max-width: 22ch; color: #c7ccd6; }}
</style>
</head>
<body>
<h1>Secrets Sentinel Report</h1>
<div class="summary">
  <div class="stat"><span class="n">{counts['high']}</span>high confidence</div>
  <div class="stat"><span class="n">{counts['medium']}</span>medium confidence</div>
  <div class="stat"><span class="n">{counts['low']}</span>low confidence</div>
</div>
<table>
<thead><tr>
  <th>Repo</th><th>File:Line</th><th>Pattern</th><th>Tier</th><th>Status</th>
  <th>AI verdict</th><th>Redacted context</th><th>Commit</th><th>Remediation</th>
</tr></thead>
<tbody>
{''.join(rows) if rows else '<tr><td colspan="9">No findings.</td></tr>'}
</tbody>
</table>
</body>
</html>
"""
    Path(out_path).write_text(html_doc, encoding="utf-8")
