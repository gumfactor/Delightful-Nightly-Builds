# Manual — EDGAR Lens

> **Version:** 1.0 (built 2026-08-28)
> **Complexity:** Ambitious Project

---

## What This Is

EDGAR Lens pulls the real, filed financial statement history (revenue, net income, operating income, assets, liabilities, equity, cash) for a watchlist of public companies directly from the SEC's free EDGAR XBRL API, stores it locally, and surfaces the specific years where a company's fundamentals genuinely deteriorated — a revenue decline, margin compression, a leverage spike, negative equity, or a swing from profit to loss — using fixed, deterministic thresholds rather than an AI guess. It renders as a dark-mode dashboard you open directly in a browser, no server required.

---

## Quick Start

1. `cd builds/2026-08-28-edgar-lens`
2. `python3 main.py sync --tickers AAPL,MSFT,GOOGL` (any comma-separated tickers you want to track)
3. `python3 main.py render` — writes `dashboard.html`
4. Open `dashboard.html` in your browser
5. Re-run `sync` any time to refresh — it's safe to run repeatedly, it upserts rather than duplicates

---

## How to Use It

### `sync --tickers TICK1,TICK2,...`

Resolves each ticker to its SEC CIK (cached locally after the first lookup) and fetches its full filed financial history from `data.sec.gov`. Only annual (10-K, full fiscal year) facts are used. Re-running `sync` on a ticker you've already synced is safe — it always reflects the latest values SEC has on file (e.g. after a restatement), never duplicates a fiscal year.

By default this uses a generic placeholder `User-Agent` header. SEC's fair-access policy asks API clients to self-identify. Set your own before relying on this daily:

```bash
python3 main.py sync --tickers AAPL --user-agent "YourApp/1.0 (you@example.com)"
# or once, for the session:
export EDGAR_USER_AGENT="YourApp/1.0 (you@example.com)"
```

### `list`

Shows every ticker you've synced, its CIK, and the fiscal-year range on file.

### `show TICKER`

Terminal table of one company's yearly revenue, net income, net margin, debt-to-equity, and revenue YoY growth.

### `flags`

Terminal list of every anomaly flagged across every tracked company, most useful for a quick daily scan.

### `render [--out dashboard.html] [--ai]`

Builds the HTML dashboard: a hero-stats summary, a latest-fiscal-year comparison table across all tracked companies, a per-company multi-year trend chart (falls back to a plain data table if the Chart.js CDN is unreachable), and an Anomalies panel listing every flagged company-year.

Add `--ai` to have Claude Haiku write a one-sentence plain-English note for each flagged anomaly (requires `ANTHROPIC_API_KEY` in your environment; only the already-computed numbers are ever sent, never raw filing text). Without `--ai`, or with no key set, every anomaly still gets a clear deterministic-template sentence — the dashboard is always complete either way.

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # optional
python3 main.py render --ai
```

---

## What Counts as an Anomaly

| Type | Trigger |
|------|---------|
| Revenue decline | Revenue fell 10% or more year-over-year |
| Margin compression | Net margin dropped 5 percentage points or more year-over-year |
| Leverage spike | Debt-to-equity rose 0.5x or more year-over-year |
| Negative equity | Stockholders' equity is zero or negative |
| Swing to loss | Net income went from ≥$0 to negative year-over-year |

Every threshold is a fixed constant in `src/metrics.py` — not tuned per company, not AI-guessed.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--db` | `edgar_lens.db` | SQLite database path (global flag, before the subcommand) |
| `--user-agent` (sync) | generic placeholder | SEC-compliant User-Agent header |
| `EDGAR_USER_AGENT` (env) | — | Alternative to `--user-agent` |
| `--out` (render) | `dashboard.html` | Output HTML file path |
| `--ai` (render) | off | Use Claude Haiku for anomaly narratives |
| `ANTHROPIC_API_KEY` (env) | — | Required only when using `--ai` |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `sync` prints "not found in SEC ticker index" | Ticker typo, or an OTC/foreign ticker not in SEC's US-listed index | Double-check the ticker on SEC EDGAR's full-text search |
| `sync` reports "no annual 10-K facts found" | Company files IFRS/foreign-private-issuer statements (different taxonomy), or is too new to have a 10-K on file | Not supported in this version — see FutureFeatures.md |
| Chart doesn't render, table shown instead | Chart.js CDN (`cdnjs.cloudflare.com`) is unreachable from your network | Expected fallback behavior — the underlying numbers are all still shown in the table |
| `render --ai` shows only deterministic sentences | `ANTHROPIC_API_KEY` not set, or the API call failed | Set the key, or check your network — the dashboard remains fully usable either way |

---

## Known Limitations

- Annual (10-K) figures only — no quarterly (10-Q) trend
- US-GAAP filers only; IFRS-taxonomy foreign private issuers are not supported
- 10-K/A amendments are treated the same as an original 10-K (latest `filed` date wins) rather than specially flagged as a restatement
- The tag-resolution fallback list covers the common cases but not every possible US-GAAP tag variant a filer might use — a company using an unlisted tag for a concept will show that field as blank rather than crashing
