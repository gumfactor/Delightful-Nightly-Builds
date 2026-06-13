"""
Pure rendering functions. Takes a list of processed ticker dicts and returns strings.
No I/O, no network calls.
"""

from datetime import datetime, timezone
from typing import Optional


def _change_class(change_pct: Optional[float]) -> str:
    """Return CSS class name based on sign of daily change."""
    if change_pct is None:
        return "neutral"
    if change_pct > 0:
        return "positive"
    if change_pct < 0:
        return "negative"
    return "neutral"


def _progress_bar_html(position: Optional[float]) -> str:
    """Render a mini 52-week range progress bar as inline HTML."""
    if position is None:
        return '<span class="na">N/A</span>'
    pct = round(position, 1)
    return (
        f'<div class="range-bar" title="{pct}% of 52-week range">'
        f'<div class="range-fill" style="width:{pct}%"></div>'
        f'</div>'
        f'<span class="range-pct">{pct}%</span>'
    )


def _build_summary(tickers: list[dict], generated_at: str) -> str:
    """Build the summary header HTML block."""
    gainers = sum(1 for t in tickers if t.get("change_pct") is not None and t["change_pct"] > 0)
    losers = sum(1 for t in tickers if t.get("change_pct") is not None and t["change_pct"] < 0)
    flat = sum(1 for t in tickers if t.get("change_pct") is not None and t["change_pct"] == 0)
    failed = sum(1 for t in tickers if t.get("price") is None)
    total = len(tickers)

    return f"""
    <div class="summary">
      <div class="summary-item"><span class="summary-label">Tickers</span><span class="summary-value">{total}</span></div>
      <div class="summary-item positive"><span class="summary-label">Gainers</span><span class="summary-value">{gainers}</span></div>
      <div class="summary-item negative"><span class="summary-label">Losers</span><span class="summary-value">{losers}</span></div>
      <div class="summary-item neutral"><span class="summary-label">Flat</span><span class="summary-value">{flat}</span></div>
      {"" if not failed else f'<div class="summary-item error"><span class="summary-label">Failed</span><span class="summary-value">{failed}</span></div>'}
      <div class="summary-item timestamp"><span class="summary-label">Updated</span><span class="summary-value">{generated_at}</span></div>
    </div>"""


def _build_table_rows(tickers: list[dict]) -> str:
    """Build the HTML table rows for each ticker."""
    rows = []
    for t in tickers:
        css = _change_class(t.get("change_pct"))
        range_html = _progress_bar_html(t.get("week52_position"))
        notes_html = (
            f'<span class="notes" title="{t["notes"]}">{t["notes"][:40]}</span>'
            if t.get("notes") else ""
        )
        row = f"""
      <tr class="{css}">
        <td class="col-symbol"><strong>{t["symbol"]}</strong><br><span class="label">{t["label"]}</span></td>
        <td class="col-name">{t["name"]}{notes_html}</td>
        <td class="col-price">{t["fmt_price"]}</td>
        <td class="col-change change-{css}">
          <span class="change-pct">{t["fmt_change_pct"]}</span><br>
          <span class="change-abs">{t["fmt_change_abs"]}</span>
        </td>
        <td class="col-range">
          <div class="range-row">
            <span class="range-bound">{t["fmt_52low"]}</span>
            {range_html}
            <span class="range-bound">{t["fmt_52high"]}</span>
          </div>
        </td>
        <td class="col-volume">{t["fmt_volume"]}</td>
        <td class="col-cap">{t["fmt_market_cap"]}</td>
        <td class="col-pe">{t["fmt_pe"]}</td>
        <td class="col-target">{t["fmt_target"]}</td>
      </tr>"""
        rows.append(row)
    return "\n".join(rows)


_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0f1117;
  --surface: #1a1d27;
  --surface2: #252836;
  --border: #2e3347;
  --text: #e2e8f0;
  --text-muted: #94a3b8;
  --positive: #22c55e;
  --negative: #ef4444;
  --neutral: #94a3b8;
  --accent: #6366f1;
  --radius: 8px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

@media (prefers-color-scheme: light) {
  :root {
    --bg: #f8fafc;
    --surface: #ffffff;
    --surface2: #f1f5f9;
    --border: #e2e8f0;
    --text: #0f172a;
    --text-muted: #64748b;
  }
}

body { background: var(--bg); color: var(--text); font-family: var(--font); font-size: 14px; line-height: 1.5; padding: 24px 16px; }

h1 { font-size: 20px; font-weight: 600; margin-bottom: 4px; }
.subtitle { color: var(--text-muted); font-size: 13px; margin-bottom: 20px; }

