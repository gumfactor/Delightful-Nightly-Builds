"""Self-contained dark-mode HTML report generation for TrialScope (no external requests)."""
from __future__ import annotations

import csv
import html
import statistics
from typing import Optional

from parsing import Trial
from qc import ConditionSummary, QCConfig, SubjectSummary, TrialFlagResult


def esc(value) -> str:
    """HTML-escape any user-derived value before embedding it in the report."""
    return html.escape(str(value), quote=True)


def _svg_bar_chart(labels: list[str], values: list[float], width: int = 480, height: int = 220,
                    value_fmt: str = "{:.1f}", bar_color: str = "#5fb3ff") -> str:
    if not labels:
        return "<p class='empty'>No data.</p>"
    max_val = max(values) if values and max(values) > 0 else 1.0
    padding_left = 60
    padding_bottom = 40
    plot_w = width - padding_left - 20
    plot_h = height - padding_bottom - 20
    bar_w = plot_w / len(labels)

    bars = []
    for i, (label, val) in enumerate(zip(labels, values)):
        bar_h = (val / max_val) * plot_h
        x = padding_left + i * bar_w + bar_w * 0.15
        y = 20 + (plot_h - bar_h)
        w = bar_w * 0.7
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{bar_h:.1f}" fill="{bar_color}" rx="2">'
            f"<title>{esc(label)}: {value_fmt.format(val)}</title></rect>"
        )
        bars.append(
            f'<text x="{x + w/2:.1f}" y="{height - padding_bottom + 16}" font-size="10" '
            f'fill="#b8c2cc" text-anchor="middle">{esc(label[:10])}</text>'
        )
        bars.append(
            f'<text x="{x + w/2:.1f}" y="{y - 4:.1f}" font-size="10" fill="#e6edf3" '
            f'text-anchor="middle">{value_fmt.format(val)}</text>'
        )

    axis = f'<line x1="{padding_left}" y1="{20 + plot_h}" x2="{width - 20}" y2="{20 + plot_h}" stroke="#3a4552" />'
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img">'
        f"{axis}{''.join(bars)}</svg>"
    )


def _svg_histogram(values: list[float], bins: int = 12, width: int = 480, height: int = 220,
                    color: str = "#7ee787") -> str:
    values = [v for v in values if v is not None]
    if not values:
        return "<p class='empty'>No reaction-time data.</p>"
    lo, hi = min(values), max(values)
    if lo == hi:
        hi = lo + 1
    bin_width = (hi - lo) / bins
    counts = [0] * bins
    for v in values:
        idx = min(bins - 1, int((v - lo) / bin_width))
        counts[idx] += 1
    labels = [f"{lo + i * bin_width:.0f}" for i in range(bins)]
    return _svg_bar_chart(labels, counts, width=width, height=height, value_fmt="{:.0f}", bar_color=color)


def _svg_line_chart(series: dict[str, list[dict]], y_key: str, width: int = 480, height: int = 220,
                     y_fmt: str = "{:.2f}") -> str:
    colors = ["#5fb3ff", "#f78166", "#7ee787", "#d2a8ff", "#f2cc60"]
    all_points = [p for pts in series.values() for p in pts if p.get(y_key) is not None]
    if not all_points:
        return "<p class='empty'>No data.</p>"
    y_vals = [p[y_key] for p in all_points]
    y_min, y_max = min(y_vals), max(y_vals)
    if y_min == y_max:
        y_max = y_min + 1
    padding_left = 50
    padding_bottom = 30
    plot_w = width - padding_left - 20
    plot_h = height - padding_bottom - 20
    max_n_bins = max((len(pts) for pts in series.values()), default=1) or 1

    def x_for(i: int) -> float:
        return padding_left + (i / max(1, max_n_bins - 1)) * plot_w

    def y_for(v: float) -> float:
        return 20 + plot_h - ((v - y_min) / (y_max - y_min)) * plot_h

    parts = [f'<line x1="{padding_left}" y1="{20+plot_h}" x2="{width-20}" y2="{20+plot_h}" stroke="#3a4552" />']
    legend = []
    for ci, (condition, pts) in enumerate(sorted(series.items())):
        color = colors[ci % len(colors)]
        coords = [(x_for(i), y_for(p[y_key])) for i, p in enumerate(pts) if p.get(y_key) is not None]
        if not coords:
            continue
        path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(coords))
        parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" />')
        for x, y in coords:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}" />')
        legend.append(f'<span style="color:{color}">&#9679;</span> {esc(condition)}')

    legend_html = '<div class="legend">' + " &nbsp; ".join(legend) + "</div>"
    svg = f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img">{"".join(parts)}</svg>'
    return legend_html + svg


