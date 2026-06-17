"""Generate text reports, HTML reports, and clean CSV exports."""

import csv
import html as html_lib
import io
from datetime import datetime, timezone


# ── Text report ──────────────────────────────────────────────────────────────

def generate_text_report(quality, survey, source_name: str = "survey") -> str:
    """
    Return a plain-text quality report string for the given QualityReport.

    All numeric values are formatted for terminal readability.
    """
    q = quality
    ts = compute_timing_stats = q.timing_stats
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "=" * 62,
        "  QUALTRICS SURVEY DATA QUALITY REPORT",
        f"  Source : {source_name}",
        f"  Generated: {now}",
        "=" * 62,
        "",
        "OVERVIEW",
        f"  Total respondents  : {q.respondent_count}",
        f"  Completed (100%)   : {q.completed_count}  "
        f"({q.completion_rate:.1%})",
        f"  Fast responses     : {len(q.fast_response_ids)}  "
        f"(< {q.timing_threshold_seconds}s)",
        f"  Straight-liners    : {len(q.straight_liner_ids)}",
        f"  Duplicate IPs      : {len(q.duplicate_ips)}",
        "",
    ]

    # Timing
    if ts.get("count"):
        lines += [
            "TIMING (seconds)",
            f"  Mean   : {ts['mean']}",
            f"  Median : {ts['median']}",
            f"  Min    : {ts['min']}",
            f"  Max    : {ts['max']}",
            f"  Fast   : {ts['fast_count']} respondents "
            f"(< {q.timing_threshold_seconds}s)",
            "",
        ]

    # Missing data — only columns with any missing
    missing_items = [
        (col, rate)
        for col, rate in q.per_column_missing.items()
        if rate > 0
    ]
    if missing_items:
        lines.append("MISSING DATA (columns with any missing)")
        for col, rate in sorted(missing_items, key=lambda x: -x[1]):
            bar_len = int(rate * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"  {col:<35} {bar} {rate:.1%}")
        lines.append("")

    # Straight-liners
    if q.straight_liner_ids:
        lines.append(f"STRAIGHT-LINERS ({len(q.straight_liner_ids)})")
        for rid in q.straight_liner_ids[:10]:
            lines.append(f"  {rid}")
        if len(q.straight_liner_ids) > 10:
            lines.append(f"  … and {len(q.straight_liner_ids) - 10} more")
        lines.append("")

    # Duplicate IPs
    if q.duplicate_ips:
        lines.append(f"DUPLICATE IPs ({len(q.duplicate_ips)})")
        for ip in q.duplicate_ips[:10]:
            lines.append(f"  {ip}")
        lines.append("")

    # Cronbach's alpha
    if q.cronbach_results:
        lines.append("SCALE RELIABILITY (Cronbach's α)")
        for scale, alpha in sorted(q.cronbach_results.items()):
            if alpha is None:
                lines.append(f"  {scale:<20}  n/a (insufficient data)")
            else:
                interpretation = _alpha_label(alpha)
                lines.append(f"  {scale:<20}  α = {alpha:.3f}  [{interpretation}]")
        lines.append("")

    lines.append("=" * 62)
    return "\n".join(lines)


def _alpha_label(alpha: float) -> str:
    """Return a qualitative label for a Cronbach's alpha value."""
    if alpha >= 0.90:
        return "excellent"
    if alpha >= 0.80:
        return "good"
    if alpha >= 0.70:
        return "acceptable"
    if alpha >= 0.60:
        return "questionable"
    if alpha >= 0.50:
        return "poor"
    return "unacceptable"


# ── HTML report ───────────────────────────────────────────────────────────────

