"""Generate text reports, HTML reports, and clean CSV exports."""

import csv
import html as html_lib
import io
from datetime import datetime, timezone


# ── Text report ──────────────────────────────────────────────────────────────

def generate_text_report(quality, survey, source_name: str = "survey") -> str:
    """Return a plain-text quality report string for the given QualityReport."""
    q = quality
    ts = q.timing_stats
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    thr = q.thresholds

    lines = [
        "=" * 62,
        "  QUALTRICS SURVEY DATA QUALITY REPORT",
        f"  Source : {source_name}",
        f"  Generated: {now}",
        "=" * 62,
        "",
        "OVERVIEW",
        f"  Total respondents  : {q.respondent_count}",
        f"  Completed (100%)   : {q.completed_count}  ({q.completion_rate:.1%})",
        f"  Fast responses     : {len(q.fast_response_ids)}  (< {q.timing_threshold_seconds}s)",
        f"  Straight-liners    : {len(q.straight_liner_ids)}",
        f"  Duplicate IPs      : {len(q.duplicate_ips)}",
        f"  High missing (resp): {len(q.high_missing_respondents)}  (> {thr.missing_respondent_flag:.0%} items blank)",
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
            f"  Fast   : {ts['fast_count']} respondents (< {q.timing_threshold_seconds}s)",
            "",
        ]

    # Missing data by column
    missing_items = [
        (col, rate) for col, rate in q.per_column_missing.items() if rate > 0
    ]
    if missing_items:
        lines.append("MISSING DATA (columns with any missing)")
        for col, rate in sorted(missing_items, key=lambda x: -x[1]):
            bar_len = int(rate * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            flag = " !" if rate >= thr.missing_column_flag else (
                " ·" if rate >= thr.missing_column_warn else "  "
            )
            lines.append(f"  {col:<35} {bar} {rate:.1%}{flag}")
        lines.append("  ! = ≥ 20%  · = ≥ 5%")
        lines.append("")

    # Straight-liners & duplicate IPs
    if q.straight_liner_ids:
        lines.append(f"STRAIGHT-LINERS ({len(q.straight_liner_ids)})")
        for rid in q.straight_liner_ids[:10]:
            lines.append(f"  {rid}")
        if len(q.straight_liner_ids) > 10:
            lines.append(f"  … and {len(q.straight_liner_ids) - 10} more")
        lines.append("")
    if q.duplicate_ips:
        lines.append(f"DUPLICATE IPs ({len(q.duplicate_ips)})")
        for ip in q.duplicate_ips[:10]:
            lines.append(f"  {ip}")
        lines.append("")

    # Outliers
    total_outlier_cols = len(q.outlier_zscore) + len(q.outlier_iqr)
    if total_outlier_cols > 0:
        lines.append(f"OUTLIERS (z > {thr.outlier_z_threshold} or IQR fence)")
        z_all: dict = {}
        for col, ids in q.outlier_zscore.items():
            for rid, z in ids.items():
                z_all.setdefault(rid, []).append(f"{col} z={z:+.2f}")
        iqr_all: dict = {}
        for col, ids in q.outlier_iqr.items():
            for rid, val in ids.items():
                iqr_all.setdefault(rid, []).append(f"{col} IQR")
        # Respondents flagged on multiple columns
        multi = {
            rid: cnt for rid, cnt in q.respondent_outlier_counts.items() if cnt >= 2
        }
        if multi:
            lines.append(f"  Multi-column outliers ({len(multi)} respondents):")
            for rid, cnt in sorted(multi.items(), key=lambda x: -x[1])[:10]:
                lines.append(f"    {rid}  —  {cnt} columns")
        lines.append(
            f"  Z-score: {sum(len(v) for v in q.outlier_zscore.values())} flags across "
            f"{len(q.outlier_zscore)} column(s)"
        )
        lines.append(
            f"  IQR:     {sum(len(v) for v in q.outlier_iqr.values())} flags across "
            f"{len(q.outlier_iqr)} column(s)"
        )
        lines.append("")

    # Floor/ceiling effects
    affected = [
        (col, fc) for col, fc in q.floor_ceiling_effects.items()
        if fc["floor_effect"] or fc["ceiling_effect"]
    ]
    if affected:
        lines.append("FLOOR / CEILING EFFECTS (> 80% at scale endpoint)")
        for col, fc in affected:
            tags = []
            if fc["floor_effect"]:
                tags.append(f"floor {fc['floor_rate']:.0%}")
            if fc["ceiling_effect"]:
                tags.append(f"ceiling {fc['ceiling_rate']:.0%}")
            lines.append(f"  {col:<35} {', '.join(tags)}")
        lines.append("")

    # Distributional stats & normality
    non_normal = [
        (col, s) for col, s in q.column_stats.items()
        if s.get("normality") and not s["normality"]["is_normal"]
    ]
    if non_normal:
        lines.append("NORMALITY (D'Agostino–Pearson K², p < 0.05 = non-normal)")
        lines.append(f"  {'Column':<30} {'Skew':>7} {'Kurt':>7} {'K²':>7} {'p':>7}")
        lines.append("  " + "-" * 56)
        for col, s in non_normal[:20]:
            norm = s["normality"]
            lines.append(
                f"  {col:<30} {s.get('skewness') or 0:>+7.3f} "
                f"{s.get('kurtosis') or 0:>+7.3f} "
                f"{norm['statistic']:>7.3f} {norm['p_value']:>7.4f} *"
            )
        lines.append("")

    # Scale reliability + item-total correlations
    if q.cronbach_results:
        lines.append("SCALE RELIABILITY (Cronbach's α) & ITEM-TOTAL CORRELATIONS")
        for scale, alpha in sorted(q.cronbach_results.items()):
            if alpha is None:
                lines.append(f"  {scale:<20}  n/a (insufficient data)")
            else:
                lines.append(f"  {scale:<20}  α = {alpha:.3f}  [{_alpha_label(alpha)}]")
            itc = q.item_total_correlations.get(scale, {})
            if itc:
                for item, r in sorted(itc.items()):
                    flag = " !" if r is not None and r < q.thresholds.low_item_total_r else ""
                    r_str = f"{r:.3f}" if r is not None else " n/a"
                    lines.append(f"      {item:<28} r = {r_str}{flag}")
            lines.append("")

    # Correlation matrices
    for scale, matrix in q.correlation_matrices.items():
        cols = list(matrix.keys())
        if len(cols) < 2:
            continue
        lines.append(f"CORRELATION MATRIX — {scale}")
        header = f"  {'':>12}" + "".join(f"{c[:8]:>10}" for c in cols)
        lines.append(header)
        for ci in cols:
            row_str = f"  {ci[:12]:<12}"
            for cj in cols:
                val = matrix[ci].get(cj)
                if val is None:
                    row_str += f"{'n/a':>10}"
                elif ci == cj:
                    row_str += f"{'1.00':>10}"
                else:
                    row_str += f"{val:>10.3f}"
            lines.append(row_str)
        lines.append("")

    # Condition tests
    if q.condition_tests:
        lines.append(f"BETWEEN-GROUP TESTS  (condition: {q.condition_column})")
        for scale, result in q.condition_tests.items():
            test = result.get("test") or {}
            t_type = test.get("type", "")
            p = test.get("p_value")
            sig = " *" if p is not None and p < 0.05 else ""
            p_str = f"p = {p:.4f}{sig}" if p is not None else "n/a"
            lines.append(f"  {scale:<20}  {t_type}  {p_str}")
            for group, gs in result.get("group_stats", {}).items():
                lines.append(
                    f"      {str(group):<16} n={gs['n']}  "
                    f"M={gs.get('mean', '?')}  SD={gs.get('std', '?')}"
                )
            lines.append("")

    # Attention checks
    if q.attention_results:
        lines.append("ATTENTION CHECKS")
        for col, res in sorted(q.attention_results.items()):
            expected = res.get("expected") or "(unknown expected)"
            pass_rate = res.get("pass_rate")
            n = res.get("n_checked", 0)
            n_failed = len(res.get("failed_ids", []))
            if pass_rate is None:
                lines.append(f"  {col:<30} expected unknown  n={n}")
            else:
                flag = " !" if pass_rate < 0.80 else ""
                lines.append(
                    f"  {col:<30} expect='{expected}'  "
                    f"pass={pass_rate:.1%}  failed={n_failed}/{n}{flag}"
                )
        lines.append("")

    # Careless responding index
    if q.careless_index:
        from src.careless import careless_summary
        summary = careless_summary(q.careless_index)
        flagged = summary["n_flagged"]
        total = len(q.careless_index)
        lines.append(f"CARELESS RESPONDING INDEX  (threshold ≥ 0.40)")
        lines.append(f"  Flagged: {flagged}/{total} respondents")
        if summary["mean_score"] is not None:
            lines.append(f"  Mean score: {summary['mean_score']:.3f}")
        # Show top offenders
        top = sorted(q.careless_index.items(), key=lambda x: -x[1]["score"])[:10]
        if any(s > 0 for _, d in top for s in [d["score"]]):
            lines.append("  Highest scorers:")
            for rid, data in top:
                if data["score"] == 0:
                    break
                lines.append(
                    f"    {rid:<25} score={data['score']:.3f}  "
                    f"[{', '.join(data['flags'])}]"
                )
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
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem; margin-bottom: var(--gap); }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem; }
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
.alpha-pill { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.pill-excellent    { background: #14532d; color: #86efac; }
.pill-good         { background: #052e16; color: #4ade80; }
.pill-acceptable   { background: #1c1917; color: #fbbf24; }
.pill-questionable { background: #431407; color: #fb923c; }
.pill-poor         { background: #450a0a; color: #f87171; }
.pill-unacceptable { background: #1f0000; color: #fca5a5; }
.flag-chip { display: inline-block; background: #1e1b4b; color: #a5b4fc; border-radius: 4px; padding: 0.1rem 0.4rem; font-size: 0.7rem; margin: 0.1rem; }
.corr-cell { font-family: monospace; text-align: right; font-size: 0.8rem; }
.corr-pos-hi  { color: #22c55e; }
.corr-pos-mid { color: #86efac; }
.corr-neg-hi  { color: #ef4444; }
.corr-neg-mid { color: #fca5a5; }
.corr-diag    { color: var(--muted); }
.sig { color: var(--amber); font-weight: 700; }
@media (max-width: 600px) { .grid { grid-template-columns: 1fr 1fr; } body { padding: 1rem; } }
"""


def _color_class(rate: float) -> str:
    if rate < 0.05:
        return "good"
    if rate < 0.15:
        return "warn"
    return "bad"


def _alpha_pill_class(alpha: float) -> str:
    return "pill-" + _alpha_label(alpha)


def _corr_class(r) -> str:
    if r is None:
        return ""
    if r >= 0.7:
        return "corr-pos-hi"
    if r >= 0.3:
        return "corr-pos-mid"
    if r <= -0.7:
        return "corr-neg-hi"
    if r <= -0.3:
        return "corr-neg-mid"
    return ""


def generate_html_report(quality, survey, source_name: str = "survey") -> str:
    """Return a self-contained HTML quality report.

    All user-supplied strings are passed through html.escape() before insertion.
    """
    q = quality
    ts = q.timing_stats
    thr = q.thresholds
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    esc = html_lib.escape

    # ── Overview cards ──
    completion_cls = "good" if q.completion_rate >= 0.9 else ("warn" if q.completion_rate >= 0.7 else "bad")
    outlier_total = sum(q.respondent_outlier_counts.values())
    cards_html = f"""
    <div class="grid">
      <div class="card"><div class="card-value">{q.respondent_count}</div><div class="card-label">Total Respondents</div></div>
      <div class="card"><div class="card-value {completion_cls}">{q.completion_rate:.1%}</div><div class="card-label">Completion Rate</div></div>
      <div class="card"><div class="card-value {'bad' if q.fast_response_ids else 'good'}">{len(q.fast_response_ids)}</div><div class="card-label">Fast Responses (&lt;{q.timing_threshold_seconds}s)</div></div>
      <div class="card"><div class="card-value {'bad' if q.straight_liner_ids else 'good'}">{len(q.straight_liner_ids)}</div><div class="card-label">Straight-liners</div></div>
      <div class="card"><div class="card-value {'warn' if q.duplicate_ips else 'good'}">{len(q.duplicate_ips)}</div><div class="card-label">Duplicate IPs</div></div>
      <div class="card"><div class="card-value {'warn' if q.high_missing_respondents else 'good'}">{len(q.high_missing_respondents)}</div><div class="card-label">High-Missing Respondents</div></div>
      <div class="card"><div class="card-value {'warn' if outlier_total else 'good'}">{outlier_total}</div><div class="card-label">Outlier Flags</div></div>
    </div>"""

    # ── Timing ──
    timing_html = ""
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

    # ── Missing data ──
    missing_items = sorted(
        [(col, rate) for col, rate in q.per_column_missing.items() if rate > 0],
        key=lambda x: -x[1],
    )
    if missing_items:
        rows_html = ""
        for col, rate in missing_items:
            bar_w = int(rate * 100)
            bar_color = "#ef4444" if rate >= thr.missing_column_flag else (
                "#f59e0b" if rate >= thr.missing_column_warn else "#22c55e"
            )
            cls = _color_class(rate)
            rows_html += (
                f"<tr><td>{esc(col)}</td><td class='{cls}'>{rate:.1%}</td>"
                f"<td><div class='bar-outer'><div class='bar-inner' "
                f"style='width:{bar_w}%;background:{bar_color}'></div></div></td></tr>"
            )
        missing_html = f"""
    <section>
      <h2>Missing Data</h2>
      <table>
        <tr><th>Column</th><th>Missing %</th><th></th></tr>
        {rows_html}
      </table>
    </section>"""
    else:
        missing_html = """<section><h2>Missing Data</h2><p class="good">No missing data detected.</p></section>"""

    # ── Outliers ──
    outlier_html = ""
    if q.outlier_zscore or q.outlier_iqr:
        multi = {rid: cnt for rid, cnt in q.respondent_outlier_counts.items() if cnt >= 2}
        multi_rows = ""
        for rid, cnt in sorted(multi.items(), key=lambda x: -x[1])[:15]:
            multi_rows += f"<tr><td>{esc(rid)}</td><td>{cnt}</td></tr>"
        multi_section = (
            f"<p><strong>{len(multi)} respondent(s) are outliers on 2+ columns.</strong></p>"
            f"<table><tr><th>ResponseId</th><th>Columns flagged</th></tr>{multi_rows}</table>"
        ) if multi else ""

        z_count = sum(len(v) for v in q.outlier_zscore.values())
        iq_count = sum(len(v) for v in q.outlier_iqr.values())
        outlier_html = f"""
    <section>
      <h2>Outliers (z &gt; {thr.outlier_z_threshold} | IQR fence)</h2>
      <p>Z-score: <span class="warn">{z_count}</span> flags across {len(q.outlier_zscore)} column(s) &nbsp;|&nbsp;
         IQR: <span class="warn">{iq_count}</span> flags across {len(q.outlier_iqr)} column(s)</p>
      {multi_section}
    </section>"""

    # ── Floor/ceiling effects ──
    fc_html = ""
    affected = [(col, fc) for col, fc in q.floor_ceiling_effects.items()
                if fc["floor_effect"] or fc["ceiling_effect"]]
    if affected:
        fc_rows = ""
        for col, fc in affected:
            tags = []
            if fc["floor_effect"]:
                tags.append(f"<span class='flag-chip'>floor {fc['floor_rate']:.0%}</span>")
            if fc["ceiling_effect"]:
                tags.append(f"<span class='flag-chip'>ceiling {fc['ceiling_rate']:.0%}</span>")
            fc_rows += f"<tr><td>{esc(col)}</td><td>{''.join(tags)}</td></tr>"
        fc_html = f"""
    <section>
      <h2>Floor / Ceiling Effects (&gt;80% at scale endpoint)</h2>
      <table><tr><th>Column</th><th>Effect</th></tr>{fc_rows}</table>
    </section>"""

    # ── Distributional stats & normality ──
    norm_rows = ""
    for col, s in sorted(q.column_stats.items()):
        norm = s.get("normality")
        if norm is None:
            continue
        sig_cls = "" if norm["is_normal"] else " class='bad'"
        skew_str = f"{s.get('skewness') or 0:+.3f}"
        kurt_str = f"{s.get('kurtosis') or 0:+.3f}"
        p_flag = "" if norm["is_normal"] else " <span class='sig'>*</span>"
        norm_rows += (
            f"<tr{sig_cls}><td>{esc(col)}</td>"
            f"<td>{skew_str}</td><td>{kurt_str}</td>"
            f"<td>{norm['statistic']:.3f}</td>"
            f"<td>{norm['p_value']:.4f}{p_flag}</td></tr>"
        )
    norm_html = ""
    if norm_rows:
        norm_html = f"""
    <section>
      <h2>Distributional Statistics &amp; Normality (D'Agostino–Pearson K²)</h2>
      <table>
        <tr><th>Column</th><th>Skewness</th><th>Kurtosis</th><th>K²</th><th>p-value</th></tr>
        {norm_rows}
      </table>
      <p style="color:var(--muted);font-size:0.75rem;margin-top:0.5rem">* p &lt; 0.05 — departure from normality detected</p>
    </section>"""

    # ── Scale reliability + item-total correlations ──
    reliability_html = ""
    if q.cronbach_results:
        scale_sections = ""
        for scale_name, alpha in sorted(q.cronbach_results.items()):
            cols_list = esc(", ".join(q.detected_scales.get(scale_name, [])))
            if alpha is None:
                alpha_cell = "<td colspan='2' class='muted'>n/a — insufficient data</td>"
            else:
                pill_cls = _alpha_pill_class(alpha)
                label = _alpha_label(alpha)
                alpha_cell = f"<td>{alpha:.3f}</td><td><span class='alpha-pill {pill_cls}'>{label}</span></td>"

            itc = q.item_total_correlations.get(scale_name, {})
            itc_rows = ""
            for item, r in sorted(itc.items()):
                r_str = f"{r:.3f}" if r is not None else "n/a"
                flag = " <span class='bad'>!</span>" if r is not None and r < q.thresholds.low_item_total_r else ""
                itc_rows += f"<tr><td>{esc(item)}</td><td class='corr-cell'>{r_str}{flag}</td></tr>"

            itc_table = (
                f"<table style='margin-top:0.5rem'>"
                f"<tr><th>Item</th><th>Item-total r</th></tr>{itc_rows}</table>"
            ) if itc_rows else ""

            scale_sections += f"""
        <div style='margin-bottom:1.5rem'>
          <table>
            <tr><th>Scale</th><th>Items</th><th>α</th><th>Quality</th></tr>
            <tr><td>{esc(scale_name)}</td><td style='font-size:0.75rem;color:var(--muted)'>{cols_list}</td>{alpha_cell}</tr>
          </table>
          {itc_table}
        </div>"""
        reliability_html = f"""
    <section>
      <h2>Scale Reliability (Cronbach's α) &amp; Item-Total Correlations</h2>
      {scale_sections}
      <p style="color:var(--muted);font-size:0.75rem">! item-total r &lt; {q.thresholds.low_item_total_r} — consider removing item</p>
    </section>"""

    # ── Correlation matrices ──
    corr_html = ""
    corr_sections = ""
    for scale_name, matrix in q.correlation_matrices.items():
        cols = list(matrix.keys())
        if len(cols) < 2:
            continue
        header_cells = "".join(f"<th>{esc(c[:10])}</th>" for c in cols)
        matrix_rows = ""
        for ci in cols:
            cells = f"<td>{esc(ci[:14])}</td>"
            for cj in cols:
                val = matrix[ci].get(cj)
                if ci == cj:
                    cells += "<td class='corr-cell corr-diag'>1.00</td>"
                elif val is None:
                    cells += "<td class='corr-cell'>n/a</td>"
                else:
                    cls = _corr_class(val)
                    cells += f"<td class='corr-cell {cls}'>{val:.3f}</td>"
            matrix_rows += f"<tr>{cells}</tr>"
        corr_sections += f"""
        <div style='margin-bottom:1.5rem;overflow-x:auto'>
          <strong>{esc(scale_name)}</strong>
          <table style='margin-top:0.5rem'>
            <tr><th></th>{header_cells}</tr>
            {matrix_rows}
          </table>
        </div>"""
    if corr_sections:
        corr_html = f"""
    <section>
      <h2>Correlation Matrices</h2>
      {corr_sections}
    </section>"""

    # ── Response quality (straight-liners, dup IPs) ──
    straight_html = (
        f"<p class='bad'><strong>{len(q.straight_liner_ids)} straight-liner(s)</strong></p>"
        if q.straight_liner_ids else "<p class='good'>No straight-liners detected.</p>"
    )
    dup_html = (
        f"<p class='warn'><strong>{len(q.duplicate_ips)} duplicate IP(s):</strong> "
        + "".join(f"<span class='flag-chip'>{esc(ip)}</span>" for ip in q.duplicate_ips)
        + "</p>"
        if q.duplicate_ips else "<p class='good'>No duplicate IP addresses detected.</p>"
    )
    quality_section = f"""
    <section>
      <h2>Response Quality</h2>
      {straight_html}
      {dup_html}
    </section>"""

    # ── Attention checks ──
    attn_html = ""
    if q.attention_results:
        attn_rows = ""
        for col, res in sorted(q.attention_results.items()):
            expected = res.get("expected") or "(unknown)"
            pass_rate = res.get("pass_rate")
            n = res.get("n_checked", 0)
            n_failed = len(res.get("failed_ids", []))
            qt = esc((res.get("question_text") or "")[:80])
            if pass_rate is None:
                pass_cell = "<td colspan='3' style='color:var(--muted)'>expected answer unknown</td>"
            else:
                rate_cls = "good" if pass_rate >= 0.80 else "bad"
                pass_cell = (
                    f"<td class='{rate_cls}'>{pass_rate:.1%}</td>"
                    f"<td>{n_failed}/{n}</td>"
                    f"<td>{esc(str(expected))}</td>"
                )
            attn_rows += (
                f"<tr><td>{esc(col)}</td>{pass_cell}"
                f"<td style='font-size:0.75rem;color:var(--muted)'>{qt}</td></tr>"
            )
        attn_html = f"""
    <section>
      <h2>Attention Checks</h2>
      <table>
        <tr><th>Column</th><th>Pass Rate</th><th>Failed</th><th>Expected</th><th>Question</th></tr>
        {attn_rows}
      </table>
    </section>"""

    # ── Careless responding index ──
    careless_html = ""
    if q.careless_index:
        from src.careless import careless_summary
        summary = careless_summary(q.careless_index)
        flagged = summary["n_flagged"]
        total = len(q.careless_index)
        mean_score = summary.get("mean_score")
        mean_str = f"{mean_score:.3f}" if mean_score is not None else "n/a"
        flag_cls = "bad" if flagged else "good"

        top = sorted(q.careless_index.items(), key=lambda x: -x[1]["score"])[:15]
        top_rows = ""
        for rid, data in top:
            if data["score"] == 0:
                break
            score_cls = "bad" if data["score"] >= 0.6 else ("warn" if data["score"] >= 0.4 else "")
            chips = "".join(
                f"<span class='flag-chip'>{esc(f)}</span>" for f in data["flags"]
            )
            top_rows += (
                f"<tr><td>{esc(rid)}</td>"
                f"<td class='{score_cls}'>{data['score']:.3f}</td>"
                f"<td>{chips}</td></tr>"
            )

        dist = summary.get("score_distribution", {})
        dist_cells = "".join(
            f"<td style='text-align:center'>{dist.get(b, 0)}</td>"
            for b in ["0.0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"]
        )
        top_table = (
            f"<table style='margin-top:1rem'>"
            f"<tr><th>ResponseId</th><th>Score</th><th>Flags</th></tr>"
            f"{top_rows}</table>"
        ) if top_rows else ""

        careless_html = f"""
    <section>
      <h2>Careless Responding Index (threshold ≥ 0.40)</h2>
      <p><strong class="{flag_cls}">{flagged}/{total}</strong> respondents flagged
         &nbsp;|&nbsp; Mean score: {mean_str}</p>
      <table style='margin-top:0.75rem'>
        <tr><th>0.0–0.2</th><th>0.2–0.4</th><th>0.4–0.6</th>
            <th>0.6–0.8</th><th>0.8–1.0</th></tr>
        <tr>{dist_cells}</tr>
      </table>
      {top_table}
    </section>"""

    # ── Condition tests ──
    cond_html = ""
    if q.condition_tests:
        cond_rows = ""
        for scale, result in q.condition_tests.items():
            test = result.get("test") or {}
            p = test.get("p_value")
            t_type = test.get("type", "")
            p_str = f"{p:.4f}" if p is not None else "n/a"
            sig_span = " <span class='sig'>*</span>" if p is not None and p < 0.05 else ""
            gs = result.get("group_stats", {})
            group_detail = " | ".join(
                f"{esc(str(g))}: M={v.get('mean','?')} n={v['n']}"
                for g, v in gs.items()
            )
            cond_rows += (
                f"<tr><td>{esc(scale)}</td><td>{esc(t_type)}</td>"
                f"<td>{p_str}{sig_span}</td><td style='font-size:0.8rem;color:var(--muted)'>{group_detail}</td></tr>"
            )
        cond_html = f"""
    <section>
      <h2>Between-Group Tests (condition: {esc(str(q.condition_column))})</h2>
      <table>
        <tr><th>Scale</th><th>Test</th><th>p-value</th><th>Group means</th></tr>
        {cond_rows}
      </table>
      <p style="color:var(--muted);font-size:0.75rem;margin-top:0.5rem">* p &lt; 0.05 — significant difference between groups</p>
    </section>"""

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
{outlier_html}
{fc_html}
{norm_html}
{reliability_html}
{corr_html}
{cond_html}
{attn_html}
{careless_html}
</body>
</html>"""


# ── Clean CSV export ──────────────────────────────────────────────────────────

def export_clean_csv(
    survey,
    quality,
    exclude_incomplete: bool = True,
    exclude_fast: bool = True,
    exclude_straight_liners: bool = True,
    exclude_high_missing: bool = False,
) -> str:
    """Return a cleaned CSV string with a QI_Flags column appended.

    Rows matching the exclusion criteria are removed when the corresponding
    flag is True. All remaining rows get a QI_Flags value (empty string if clean).
    """
    from src.quality import _parse_duration, _get_response_id

    excluded_ids: set = set()
    if exclude_incomplete:
        for row in survey.rows:
            if str(row.get("Progress") or "").strip() != "100":
                excluded_ids.add(id(row))
    if exclude_fast:
        for row in survey.rows:
            d = _parse_duration(row)
            if d is not None and d < quality.timing_threshold_seconds:
                excluded_ids.add(id(row))
    if exclude_straight_liners:
        sl_set = set(quality.straight_liner_ids)
        for row in survey.rows:
            if _get_response_id(row) in sl_set:
                excluded_ids.add(id(row))
    if exclude_high_missing:
        hm_set = set(quality.high_missing_respondents)
        for row in survey.rows:
            if _get_response_id(row) in hm_set:
                excluded_ids.add(id(row))

    dup_ip_set = set(quality.duplicate_ips)
    fast_id_set = set(quality.fast_response_ids)
    sl_set = set(quality.straight_liner_ids)
    hm_set = set(quality.high_missing_respondents)

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
        d = _parse_duration(row)
        if d is not None and d < quality.timing_threshold_seconds:
            flags.append("fast_response")
        if _get_response_id(row) in sl_set:
            flags.append("straight_liner")
        ip = row.get("IPAddress") or row.get("ipAddress")
        if ip and ip in dup_ip_set:
            flags.append("duplicate_ip")
        if _get_response_id(row) in hm_set:
            flags.append("high_missing")

        values = [row.get(c) if row.get(c) is not None else "" for c in survey.column_names]
        values.append("|".join(flags))
        writer.writerow(values)

    return output.getvalue()