.summary {
  display: flex; flex-wrap: wrap; gap: 12px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px 20px; margin-bottom: 20px;
}
.summary-item { display: flex; flex-direction: column; min-width: 80px; }
.summary-item.positive .summary-value { color: var(--positive); }
.summary-item.negative .summary-value { color: var(--negative); }
.summary-item.error .summary-value { color: var(--negative); }
.summary-item.timestamp { margin-left: auto; text-align: right; }
.summary-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
.summary-value { font-size: 20px; font-weight: 600; }
.summary-item.timestamp .summary-value { font-size: 13px; font-weight: 400; }

.table-wrapper { overflow-x: auto; border-radius: var(--radius); border: 1px solid var(--border); }
table { width: 100%; border-collapse: collapse; background: var(--surface); }
thead th { background: var(--surface2); color: var(--text-muted); font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; padding: 10px 14px; text-align: right; white-space: nowrap; }
thead th:first-child, thead th:nth-child(2) { text-align: left; }
tbody tr { border-top: 1px solid var(--border); transition: background 0.1s; }
tbody tr:hover { background: var(--surface2); }
tbody td { padding: 12px 14px; text-align: right; vertical-align: middle; }
tbody td:first-child, tbody td:nth-child(2) { text-align: left; }

.col-symbol strong { font-size: 15px; }
.label { font-size: 11px; color: var(--text-muted); }
.col-name { color: var(--text-muted); font-size: 12px; max-width: 180px; }
.notes { display: block; font-style: italic; color: var(--text-muted); font-size: 11px; }
.col-price { font-size: 16px; font-weight: 600; }

.change-positive { color: var(--positive); }
.change-negative { color: var(--negative); }
.change-neutral { color: var(--neutral); }
.change-pct { font-size: 14px; font-weight: 600; }
.change-abs { font-size: 11px; opacity: 0.8; }

.range-row { display: flex; align-items: center; gap: 6px; justify-content: flex-end; }
.range-bound { font-size: 11px; color: var(--text-muted); white-space: nowrap; }
.range-bar { width: 80px; height: 6px; background: var(--surface2); border-radius: 3px; overflow: hidden; flex-shrink: 0; }
.range-fill { height: 100%; background: var(--accent); border-radius: 3px; }
.range-pct { font-size: 11px; color: var(--text-muted); min-width: 36px; text-align: right; }
.na { color: var(--text-muted); font-size: 12px; }

@media (max-width: 768px) {
  .col-name, .col-range, .col-target { display: none; }
  body { padding: 16px 8px; }
}
"""


def render_html(tickers: list[dict], title: str = "Investment Watchlist") -> str:
    """
    Render a complete self-contained HTML dashboard from processed ticker records.

    Returns a full HTML string with embedded CSS. No external dependencies.
    """
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    summary_html = _build_summary(tickers, generated_at)
    rows_html = _build_table_rows(tickers)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>{_CSS}</style>
</head>
<body>
  <h1>{title}</h1>
  <p class="subtitle">Live data from Yahoo Finance &mdash; {generated_at}</p>
  {summary_html}
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Name</th>
          <th>Price</th>
          <th>Day Change</th>
          <th>52-Week Range</th>
          <th>Volume</th>
          <th>Mkt Cap</th>
          <th>P/E</th>
          <th>Target</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>
</body>
</html>"""


def render_text(tickers: list[dict]) -> str:
    """
    Render a plain-text table of the watchlist for terminal output.
    """
    lines = []
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"Investment Watchlist — {generated_at}")
    lines.append("=" * 80)
    header = f"{'Symbol':<8} {'Name':<22} {'Price':>10} {'Change':>10} {'Chg%':>8}  {'Mkt Cap':>10}  {'P/E':>7}"
    lines.append(header)
    lines.append("-" * 80)
    for t in tickers:
        name = (t["name"] or t["label"])[:21]
        row = (
            f"{t['symbol']:<8} {name:<22} {t['fmt_price']:>10} "
            f"{t['fmt_change_abs']:>10} {t['fmt_change_pct']:>8}  "
            f"{t['fmt_market_cap']:>10}  {t['fmt_pe']:>7}"
        )
        lines.append(row)
    lines.append("=" * 80)
    gainers = sum(1 for t in tickers if t.get("change_pct") is not None and t["change_pct"] > 0)
    losers = sum(1 for t in tickers if t.get("change_pct") is not None and t["change_pct"] < 0)
    lines.append(f"Gainers: {gainers}  |  Losers: {losers}  |  Total: {len(tickers)}")
    return "\n".join(lines)