_CSS = """
:root {
  --bg: #0f1117;
  --surface: #1a1d27;
  --border: #2d3048;
  --text: #e2e8f0;
  --muted: #6b7280;
  --accent: #6366f1;
  --green: #22c55e;
  --amber: #f59e0b;
  --red: #ef4444;
  --radius: 8px;
  --gap: 1.5rem;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg); color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 14px; line-height: 1.6; padding: var(--gap);
}
h1 { font-size: 1.4rem; font-weight: 700; margin-bottom: 0.25rem; }
h2 { font-size: 1rem; font-weight: 600; color: var(--accent); margin-bottom: 1rem; }
.meta { color: var(--muted); font-size: 0.8rem; margin-bottom: var(--gap); }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; margin-bottom: var(--gap); }
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1rem;
}
.card-value { font-size: 2rem; font-weight: 700; }
.card-label { color: var(--muted); font-size: 0.8rem; }
.good { color: var(--green); }
.warn { color: var(--amber); }
.bad  { color: var(--red);   }
section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; margin-bottom: var(--gap); }
table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
th { text-align: left; padding: 0.5rem 0.75rem; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); }
td { padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border); vertical-align: middle; }
tr:last-child td { border-bottom: none; }
.bar-outer { background: var(--border); border-radius: 4px; height: 6px; width: 100px; display: inline-block; vertical-align: middle; }
.bar-inner { height: 6px; border-radius: 4px; }
.alpha-pill {
  display: inline-block; padding: 0.1rem 0.5rem; border-radius: 20px;
  font-size: 0.75rem; font-weight: 600;
}
.pill-excellent { background: #14532d; color: #86efac; }
.pill-good      { background: #052e16; color: #4ade80; }
.pill-acceptable{ background: #1c1917; color: #fbbf24; }
.pill-questionable { background: #431407; color: #fb923c; }
.pill-poor      { background: #450a0a; color: #f87171; }
.pill-unacceptable { background: #1f0000; color: #fca5a5; }
.flag-chip {
  display: inline-block; background: #1e1b4b; color: #a5b4fc;
  border-radius: 4px; padding: 0.1rem 0.4rem; font-size: 0.7rem; margin: 0.1rem;
}
@media (max-width: 600px) { .grid { grid-template-columns: 1fr 1fr; } body { padding: 1rem; } }
"""


def _color_class(rate: float) -> str:
    if rate < 0.05:
        return "good"
    if rate < 0.15:
        return "warn"
    return "bad"


def _alpha_pill_class(alpha: float) -> str:
    return "pill-" + _alpha_label(alpha).replace(" ", "-")


def generate_html_report(quality, survey, source_name: str = "survey") -> str:
    """
    Return a self-contained HTML quality report string.

    All user-supplied strings are passed through html.escape() before insertion.
    """
    q = quality
    ts = q.timing_stats
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    esc = html_lib.escape

    # Stat cards
    completion_cls = "good" if q.completion_rate >= 0.9 else ("warn" if q.completion_rate >= 0.7 else "bad")
    cards_html = f"""
    <div class="grid">
      <div class="card">
        <div class="card-value">{q.respondent_count}</div>
        <div class="card-label">Total Respondents</div>
      </div>
      <div class="card">
        <div class="card-value {completion_cls}">{q.completion_rate:.1%}</div>
        <div class="card-label">Completion Rate</div>
      </div>
      <div class="card">
        <div class="card-value {'bad' if q.fast_response_ids else 'good'}">{len(q.fast_response_ids)}</div>
        <div class="card-label">Fast Responses (&lt;{q.timing_threshold_seconds}s)</div>
      </div>
      <div class="card">
        <div class="card-value {'bad' if q.straight_liner_ids else 'good'}">{len(q.straight_liner_ids)}</div>
        <div class="card-label">Straight-liners</div>
      </div>
      <div class="card">
        <div class="card-value {'warn' if q.duplicate_ips else 'good'}">{len(q.duplicate_ips)}</div>
        <div class="card-label">Duplicate IPs</div>
      </div>
    </div>"""

    # Timing section
    if ts.get("count"):
        timing_html = f"""
    <section>
      <h2>Timing</h2>
      <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Mean</td><td>{ts['mean']}s</td></tr>
        <tr><td>Median</td><td>{ts['median']}s</td></tr>
        <tr><td>Min</td><td>{ts['min']}s</td></tr>
        <tr><td>Max</td><td>{ts['max']}s</td></tr>
        <tr><td>Fast responses (&lt;{q.timing_threshold_seconds}s)</td>
            <td class="{'bad' if ts['fast_count'] else 'good'}">{ts['fast_count']}</td></tr>
      </table>
    </section>"""
    else:
        timing_html = ""

    # Missing data section
    missing_items = sorted(
        [(col, rate) for col, rate in q.per_column_missing.items() if rate > 0],
        key=lambda x: -x[1],
    )
    if missing_items:
        rows_html = ""
        for col, rate in missing_items:
            bar_w = int(rate * 100)
            bar_color = "#ef4444" if rate >= 0.15 else ("#f59e0b" if rate >= 0.05 else "#22c55e")
            cls = _color_class(rate)
            rows_html += (
                f"<tr><td>{esc(col)}</td>"
                f"<td class='{cls}'>{rate:.1%}</td>"
                f"<td><div class='bar-outer'><div class='bar-inner' "
                f"style='width:{bar_w}%;background:{bar_color}'></div></div></td></tr>"
            )
        missing_html = f"""
    <section>
      <h2>Missing Data</h2>
      <table>
        <tr><th>Column</th><th>Missing %</th><th>Visual</th></tr>
        {rows_html}
      </table>
    </section>"""
    else:
        missing_html = """
    <section>
      <h2>Missing Data</h2>
      <p class="good">No missing data detected.</p>
    </section>"""

    # Response quality section
    straight_html = ""
    if q.straight_liner_ids:
        chips = "".join(f"<span class='flag-chip'>{esc(rid)}</span>" for rid in q.straight_liner_ids[:20])
        more = f" <span class='muted'>…and {len(q.straight_liner_ids)-20} more</span>" if len(q.straight_liner_ids) > 20 else ""
        straight_html = f"<p class='bad'><strong>{len(q.straight_liner_ids)} straight-liner(s):</strong> {chips}{more}</p>"
    else:
        straight_html = "<p class='good'>No straight-liners detected.</p>"

    dup_html = ""
    if q.duplicate_ips:
        chips = "".join(f"<span class='flag-chip'>{esc(ip)}</span>" for ip in q.duplicate_ips)
        dup_html = f"<p class='warn'><strong>{len(q.duplicate_ips)} duplicate IP(s):</strong> {chips}</p>"
    else:
        dup_html = "<p class='good'>No duplicate IP addresses detected.</p>"

    quality_section = f"""
    <section>
      <h2>Response Quality</h2>
      {straight_html}
      {dup_html}
    </section>"""

    # Scale reliability section
    if q.cronbach_results:
        scale_rows = ""
        for scale_name, alpha in sorted(q.cronbach_results.items()):
            cols_list = ", ".join(esc(c) for c in q.detected_scales.get(scale_name, []))
            if alpha is None:
                scale_rows += (
                    f"<tr><td>{esc(scale_name)}</td><td>{cols_list}</td>"
                    f"<td colspan='2' class='muted'>n/a</td></tr>"
                )
            else:
                pill_cls = _alpha_pill_class(alpha)
                label = _alpha_label(alpha)
                scale_rows += (
                    f"<tr><td>{esc(scale_name)}</td><td>{cols_list}</td>"
                    f"<td>{alpha:.3f}</td>"
                    f"<td><span class='alpha-pill {pill_cls}'>{label}</span></td></tr>"
                )
        reliability_html = f"""
    <section>
      <h2>Scale Reliability (Cronbach's α)</h2>
      <table>
        <tr><th>Scale</th><th>Items</th><th>α</th><th>Quality</th></tr>
        {scale_rows}
      </table>
    </section>"""
    else:
        reliability_html = ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Survey QC Report — {esc(source_name)}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>Survey Data Quality Report</h1>
