"""Terminal, JSON, and self-contained HTML report rendering for Voiceprint."""

from __future__ import annotations

import html
import json

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"


def _score_color(score: float, use_color: bool) -> str:
    if not use_color:
        return ""
    if score >= 80:
        return GREEN
    if score >= 60:
        return YELLOW
    return RED


def _score_label(score: float) -> str:
    if score >= 80:
        return "Reads natural"
    if score >= 60:
        return "Some formulaic patterns"
    return "Heavily flagged"


def render_terminal(
    file_path: str, analysis: dict, score_result: dict, review: dict | None = None, use_color: bool = True
) -> str:
    score = score_result["score"]
    color = _score_color(score, use_color)
    reset = RESET if use_color else ""
    bold = BOLD if use_color else ""

    lines = [
        f"{bold}Voiceprint report — {file_path}{reset}",
        f"{color}{bold}Human Voice Score: {score}/100 ({_score_label(score)}){reset}",
        f"Words: {analysis['word_count']}  Sentences: {analysis['sentence_count']}  Flags: {score_result['flag_count']}",
        "",
        "Penalty breakdown:",
    ]
    for category, penalty in score_result["breakdown"].items():
        if penalty > 0:
            lines.append(f"  - {category.replace('_', ' ')}: -{penalty:.1f}")

    ai_tell_hits = analysis["ai_tell_hits"]
    if ai_tell_hits:
        lines.append("")
        lines.append(f"AI-tell phrases ({len(ai_tell_hits)} total):")
        for hit in ai_tell_hits[:15]:
            lines.append(f"  line {hit['line']}: \"{hit['phrase']}\" — {hit['excerpt'][:80]}")
        if len(ai_tell_hits) > 15:
            lines.append(f"  ... and {len(ai_tell_hits) - 15} more")

    if review is not None:
        lines.append("")
        lines.append(f"Second opinion ({review['source']}):")
        for item in review["items"]:
            lines.append(f"  - {item['diagnosis']}")
            if item.get("rewrite"):
                lines.append(f"    Suggested rewrite: {item['rewrite']}")

    return "\n".join(lines)


def render_json(file_path: str, analysis: dict, score_result: dict, review: dict | None = None) -> str:
    payload = {
        "file_path": file_path,
        "score": score_result["score"],
        "flag_count": score_result["flag_count"],
        "breakdown": score_result["breakdown"],
        "word_count": analysis["word_count"],
        "sentence_count": analysis["sentence_count"],
        "ai_tell_hits": analysis["ai_tell_hits"],
        "em_dash_count": analysis["em_dash_count"],
        "semicolon_count": analysis["semicolon_count"],
        "hedge_hit_count": len(analysis["hedge_hits"]),
        "passive_match_count": len(analysis["passive_matches"]),
        "rule_of_three_count": len(analysis["rule_of_three_matches"]),
        "type_token_ratio": analysis["type_token_ratio"],
        "repeated_openers": analysis["repeated_openers"],
        "review": review,
    }
    return json.dumps(payload, indent=2)


