"""Render PackageResult lists as terminal text or self-contained HTML."""
import html as html_lib
from typing import List
from src.models import PackageResult, Summary

# ANSI colour codes
_RESET = "\033[0m"
_BOLD = "\033[1m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_CYAN = "\033[36m"
_DIM = "\033[2m"

_STATUS_COLOUR = {
    "up-to-date": _GREEN,
    "patch": _YELLOW,
    "minor": _YELLOW,
    "major": _RED,
    "unpinned": _CYAN,
    "unknown": _DIM,
    "error": _RED,
}

_STATUS_SYMBOL = {
    "up-to-date": "✓",
    "patch": "↑",
    "minor": "↑↑",
    "major": "↑↑↑",
    "unpinned": "?",
    "unknown": "–",
    "error": "✗",
}

_CSS = """
:root {
    --bg: #0d1117;
    --surface: #161b22;
    --border: #30363d;
    --text: #c9d1d9;
    --muted: #8b949e;
    --green: #3fb950;
    --yellow: #d29922;
    --orange: #e3712b;
    --red: #f85149;
    --cyan: #58a6ff;
    --radius: 6px;
    --font: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: var(--bg); color: var(--text);
    font-family: var(--font); font-size: 14px;
    padding: 24px; max-width: 1000px; margin: 0 auto;
}
h1 { font-size: 20px; margin-bottom: 4px; }
.subtitle { color: var(--muted); margin-bottom: 20px; font-size: 12px; }
.stats {
    display: flex; gap: 12px; flex-wrap: wrap;
    margin-bottom: 24px;
}
.stat-box {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 10px 16px;
    min-width: 100px; text-align: center;
}
.stat-box .num { font-size: 24px; font-weight: bold; }
.stat-box .label { font-size: 11px; color: var(--muted); margin-top: 2px; }
.ok { color: var(--green); }
.warn { color: var(--yellow); }
.crit { color: var(--red); }
.info { color: var(--cyan); }
table {
    width: 100%; border-collapse: collapse;
    background: var(--surface); border-radius: var(--radius);
    overflow: hidden; border: 1px solid var(--border);
}
th {
    text-align: left; padding: 10px 14px;
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
    color: var(--muted); border-bottom: 1px solid var(--border);
}
td { padding: 10px 14px; border-bottom: 1px solid var(--border); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #1c2129; }
.badge {
    display: inline-block; padding: 2px 8px; border-radius: 12px;
    font-size: 11px; font-weight: bold; letter-spacing: 0.3px;
}
.badge-ok  { background: #1a3a1a; color: var(--green); }
.badge-patch { background: #3a3000; color: var(--yellow); }
.badge-minor { background: #3a2500; color: var(--orange); }
.badge-major { background: #3a0a0a; color: var(--red); }
.badge-unpinned { background: #0d1f3a; color: var(--cyan); }
.badge-unknown { background: #1a1a1a; color: var(--muted); }
.yanked-flag {
    display: inline-block; background: #3a0a0a; color: var(--red);
    border: 1px solid var(--red); border-radius: 3px;
    font-size: 10px; padding: 1px 5px; margin-left: 4px;
    vertical-align: middle;
}
.muted { color: var(--muted); }
"""


def _status_badge_html(status: str) -> str:
    badge_class = {
        "up-to-date": "badge-ok",
        "patch": "badge-patch",
        "minor": "badge-minor",
        "major": "badge-major",
        "unpinned": "badge-unpinned",
    }.get(status, "badge-unknown")
    return f'<span class="badge {badge_class}">{html_lib.escape(status)}</span>'


def _stat_box(num: int, label: str, css_class: str = "") -> str:
    num_cls = f' class="{css_class}"' if css_class else ""
    return (
        f'<div class="stat-box">'
        f'<div class="num{num_cls}">{num}</div>'
        f'<div class="label">{label}</div>'
        f'</div>'
    )


def render_html(results: List[PackageResult], summary: Summary, title: str = "dep-check") -> str:
    """Render a self-contained HTML report. No external asset references."""
    from datetime import datetime, timezone
    generated = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Summary stat boxes
    needs = summary.needs_update
    needs_cls = "ok" if needs == 0 else ("warn" if needs <= 3 else "crit")
    yanked_cls = "crit" if summary.yanked > 0 else "ok"

    stat_boxes = "".join([
        _stat_box(summary.total, "total"),
        _stat_box(summary.up_to_date, "up-to-date", "ok"),
        _stat_box(needs, "need update", needs_cls),
        _stat_box(summary.major, "major", "crit" if summary.major else "ok"),
        _stat_box(summary.yanked, "yanked", yanked_cls),
        _stat_box(summary.unpinned, "unpinned", "info" if summary.unpinned else ""),
        _stat_box(summary.unknown, "unknown"),
    ])

    # Table rows
    rows = []
    for r in sorted(results, key=lambda x: (x.status == "up-to-date", x.req.name)):
        name = html_lib.escape(r.req.name)
        pinned = html_lib.escape(r.req.pinned_version or "—")
        latest = html_lib.escape(r.latest_version or "—")
        badge = _status_badge_html(r.status)
        yanked_html = ""
        if r.yanked:
            reason = html_lib.escape(r.yanked_reason or "no reason given")
            yanked_html = f'<span class="yanked-flag" title="{reason}">YANKED</span>'
        days = f"{r.days_since_pinned}d" if r.days_since_pinned is not None else "—"
        rows.append(
            f"<tr>"
            f'<td>{name}{yanked_html}</td>'
            f'<td>{pinned}</td>'
            f'<td>{latest}</td>'
            f'<td>{badge}</td>'
            f'<td class="muted">{days}</td>'
            f"</tr>"
        )
    table_body = "\n".join(rows) if rows else '<tr><td colspan="5" class="muted">No packages found.</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_lib.escape(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>{html_lib.escape(title)}</h1>
<p class="subtitle">Generated {generated}</p>
<div class="stats">{stat_boxes}</div>
<table>
<thead><tr>
<th>Package</th><th>Pinned</th><th>Latest</th><th>Status</th><th>Age</th>
</tr></thead>
<tbody>
{table_body}
</tbody>
</table>
</body>
</html>"""


def render_terminal(results: List[PackageResult], summary: Summary) -> str:
    """Render a coloured terminal table."""
    if not results:
        return "No packages found.\n"

    col_name = max(len(r.req.name) for r in results)
    col_name = max(col_name, 7)
    col_ver = 12

    header = (
        f"{'Package':<{col_name}}  {'Pinned':<{col_ver}}  {'Latest':<{col_ver}}  Status"
    )
    sep = "-" * len(header)

    lines = [_BOLD + header + _RESET, sep]
    for r in sorted(results, key=lambda x: (x.status == "up-to-date", x.req.name)):
        colour = _STATUS_COLOUR.get(r.status, _DIM)
        sym = _STATUS_SYMBOL.get(r.status, "?")
        pinned = r.req.pinned_version or "—"
        latest = r.latest_version or "—"
        yanked = " [YANKED]" if r.yanked else ""
        line = (
            f"{r.req.name:<{col_name}}  "
            f"{pinned:<{col_ver}}  "
            f"{latest:<{col_ver}}  "
            f"{colour}{sym} {r.status}{yanked}{_RESET}"
        )
        lines.append(line)

    lines.append(sep)
    needs = summary.needs_update
    needs_col = _GREEN if needs == 0 else (_YELLOW if needs <= 3 else _RED)
    lines.append(
        f"{_BOLD}{summary.total} packages{_RESET}: "
        f"{_GREEN}{summary.up_to_date} up-to-date{_RESET}, "
        f"{needs_col}{needs} need update{_RESET}"
        + (f", {_RED}{summary.yanked} yanked{_RESET}" if summary.yanked else "")
        + (f", {_CYAN}{summary.unpinned} unpinned{_RESET}" if summary.unpinned else "")
        + (f", {_DIM}{summary.unknown} unknown{_RESET}" if summary.unknown else "")
    )
    return "\n".join(lines) + "\n"
