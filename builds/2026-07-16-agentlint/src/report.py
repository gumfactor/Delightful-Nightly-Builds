"""Report building and rendering (text / JSON / HTML) for AgentLint."""

from __future__ import annotations

import html
import json

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
SEVERITY_COLORS = {"error": "#ef4444", "warning": "#f59e0b", "info": "#38bdf8"}


def summarize(findings) -> dict:
    counts = {"error": 0, "warning": 0, "info": 0}
    for finding in findings:
        counts[finding["severity"]] = counts.get(finding["severity"], 0) + 1
    return counts


def build_report(findings, target: str) -> dict:
    sorted_findings = sorted(
        findings, key=lambda f: (SEVERITY_ORDER.get(f["severity"], 99), f.get("line") or 0)
    )
    return {
        "target": target,
        "summary": summarize(sorted_findings),
        "findings": sorted_findings,
    }


def render_json(report: dict) -> str:
    return json.dumps(report, indent=2)


def render_text(report: dict) -> str:
    lines = [f"AgentLint report — {report['target']}", ""]
    summary = report["summary"]
    lines.append(
        f"Summary: {summary['error']} error(s), {summary['warning']} warning(s), "
        f"{summary['info']} info"
    )
    lines.append("")

    if not report["findings"]:
        lines.append("No issues found.")
        return "\n".join(lines)

    for finding in report["findings"]:
        location = f"line {finding['line']}" if finding.get("line") else "no specific line"
        lines.append(f"[{finding['severity'].upper()}] ({finding['check']}, {location})")
        lines.append(f"  {finding['message']}")
        if finding.get("excerpt"):
            lines.append(f"  > {finding['excerpt']}")
        lines.append("")
    return "\n".join(lines)


def render_html(report: dict) -> str:
    summary = report["summary"]
    target = html.escape(report["target"])

    rows = []
    for finding in report["findings"]:
        severity = finding["severity"]
        color = SEVERITY_COLORS.get(severity, "#94a3b8")
        location = f"line {finding['line']}" if finding.get("line") else "—"
        excerpt_html = (
            f'<div class="excerpt">{html.escape(finding.get("excerpt", ""))}</div>'
            if finding.get("excerpt") else ""
        )
        rows.append(f"""
        <div class="finding" style="border-left-color: {color}">
          <div class="finding-head">
            <span class="badge" style="background: {color}">{html.escape(severity.upper())}</span>
            <span class="check">{html.escape(finding['check'])}</span>
            <span class="location">{html.escape(location)}</span>
          </div>
          <div class="message">{html.escape(finding['message'])}</div>
          {excerpt_html}
        </div>""")

    findings_html = "\n".join(rows) if rows else '<p class="empty">No issues found.</p>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AgentLint report — {target}</title>
<style>
  :root {{
    --bg: #0f172a; --panel: #1e293b; --text: #e2e8f0; --muted: #94a3b8;
    --border: #334155;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 24px; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
  }}
  .container {{ max-width: 860px; margin: 0 auto; }}
  h1 {{ font-size: 1.3rem; word-break: break-all; }}
  .summary {{
    display: flex; gap: 12px; flex-wrap: wrap; margin: 16px 0 24px;
  }}
  .stat {{
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 8px; padding: 10px 16px; min-width: 90px; text-align: center;
  }}
  .stat .n {{ font-size: 1.4rem; font-weight: 700; display: block; }}
  .stat .label {{ color: var(--muted); font-size: 0.8rem; }}
  .finding {{
    background: var(--panel); border: 1px solid var(--border); border-left-width: 4px;
    border-radius: 6px; padding: 12px 16px; margin-bottom: 10px;
  }}
  .finding-head {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
  .badge {{
    color: #0f172a; font-weight: 700; font-size: 0.7rem; padding: 2px 8px;
    border-radius: 999px; letter-spacing: 0.03em;
  }}
  .check {{ color: var(--muted); font-size: 0.85rem; font-family: monospace; }}
  .location {{ color: var(--muted); font-size: 0.85rem; margin-left: auto; }}
  .message {{ margin-top: 8px; }}
  .excerpt {{
    margin-top: 8px; padding: 8px 10px; background: #0b1222; border-radius: 4px;
    font-family: monospace; font-size: 0.85rem; color: var(--muted);
    overflow-x: auto; white-space: pre-wrap; word-break: break-word;
  }}
  .empty {{ color: var(--muted); }}
  @media (prefers-color-scheme: light) {{
    :root {{ --bg: #f8fafc; --panel: #ffffff; --text: #0f172a; --muted: #64748b; --border: #e2e8f0; }}
    .badge {{ color: #ffffff; }}
    .excerpt {{ background: #f1f5f9; }}
  }}
</style>
</head>
<body>
  <div class="container">
    <h1>AgentLint report</h1>
    <p class="location">{target}</p>
    <div class="summary">
      <div class="stat"><span class="n">{summary['error']}</span><span class="label">errors</span></div>
      <div class="stat"><span class="n">{summary['warning']}</span><span class="label">warnings</span></div>
      <div class="stat"><span class="n">{summary['info']}</span><span class="label">info</span></div>
    </div>
    {findings_html}
  </div>
</body>
</html>
"""