def _history_table_rows(history: list[dict]) -> str:
    rows = []
    for entry in history:
        rows.append(
            "<tr>"
            f"<td>{html.escape(entry['run_at'])}</td>"
            f"<td>{entry['score']}</td>"
            f"<td>{entry['word_count']}</td>"
            f"<td>{entry['flag_count']}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_html(
    file_path: str,
    analysis: dict,
    score_result: dict,
    review: dict | None = None,
    history: list[dict] | None = None,
) -> str:
    history = history or []
    score = score_result["score"]
    safe_file_path = html.escape(file_path)

    ai_tell_rows = "\n".join(
        "<tr>"
        f"<td>{hit['line']}</td>"
        f"<td><code>{html.escape(hit['phrase'])}</code></td>"
        f"<td>{html.escape(hit['excerpt'])}</td>"
        "</tr>"
        for hit in analysis["ai_tell_hits"]
    )

    breakdown_rows = "\n".join(
        f"<tr><td>{html.escape(category.replace('_', ' '))}</td><td>-{penalty:.1f}</td></tr>"
        for category, penalty in score_result["breakdown"].items()
        if penalty > 0
    )

    review_html = ""
    if review is not None:
        items_html = "\n".join(
            "<div class='review-item'>"
            f"<p class='diagnosis'>{html.escape(item['diagnosis'])}</p>"
            + (
                f"<p class='rewrite'><strong>Suggested rewrite:</strong> {html.escape(item['rewrite'])}</p>"
                if item.get("rewrite")
                else ""
            )
            + "</div>"
            for item in review["items"]
        )
        review_html = f"""
        <section>
          <h2>Second opinion <span class="tag">{html.escape(review['source'])}</span></h2>
          {items_html}
        </section>
        """

    history_rows = _history_table_rows(history)
    history_scores = json.dumps([entry["score"] for entry in history])
    history_labels = json.dumps([entry["run_at"] for entry in history])

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voiceprint report — {safe_file_path}</title>
<style>
  :root {{
    --bg: #0f1115; --panel: #171a21; --text: #e8eaed; --muted: #9aa0a6;
    --accent: #7cc7ff; --good: #4caf50; --warn: #ffb74d; --bad: #ef5350;
    --border: #2a2e37;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont,
    "Segoe UI", Roboto, sans-serif; margin: 0; padding: 1.5rem; line-height: 1.5;
  }}
  h1 {{ font-size: 1.2rem; word-break: break-all; }}
  h2 {{ font-size: 1.05rem; margin-top: 2rem; }}
  .score {{
    font-size: 3rem; font-weight: 700;
    color: {"var(--good)" if score >= 80 else "var(--warn)" if score >= 60 else "var(--bad)"};
  }}
  .score-label {{ color: var(--muted); }}
  section {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; margin-top: 1rem; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th, td {{ text-align: left; padding: 0.4rem; border-bottom: 1px solid var(--border); }}
  code {{ background: #232733; padding: 0.1rem 0.3rem; border-radius: 4px; }}
  .stats {{ color: var(--muted); }}
  .tag {{ font-size: 0.75rem; background: #232733; padding: 0.1rem 0.5rem; border-radius: 999px; margin-left: 0.5rem; }}
  .review-item {{ border-top: 1px solid var(--border); padding-top: 0.6rem; margin-top: 0.6rem; }}
  .review-item:first-child {{ border-top: none; margin-top: 0; padding-top: 0; }}
  .rewrite {{ color: var(--accent); }}
  #history-chart {{ max-width: 100%; }}
  @media (max-width: 480px) {{ body {{ padding: 0.75rem; }} .score {{ font-size: 2.2rem; }} }}
</style>
</head>
<body>
  <h1>Voiceprint — {safe_file_path}</h1>
  <div class="score">{score}<span style="font-size:1.2rem;color:var(--muted)">/100</span></div>
  <div class="score-label">{html.escape(_score_label(score))}</div>
  <p class="stats">{analysis['word_count']} words · {analysis['sentence_count']} sentences · {score_result['flag_count']} flags</p>

  <section>
    <h2>Penalty breakdown</h2>
    <table><tbody>{breakdown_rows or '<tr><td colspan="2">No penalties — clean by every heuristic.</td></tr>'}</tbody></table>
  </section>

  <section>
    <h2>AI-tell phrases ({len(analysis['ai_tell_hits'])})</h2>
    <table>
      <thead><tr><th>Line</th><th>Phrase</th><th>Excerpt</th></tr></thead>
      <tbody>{ai_tell_rows or '<tr><td colspan="3">None found.</td></tr>'}</tbody>
    </table>
  </section>

  {review_html}

  <section>
    <h2>History ({len(history)} run{'s' if len(history) != 1 else ''})</h2>
    <canvas id="history-chart" height="120"></canvas>
    <table>
      <thead><tr><th>Run</th><th>Score</th><th>Words</th><th>Flags</th></tr></thead>
      <tbody>{history_rows or '<tr><td colspan="4">No prior runs recorded for this file.</td></tr>'}</tbody>
    </table>
  </section>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js" integrity="sha512-2NRPvSDT+w7c2VwaC7EQ2RdEBTdmDkeaEUXQzc/wF3lB4WNsuXaKS12+ivgMKNs+ELlAB4S6mggnvKfHtGT/DA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <script>
    (function () {{
      var labels = {history_labels};
      var scores = {history_scores};
      var canvas = document.getElementById('history-chart');
      if (typeof Chart === 'undefined' || labels.length < 2) {{
        canvas.style.display = 'none';
        return;
      }}
      new Chart(canvas, {{
        type: 'line',
        data: {{ labels: labels, datasets: [{{ label: 'Human Voice Score', data: scores, borderColor: '#7cc7ff', tension: 0.2 }}] }},
        options: {{ scales: {{ y: {{ min: 0, max: 100 }} }}, plugins: {{ legend: {{ display: false }} }} }}
      }});
    }})();
  </script>
</body>
</html>
"""
