"""Assemble a self-contained HTML report from a list of TickerData."""

from __future__ import annotations

from datetime import datetime, timezone

from .fetcher import (
    TickerData,
    format_change,
    format_market_cap,
    format_pe,
    format_price,
    format_volume,
    format_52w_range,
)
from .charts import make_sparkline


_CSS = """
:root {
  --bg: #0f172a;
  --surface: #1e293b;
  --surface2: #263044;
  --border: #334155;
  --text: #e2e8f0;
  --muted: #94a3b8;
  --up: #4ade80;
  --down: #f87171;
  --accent: #38bdf8;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --mono: "SF Mono", "Fira Code", monospace;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 14px;
  line-height: 1.5;
  padding: 24px 16px;
}

header {
  margin-bottom: 24px;
}

header h1 {
  font-size: 20px;
  font-weight: 600;
  color: var(--accent);
  margin-bottom: 4px;
}

header .meta {
  color: var(--muted);
  font-size: 12px;
}

.summary {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.summary-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 20px;
  min-width: 120px;
}

.summary-card .label {
  font-size: 11px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.summary-card .value {
  font-size: 22px;
  font-weight: 700;
}

.summary-card .value.up { color: var(--up); }
.summary-card .value.down { color: var(--down); }

.table-wrap {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid var(--border);
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

thead th {
  background: var(--surface);
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 10px 14px;
  text-align: left;
  white-space: nowrap;
  border-bottom: 1px solid var(--border);
}

thead th.num { text-align: right; }

tbody tr {
  border-bottom: 1px solid var(--border);
  transition: background 0.1s;
}

tbody tr:last-child { border-bottom: none; }

tbody tr:hover { background: var(--surface2); }

tbody td {
  padding: 10px 14px;
  white-space: nowrap;
  vertical-align: middle;
}

tbody td.num { text-align: right; font-family: var(--mono); font-size: 12px; }

.ticker { font-weight: 600; color: var(--accent); font-family: var(--mono); }
.name { color: var(--muted); font-size: 12px; margin-top: 2px; }
.price { font-weight: 600; font-family: var(--mono); }
.change.up { color: var(--up); font-family: var(--mono); }
.change.down { color: var(--down); font-family: var(--mono); }
.change.flat { color: var(--muted); font-family: var(--mono); }
.error-row td { color: var(--muted); font-style: italic; }
.error-msg { font-size: 11px; color: var(--down); }

footer {
  margin-top: 24px;
  font-size: 11px;
  color: var(--muted);
  text-align: center;
}

@media (max-width: 640px) {
  .summary { gap: 12px; }
  .summary-card { padding: 10px 14px; min-width: 90px; }
  .summary-card .value { font-size: 18px; }
  table { font-size: 12px; }
  thead th, tbody td { padding: 8px 10px; }
}
"""


def _change_class(change_pct: float | None) -> str:
    if change_pct is None:
        return "flat"
    if change_pct > 0:
        return "up"
    if change_pct < 0:
        return "down"
    return "flat"


def _build_summary(tickers: list[TickerData]) -> str:
    total = len(tickers)
    ok = [t for t in tickers if t.error is None]
    gainers = sum(1 for t in ok if t.change_pct is not None and t.change_pct > 0)
    losers = sum(1 for t in ok if t.change_pct is not None and t.change_pct < 0)

    cards = [
        ("Tickers", str(total), ""),
        ("Gainers", str(gainers), "up"),
        ("Losers", str(losers), "down"),
    ]
    html = '<div class="summary">'
    for label, value, css_class in cards:
        cls = f' class="value {css_class}"' if css_class else ' class="value"'
        html += (
            f'<div class="summary-card">'
            f'<div class="label">{label}</div>'
            f'<div{cls}>{value}</div>'
            f"</div>"
        )
    html += "</div>"
    return html


def _build_row(ticker: TickerData) -> str:
    if ticker.error:
        return (
            f'<tr class="error-row">'
            f'<td><span class="ticker">{ticker.symbol}</span>'
            f'<div class="name">{ticker.name}</div></td>'
            f'<td colspan="7"><span class="error-msg">Fetch error: {ticker.error}</span></td>'
            f"</tr>"
        )

    sparkline = make_sparkline(ticker.history)
    price_str = format_price(ticker.price, ticker.currency)
    change_str = format_change(ticker.change_pct)
    change_cls = _change_class(ticker.change_pct)
    range_str = format_52w_range(ticker.week52_low, ticker.week52_high)
    pe_str = format_pe(ticker.pe_ratio)
    cap_str = format_market_cap(ticker.market_cap)
    vol_str = format_volume(ticker.volume)

    return (
        f"<tr>"
        f'<td><span class="ticker">{ticker.symbol}</span>'
        f'<div class="name">{ticker.name}</div></td>'
        f'<td class="num price">{price_str}</td>'
        f'<td class="num"><span class="change {change_cls}">{change_str}</span></td>'
        f'<td class="num">{range_str}</td>'
        f'<td class="num">{pe_str}</td>'
        f'<td class="num">{cap_str}</td>'
        f'<td class="num">{vol_str}</td>'
        f'<td>{sparkline}</td>'
        f"</tr>"
    )


def generate_report(tickers: list[TickerData], generated_at: datetime | None = None) -> str:
    """
    Produce a complete, self-contained HTML string.
    generated_at defaults to now (UTC) if not provided.
    """
    if generated_at is None:
        generated_at = datetime.now(timezone.utc)

    ts_display = generated_at.strftime("%Y-%m-%d %H:%M UTC")
    ts_iso = generated_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    summary_html = _build_summary(tickers)
    rows_html = "\n".join(_build_row(t) for t in tickers)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Portfolio Snapshot — {ts_display}</title>
  <style>{_CSS}</style>
</head>
<body>
  <header>
    <h1>Portfolio Snapshot</h1>
    <p class="meta">Generated <time datetime="{ts_iso}">{ts_display}</time> &nbsp;&middot;&nbsp; Data via Yahoo Finance</p>
  </header>

  {summary_html}

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Symbol</th>
          <th class="num">Price</th>
          <th class="num">1D Change</th>
          <th class="num">52W Range</th>
          <th class="num">P/E</th>
          <th class="num">Mkt Cap</th>
          <th class="num">Volume</th>
          <th>3M Trend</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>

  <footer>
    Data sourced from Yahoo Finance via yfinance. Prices may be delayed 15–20 minutes.
    For personal research only — not financial advice.
  </footer>
</body>
</html>"""