<p class="meta">Source: {esc(source_name)} &nbsp;|&nbsp; Generated: {now}</p>
{cards_html}
{timing_html}
{missing_html}
{quality_section}
{reliability_html}
</body>
</html>"""


# ── Clean CSV export ──────────────────────────────────────────────────────────

def export_clean_csv(
    survey,
    quality,
    exclude_incomplete: bool = True,
    exclude_fast: bool = True,
    exclude_straight_liners: bool = True,
) -> str:
    """
    Return a cleaned CSV string with a QI_Flags column appended.

    Rows matching the exclusion criteria are removed when the corresponding
    flag is True. All remaining rows get a QI_Flags value (empty string if clean).
    """
    excluded_ids: set = set()
    if exclude_incomplete:
        for row in survey.rows:
            if str(row.get("Progress") or "").strip() != "100":
                excluded_ids.add(id(row))
    if exclude_fast:
        for row in survey.rows:
            from src.quality import _parse_duration
            d = _parse_duration(row)
            if d is not None and d < quality.timing_threshold_seconds:
                excluded_ids.add(id(row))
    if exclude_straight_liners:
        sl_set = set(quality.straight_liner_ids)
        for row in survey.rows:
            from src.quality import _get_response_id
            if _get_response_id(row) in sl_set:
                excluded_ids.add(id(row))

    dup_ip_set = set(quality.duplicate_ips)
    fast_id_set = set(quality.fast_response_ids)
    sl_set = set(quality.straight_liner_ids)

    col_names = survey.column_names + ["QI_Flags"]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(col_names)

    for row in survey.rows:
        if id(row) in excluded_ids:
            continue
        flags = []
        if str(row.get("Progress") or "").strip() != "100":
            flags.append("incomplete")
        from src.quality import _parse_duration, _get_response_id
        d = _parse_duration(row)
        if d is not None and d < quality.timing_threshold_seconds:
            flags.append("fast_response")
        if _get_response_id(row) in sl_set:
            flags.append("straight_liner")
        ip = row.get("IPAddress") or row.get("ipAddress")
        if ip and ip in dup_ip_set:
            flags.append("duplicate_ip")

        values = [row.get(c) if row.get(c) is not None else "" for c in survey.column_names]
        values.append("|".join(flags))
        writer.writerow(values)

    return output.getvalue()
