"""Report renderer — produces dated markdown and self-contained HTML output."""
from __future__ import annotations

import html
import json
from typing import Any


def _esc(text: Any) -> str:
    return html.escape(str(text), quote=True)


def _safe_json(obj: Any) -> str:
    """JSON-serialize with HTML-safe Unicode escapes to prevent script-tag injection."""
    return (
        json.dumps(obj)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def render_markdown(
    report_date: str,
    github_data: dict,
    portfolio_data: dict,
    weather_data: dict,
    ai_summary: str,
) -> str:
    lines = [f"# Morning Briefing — {report_date}", ""]

    if ai_summary:
        lines += ["## Today's Priorities", ai_summary, ""]

    # GitHub
    lines.append("## GitHub Activity")
    recent = github_data.get("recent_repos", [])
    stale = github_data.get("stale_repos", [])
    prs = github_data.get("open_prs", [])
    if github_data.get("error"):
        lines.append(f"⚠ {github_data['error']}")
    else:
        lines.append(f"- **{len(recent)}** repos had recent pushes (last 24h)")
        lines.append(f"- **{len(stale)}** repos are stale (7+ days without a push)")
        lines.append(f"- **{len(prs)}** open PRs across active repos")
        for repo in recent[:5]:
            date_str = repo.get("pushed_at", "")[:10]
            issues = repo.get("open_issues", 0)
            lines.append(f"  - `{repo['name']}` — pushed {date_str}, {issues} open issues")
    lines.append("")

    # Portfolio
    lines.append("## Portfolio Pulse")
    tickers = portfolio_data.get("tickers", [])
    if not tickers:
        lines.append("_No portfolio data available_")
    else:
        up = portfolio_data.get("total_up", 0)
        flat = portfolio_data.get("total_flat", 0)
        down = portfolio_data.get("total_down", 0)
        lines.append(f"↑ {up} / → {flat} / ↓ {down}")
        lines.append("")
        lines.append("| Ticker | Price | Change |")
        lines.append("|--------|-------|--------|")
        for t in tickers:
            emoji = "🟢" if t["move"] == "up" else ("🔴" if t["move"] == "down" else "⚪")
            lines.append(f"| {t['ticker']} | {t['formatted_price']} | {emoji} {t['formatted_change']} |")
    lines.append("")

    # Weather
    lines.append("## Weather Windows (Toronto)")
    if weather_data.get("error"):
        lines.append(f"⚠ {weather_data['error']}")
    elif not weather_data.get("hours"):
        lines.append("_No weather data available_")
    else:
        for activity, label in (("run", "🏃 Running"), ("golf", "⛳ Golf"), ("boat", "⛵ Boating")):
            windows = weather_data.get(f"best_{activity}", [])
            if windows:
                best = windows[0]
                score = best["scores"][activity]
                lines.append(
                    f"**{label}:** {best['time'][-5:]} — "
                    f"{best['temp_c']}°C, {best['wind_kph']} km/h, "
                    f"{best['precip_prob']}% rain (score {score}/100)"
                )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

_CSS = """\
:root {
  --bg: #0f172a;
  --surface: #1e293b;
  --border: #334155;
  --text: #e2e8f0;
  --muted: #94a3b8;
  --green: #22c55e;
  --red: #ef4444;
  --blue: #3b82f6;
  --yellow: #f59e0b;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; padding: 1.5rem; }
h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
.subtitle { color: var(--muted); font-size: 0.875rem; margin-bottom: 1.5rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 1rem; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }
.card h2 { font-size: 1rem; margin-bottom: 0.75rem; }
.ai-card { border-color: var(--blue); margin-bottom: 1rem; }
.ai-text { color: var(--text); line-height: 1.7; font-size: 0.9rem; white-space: pre-wrap; }
table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
th { color: var(--muted); font-weight: 600; text-align: left; padding: 0.4rem 0.5rem; border-bottom: 1px solid var(--border); }
td { padding: 0.35rem 0.5rem; border-bottom: 1px solid var(--border); word-break: break-word; }
tr:last-child td { border-bottom: none; }
.badge { padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.health-active { background: rgba(34,197,94,0.2); color: var(--green); }
.health-recent { background: rgba(59,130,246,0.2); color: var(--blue); }
.health-stale  { background: rgba(239,68,68,0.2); color: var(--red); }
.health-unknown{ background: rgba(148,163,184,0.2); color: var(--muted); }
.text-green { color: var(--green); font-weight: 600; }
.text-red   { color: var(--red); font-weight: 600; }
.text-gray  { color: var(--muted); }
.score-high { color: var(--green); font-weight: 600; }
.score-mid  { color: var(--yellow); }
.score-low  { color: var(--muted); }
.stat-row { display: flex; gap: 1.5rem; margin-bottom: 0.75rem; }
.stat { font-size: 1.25rem; font-weight: 700; }
.stat-label { font-size: 0.75rem; color: var(--muted); }
.chart-wrap { height: 160px; margin-bottom: 0.75rem; }
.error { color: var(--red); font-size: 0.875rem; }
.empty-msg { color: var(--muted); font-size: 0.875rem; }
@media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
"""


def render_html(
    report_date: str,
    github_data: dict,
    portfolio_data: dict,
    weather_data: dict,
    ai_summary: str,
) -> str:
    tickers = portfolio_data.get("tickers", [])
    chart_labels = _safe_json([t["ticker"] for t in tickers])
    chart_values = _safe_json([t["change_pct"] for t in tickers])
    chart_colors = _safe_json([
        "#22c55e" if t["move"] == "up" else ("#ef4444" if t["move"] == "down" else "#94a3b8")
        for t in tickers
    ])

    recent = github_data.get("recent_repos", [])
    stale = github_data.get("stale_repos", [])
    prs = github_data.get("open_prs", [])

    # Repo rows
    repo_rows = ""
    for repo in recent[:10]:
        health = repo.get("health", "unknown")
        css_class = f"health-{health}"
        repo_rows += (
            f"<tr><td>{_esc(repo['name'])}</td>"
            f"<td>{_esc(repo.get('pushed_at', '')[:10])}</td>"
            f"<td>{_esc(str(repo.get('open_issues', 0)))}</td>"
            f"<td><span class=\"badge {_esc(css_class)}\">{_esc(health)}</span></td></tr>\n"
        )

    # PR rows
    pr_rows = ""
    for pr in prs[:8]:
        updated = pr.get("updated_at", "")
        pr_rows += (
            f"<tr><td>{_esc(pr.get('repo', ''))}</td>"
            f"<td>#{_esc(str(pr.get('number', '')))}</td>"
            f"<td>{_esc(pr.get('title', ''))}</td>"
            f"<td>{_esc(updated[:10] if updated else '')}</td></tr>\n"
        )

    # Portfolio rows
    portfolio_rows = ""
    for t in tickers:
        move_class = {"up": "text-green", "down": "text-red", "flat": "text-gray"}.get(t["move"], "text-gray")
        portfolio_rows += (
            f"<tr><td><strong>{_esc(t['ticker'])}</strong></td>"
            f"<td>{_esc(t['formatted_price'])}</td>"
            f"<td class=\"{move_class}\">{_esc(t['formatted_change'])}</td></tr>\n"
        )

    # Weather rows (every 2 hours, 6am–10pm)
    weather_rows = ""
    for hour in weather_data.get("hours", []):
        if not (6 <= hour.get("hour", 0) <= 22) or hour.get("hour", 0) % 2 != 0:
            continue
        run_s = hour["scores"]["run"]
        golf_s = hour["scores"]["golf"]
        boat_s = hour["scores"]["boat"]
        def sc(v: float) -> str:
            return "score-high" if v >= 70 else ("score-mid" if v >= 40 else "score-low")
        weather_rows += (
            f"<tr><td>{_esc(hour['time'][-5:])}</td>"
            f"<td>{_esc(str(hour['temp_c']))}°C</td>"
            f"<td>{_esc(str(hour['wind_kph']))} km/h</td>"
            f"<td>{_esc(str(hour['precip_prob']))}%</td>"
            f"<td class=\"{sc(run_s)}\">{_esc(str(run_s))}</td>"
            f"<td class=\"{sc(golf_s)}\">{_esc(str(golf_s))}</td>"
            f"<td class=\"{sc(boat_s)}\">{_esc(str(boat_s))}</td>"
            f"</tr>\n"
        )

    # AI section
    ai_section = ""
    if ai_summary:
        ai_section = (
            "<section class=\"card ai-card\">"
            "<h2>🤖 Today's Priorities</h2>"
            f"<div class=\"ai-text\">{_esc(ai_summary)}</div>"
            "</section>"
        )

    github_error = f"<p class=\"error\">⚠ {_esc(github_data.get('error', ''))}</p>" if github_data.get("error") else ""
    weather_error = f"<p class=\"error\">⚠ {_esc(weather_data.get('error', ''))}</p>" if weather_data.get("error") else ""

    github_table = (
        "<table><thead><tr><th>Repo</th><th>Last Push</th><th>Issues</th><th>Health</th></tr></thead>"
        f"<tbody>{repo_rows}</tbody></table>"
        if repo_rows else "<p class=\"empty-msg\">No recent repository activity</p>"
    )
    pr_section = (
        "<section class=\"card\">"
        "<h2>🔔 Open Pull Requests</h2>"
        "<table><thead><tr><th>Repo</th><th>PR</th><th>Title</th><th>Updated</th></tr></thead>"
        f"<tbody>{pr_rows}</tbody></table>"
        "</section>"
        if pr_rows else ""
    )
    portfolio_table = (
        "<table><thead><tr><th>Ticker</th><th>Price</th><th>Change</th></tr></thead>"
        f"<tbody>{portfolio_rows}</tbody></table>"
        if portfolio_rows else "<p class=\"empty-msg\">No portfolio data</p>"
    )
    weather_table = (
        "<table><thead><tr><th>Time</th><th>Temp</th><th>Wind</th><th>Rain</th>"
        "<th>🏃</th><th>⛳</th><th>⛵</th></tr></thead>"
        f"<tbody>{weather_rows}</tbody></table>"
        if weather_rows else "<p class=\"empty-msg\">No weather data</p>"
    )

    js_template = """\
const ctx = document.getElementById('portfolioChart');
if (ctx) {
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: __LABELS__,
      datasets: [{
        label: 'Change %',
        data: __VALUES__,
        backgroundColor: __COLORS__,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: '#1e293b' } },
        y: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: '#334155' } }
      }
    }
  });
}"""
    js_code = (
        js_template
        .replace("__LABELS__", chart_labels)
        .replace("__VALUES__", chart_values)
        .replace("__COLORS__", chart_colors)
    )

    up_count = _esc(str(portfolio_data.get("total_up", 0)))
    flat_count = _esc(str(portfolio_data.get("total_flat", 0)))
    down_count = _esc(str(portfolio_data.get("total_down", 0)))

    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        f"<title>Morning Briefing — {_esc(report_date)}</title>\n"
        "<script src=\"https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js\"></script>\n"
        f"<style>\n{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        f"<h1>Morning Briefing</h1>\n"
        f"<p class=\"subtitle\">{_esc(report_date)}</p>\n"
        f"{ai_section}\n"
        "<div class=\"grid\">\n"
        "<section class=\"card\">\n"
        "<h2>📁 GitHub Activity</h2>\n"
        f"{github_error}\n"
        "<div class=\"stat-row\">"
        f"<div><div class=\"stat\">{_esc(str(len(recent)))}</div><div class=\"stat-label\">active repos</div></div>"
        f"<div><div class=\"stat\">{_esc(str(len(stale)))}</div><div class=\"stat-label\">stale repos</div></div>"
        f"<div><div class=\"stat\">{_esc(str(len(prs)))}</div><div class=\"stat-label\">open PRs</div></div>"
        "</div>\n"
        f"{github_table}\n"
        "</section>\n"
        "<section class=\"card\">\n"
        "<h2>💹 Portfolio Pulse</h2>\n"
        "<div class=\"stat-row\">"
        f"<div><div class=\"stat text-green\">{up_count}</div><div class=\"stat-label\">up</div></div>"
        f"<div><div class=\"stat text-gray\">{flat_count}</div><div class=\"stat-label\">flat</div></div>"
        f"<div><div class=\"stat text-red\">{down_count}</div><div class=\"stat-label\">down</div></div>"
        "</div>\n"
        "<div class=\"chart-wrap\"><canvas id=\"portfolioChart\"></canvas></div>\n"
        f"{portfolio_table}\n"
        "</section>\n"
        "<section class=\"card\">\n"
        "<h2>⛅ Weather Windows</h2>\n"
        f"{weather_error}\n"
        f"{weather_table}\n"
        "</section>\n"
        f"{pr_section}\n"
        "</div>\n"
        f"<script>\n{js_code}\n</script>\n"
        "</body>\n"
        "</html>"
    )
