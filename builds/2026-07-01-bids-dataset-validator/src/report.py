"""Text, JSON, and HTML report rendering for a ScanResult."""

from __future__ import annotations

import html
import json

from .scanner import ScanResult


def build_report_dict(result: ScanResult, ai_summary: str | None = None) -> dict:
    errors = [f for f in result.findings if f.severity == "error"]
    warnings = [f for f in result.findings if f.severity == "warning"]
    return {
        "dataset_path": str(result.root),
        "files_scanned": len(result.files),
        "subjects": sorted(result.subjects),
        "findings": [f.to_dict() for f in result.findings],
        "summary": {"errors": len(errors), "warnings": len(warnings)},
        "ai_summary": ai_summary,
    }


def render_text(report: dict) -> str:
    lines = [
        "BIDS Dataset Validation Report",
        f"Dataset: {report['dataset_path']}",
        f"Files scanned: {report['files_scanned']}",
        f"Subjects: {len(report['subjects'])}",
        f"Errors: {report['summary']['errors']}  Warnings: {report['summary']['warnings']}",
        "",
    ]
    if not report["findings"]:
        lines.append("No violations found.")
    else:
        for finding in report["findings"]:
            location = f" ({finding['path']})" if finding["path"] else ""
            lines.append(
                f"[{finding['severity'].upper()}] {finding['code']}: "
                f"{finding['message']}{location}"
            )
    if report.get("ai_summary"):
        lines.append("")
        lines.append("AI Summary")
        lines.append(report["ai_summary"])
    return "\n".join(lines)


def render_json(report: dict) -> str:
    return json.dumps(report, indent=2)


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BIDS Validation Report</title>
<style>
  :root {{
    --bg: #12141a;
    --panel: #1b1f29;
    --text: #e6e8ec;
    --muted: #8b93a7;
    --error: #ef5350;
    --warning: #f4b942;
    --ok: #4caf7d;
    --border: #2a2f3b;
  }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    margin: 0;
    padding: 1.5rem;
  }}
  .panel {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
  }}
  h1 {{ font-size: 1.4rem; margin: 0 0 0.5rem; }}
  .stats {{ display: flex; gap: 1.5rem; flex-wrap: wrap; color: var(--muted); }}
  .stat-value {{ color: var(--text); font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{
    text-align: left;
    padding: 0.5rem;
    border-bottom: 1px solid var(--border);
    font-size: 0.9rem;
    word-break: break-word;
  }}
  .sev-error {{ color: var(--error); font-weight: 600; }}
  .sev-warning {{ color: var(--warning); font-weight: 600; }}
  .ok {{ color: var(--ok); }}
  @media (max-width: 600px) {{
    body {{ padding: 0.75rem; }}
    .stats {{ gap: 0.75rem; }}
  }}
</style>
</head>
<body>
  <div class="panel">
    <h1>BIDS Dataset Validation Report</h1>
    <div class="stats">
      <div>Dataset: <span class="stat-value">{dataset_path}</span></div>
      <div>Files scanned: <span class="stat-value">{files_scanned}</span></div>
      <div>Subjects: <span class="stat-value">{subject_count}</span></div>
      <div>Errors: <span class="stat-value">{errors}</span></div>
      <div>Warnings: <span class="stat-value">{warnings}</span></div>
    </div>
  </div>
  <div class="panel">
    {findings_html}
  </div>
  {ai_summary_html}
</body>
</html>
"""


def render_html(report: dict) -> str:
    if not report["findings"]:
        findings_html = '<p class="ok">No violations found.</p>'
    else:
        rows = []
        for finding in report["findings"]:
            sev_class = "sev-error" if finding["severity"] == "error" else "sev-warning"
            path = html.escape(finding["path"] or "")
            message = html.escape(finding["message"])
            code = html.escape(finding["code"])
            rows.append(
                f"<tr><td class='{sev_class}'>{finding['severity'].upper()}</td>"
                f"<td>{code}</td><td>{message}</td><td>{path}</td></tr>"
            )
        findings_html = (
            "<table><thead><tr><th>Severity</th><th>Code</th>"
            "<th>Message</th><th>Path</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )

    ai_summary_html = ""
    if report.get("ai_summary"):
        ai_summary_html = (
            "<div class='panel'><h2>AI Summary</h2><p>"
            f"{html.escape(report['ai_summary']).replace(chr(10), '<br>')}</p></div>"
        )

    return _HTML_TEMPLATE.format(
        dataset_path=html.escape(report["dataset_path"]),
        files_scanned=report["files_scanned"],
        subject_count=len(report["subjects"]),
        errors=report["summary"]["errors"],
        warnings=report["summary"]["warnings"],
        findings_html=findings_html,
        ai_summary_html=ai_summary_html,
    )