def render_report(
    subjects: list[SubjectSummary],
    conditions: list[ConditionSummary],
    trials: list[Trial],
    excluded: list[SubjectSummary],
    methods_paragraph: str,
    methods_source: str,
    config: QCConfig,
    curves: dict[str, list[dict]],
    parse_warnings: int,
) -> str:
    n_subjects = len(subjects)
    n_excluded = len(excluded)
    n_trials = len(trials)

    subject_rows = []
    for s in subjects:
        flag_html = "".join(f'<span class="badge">{esc(f)}</span>' for f in s.flags) or '<span class="ok">clean</span>'
        excl_attr = "true" if s.excluded else "false"
        mean_rt_cell = "" if s.mean_rt is None else f"{s.mean_rt:.0f}"
        sd_rt_cell = "" if s.sd_rt is None else f"{s.sd_rt:.0f}"
        subject_rows.append(
            f"<tr data-excluded='{excl_attr}'>"
            f"<td>{esc(s.subject)}</td><td>{s.n_trials}</td>"
            f"<td>{s.accuracy:.0%}</td>"
            f"<td>{mean_rt_cell}</td>"
            f"<td>{sd_rt_cell}</td>"
            f"<td>{s.n_fast_guess}</td><td>{s.n_outlier}</td>"
            f"<td>{flag_html}</td></tr>"
        )

    condition_rows = []
    for c in conditions:
        condition_rows.append(
            f"<tr><td>{esc(c.condition)}</td><td>{c.n_subjects}</td><td>{c.n_trials}</td>"
            f"<td>{c.accuracy:.0%}</td>"
            f"<td>{'' if c.mean_rt is None else f'{c.mean_rt:.0f}'}</td>"
            f"<td>{'' if c.sd_rt is None else f'{c.sd_rt:.0f}'}</td></tr>"
        )

    rt_by_condition: dict[str, list[float]] = {}
    for t in trials:
        if t.rt_ms is not None and t.correct:
            rt_by_condition.setdefault(t.condition, []).append(t.rt_ms)

    histograms = "".join(
        f"<div class='chart-card'><h4>{esc(cond)} — correct-trial RT distribution</h4>"
        f"{_svg_histogram(rts)}</div>"
        for cond, rts in sorted(rt_by_condition.items())
    )

    accuracy_by_condition = _svg_bar_chart(
        [c.condition for c in conditions], [c.accuracy * 100 for c in conditions],
        value_fmt="{:.0f}%",
    )

    accuracy_curve = _svg_line_chart(curves, "accuracy", y_fmt="{:.0%}")
    rt_curve = _svg_line_chart(curves, "mean_rt", y_fmt="{:.0f}")

    source_note = "Anthropic API (Claude)" if methods_source == "ai" else "deterministic template (no API key set)"

    empty_notice = ""
    if n_subjects == 0:
        empty_notice = "<p class='empty-banner'>No trial data found in the input file — nothing to report.</p>"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>TrialScope Report</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    background: #0d1117; color: #e6edf3; font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    margin: 0; padding: 24px; line-height: 1.5;
  }}
  h1 {{ font-size: 1.6rem; margin-bottom: 4px; }}
  h2 {{ margin-top: 40px; border-bottom: 1px solid #21262d; padding-bottom: 6px; }}
  .subtitle {{ color: #8b949e; margin-top: 0; }}
  .stat-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 20px 0; }}
  .stat-card {{
    background: #161b22; border: 1px solid #30363d; border-radius: 8px;
    padding: 14px 18px; min-width: 140px; flex: 1;
  }}
  .stat-card .value {{ font-size: 1.8rem; font-weight: 600; }}
  .stat-card .label {{ color: #8b949e; font-size: 0.85rem; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 0.9rem; }}
  th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid #21262d; }}
  th {{ color: #8b949e; cursor: pointer; user-select: none; }}
  th:hover {{ color: #e6edf3; }}
  tr[data-excluded='true'] {{ background: rgba(248, 81, 73, 0.08); }}
  .badge {{
    display: inline-block; background: #3d1d1d; color: #ffa198; border-radius: 4px;
    padding: 1px 6px; font-size: 0.75rem; margin-right: 4px; margin-bottom: 2px;
  }}
  .ok {{ color: #7ee787; font-size: 0.85rem; }}
  .chart-grid {{ display: flex; flex-wrap: wrap; gap: 16px; }}
  .chart-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; flex: 1; min-width: 320px; }}
  .chart-card h4 {{ margin: 0 0 8px 0; font-size: 0.9rem; color: #8b949e; }}
  .legend {{ font-size: 0.8rem; color: #8b949e; margin-bottom: 4px; }}
  .methods-box {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }}
  .methods-box .source {{ color: #8b949e; font-size: 0.8rem; margin-top: 10px; }}
  input#search {{
    background: #0d1117; border: 1px solid #30363d; color: #e6edf3; padding: 6px 10px;
    border-radius: 6px; width: 260px; margin-bottom: 10px;
  }}
  .empty {{ color: #8b949e; font-size: 0.85rem; }}
  .empty-banner {{ background: #3d1d1d; color: #ffa198; padding: 10px 14px; border-radius: 6px; }}
</style>
</head>
<body>
<h1>TrialScope — Behavioral Data QC Report</h1>
<p class="subtitle">{n_subjects} subjects &middot; {n_trials} trials &middot; {len(conditions)} conditions
&middot; {parse_warnings} malformed cell(s) coerced during parsing</p>
{empty_notice}

<div class="stat-row">
  <div class="stat-card"><div class="value">{n_subjects}</div><div class="label">Total subjects</div></div>
  <div class="stat-card"><div class="value">{n_excluded}</div><div class="label">Recommended exclusions</div></div>
  <div class="stat-card"><div class="value">{n_subjects - n_excluded}</div><div class="label">Final analytic sample</div></div>
  <div class="stat-card"><div class="value">{n_trials}</div><div class="label">Total trials</div></div>
</div>

<h2>Participants &amp; Data Quality</h2>
<div class="methods-box">
  <p id="methods-paragraph">{esc(methods_paragraph)}</p>
  <p class="source">Generated by: {esc(source_note)}</p>
</div>

<h2>Subjects</h2>
<input id="search" type="text" placeholder="Filter by subject ID..." onkeyup="filterSubjects()">
<table id="subject-table">
  <thead><tr>
    <th onclick="sortTable(0)">Subject</th><th onclick="sortTable(1)">Trials</th>
    <th onclick="sortTable(2)">Accuracy</th><th onclick="sortTable(3)">Mean RT</th>
    <th onclick="sortTable(4)">SD RT</th><th onclick="sortTable(5)">Fast guesses</th>
    <th onclick="sortTable(6)">Outliers</th><th>Flags</th>
  </tr></thead>
  <tbody>{"".join(subject_rows)}</tbody>
</table>

<h2>Conditions</h2>
<table>
  <thead><tr><th>Condition</th><th>Subjects</th><th>Trials</th><th>Accuracy</th><th>Mean RT</th><th>SD RT</th></tr></thead>
  <tbody>{"".join(condition_rows)}</tbody>
</table>

<h2>Accuracy by Condition</h2>
<div class="chart-card">{accuracy_by_condition}</div>

<h2>Reaction Time Distributions (correct trials)</h2>
<div class="chart-grid">{histograms}</div>

<h2>Learning Curves (binned trial position)</h2>
<div class="chart-grid">
  <div class="chart-card"><h4>Accuracy across trial blocks</h4>{accuracy_curve}</div>
  <div class="chart-card"><h4>Mean RT across trial blocks</h4>{rt_curve}</div>
</div>

<h2>Configuration Used</h2>
<table>
  <tbody>
    <tr><td>RT floor (anticipatory)</td><td>{config.rt_floor_ms:.0f} ms</td></tr>
    <tr><td>RT ceiling (absolute outlier)</td><td>{config.rt_ceiling_ms:.0f} ms</td></tr>
    <tr><td>SD outlier multiplier</td><td>{config.sd_outlier:.1f}</td></tr>
    <tr><td>Chance rate</td><td>{config.chance_rate:.0%}</td></tr>
    <tr><td>Chance-level alpha</td><td>{config.chance_alpha:.2f}</td></tr>
    <tr><td>Minimum completion fraction</td><td>{config.min_completion:.0%}</td></tr>
    <tr><td>Exclusion flag-count threshold</td><td>{config.exclude_threshold}</td></tr>
  </tbody>
</table>

<script>
function filterSubjects() {{
  const q = document.getElementById('search').value.toLowerCase();
  const rows = document.querySelectorAll('#subject-table tbody tr');
  rows.forEach(row => {{
    const subject = row.children[0].textContent.toLowerCase();
    row.style.display = subject.includes(q) ? '' : 'none';
  }});
}}

let sortState = {{}};
function sortTable(colIndex) {{
  const table = document.getElementById('subject-table');
  const tbody = table.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const asc = !sortState[colIndex];
  sortState = {{ [colIndex]: asc }};
  rows.sort((a, b) => {{
    const av = a.children[colIndex].textContent.replace('%','');
    const bv = b.children[colIndex].textContent.replace('%','');
    const an = parseFloat(av), bn = parseFloat(bv);
    if (!isNaN(an) && !isNaN(bn)) return asc ? an - bn : bn - an;
    return asc ? av.localeCompare(bv) : bv.localeCompare(av);
  }});
  rows.forEach(r => tbody.appendChild(r));
}}
</script>
</body>
</html>
"""


def write_cleaned_csv(path: str, trials: list[Trial], flags: list[TrialFlagResult]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["subject", "condition", "block", "trial_num", "rt_ms", "correct", "QC_Flag"])
        for t, flag in zip(trials, flags):
            writer.writerow([
                t.subject,
                t.condition,
                t.block,
                t.trial_num,
                "" if t.rt_ms is None else t.rt_ms,
                "" if t.correct is None else t.correct,
                flag.flag,
            ])


def write_exclusions_csv(path: str, excluded: list[SubjectSummary]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["subject", "reasons"])
        for s in excluded:
            writer.writerow([s.subject, "; ".join(s.flags)])
