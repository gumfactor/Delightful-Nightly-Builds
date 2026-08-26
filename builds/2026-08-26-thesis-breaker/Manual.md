# Manual — Thesis Breaker

> **Version:** 1.0 (built 2026-08-26)
> **Complexity:** Ambitious

---

## What This Is

Thesis Breaker takes an investment thesis you've written for a stock and argues back at it. It fetches real fundamentals for the ticker (valuation, growth, margins, debt, insider activity), runs a deterministic 5-category bear-case rule engine against both the data and your thesis text, and scores the result from 3 fixed critic personas — Value Skeptic, Macro Bear, and Governance Hawk. Every run is saved, so you can re-check the same thesis as new quarters of data arrive and watch the bear case strengthen or weaken. The AI layer (optional, off by default) only ever rephrases what the rule engine already found — it can never add a new fact or number.

---

## Quick Start

1. `cd` into this folder and install the one dependency: `pip install -r requirements.txt`
2. Run the bundled demo first — no network or API key needed: `python3 main.py demo`
3. Open the generated `report.html` in a browser
4. When ready to check a real ticker: `python3 main.py check AAPL --thesis "Bullish because ..."`
5. Open the newly written `report.html` (or pass `--out somefile.html` to name it)

---

## How to Use It

### `check TICKER --thesis "..."` — the main command

Fetches live data for `TICKER` via `yfinance` and stress-tests the thesis text you pass with `--thesis`. Writes `report.html` (or the path given by `--out`) and saves the run to `thesisbreaker.db` (or the path given by `--db`).

```
python3 main.py check AAPL --thesis "Bullish on AI-driven revenue growth and margin expansion."
```

Add `--ai-polish` to have Claude Haiku rewrite each persona's findings into more natural prose. Requires `ANTHROPIC_API_KEY` to be set in your environment — if it isn't set, or the call fails for any reason, the deterministic text is used instead and the run still completes normally.

### `demo` — try it with no network or API key

Runs the identical pipeline against a bundled, hand-crafted fixture (`fixtures/sample_aapl_fetch.json`) instead of a live fetch. Useful for seeing the tool work immediately, or when you don't have network access to Yahoo Finance right now.

```
python3 main.py demo
python3 main.py demo --thesis "Custom thesis text to test against the same fixture data"
```

### `history TICKER` — see how the bear case has evolved

```
python3 main.py history AAPL
```
Prints every saved check for that ticker with its timestamp and overall score, oldest first.

### `render --id ID` — regenerate a report from a saved run

```
python3 main.py render --id 3 --out old_check.html
```
Rebuilds the HTML report for any past check without re-fetching data.

### `list` — see everything saved across all tickers

```
python3 main.py list
```

---

## Reading the Report

- **Overall bear-case score** (0–100): the average of the 3 personas' scores. 0 means nothing weighted for any persona triggered; 100 means everything did.
- **Persona cards**: each persona only weighs the checks relevant to its lens (see `PRD.md` → Data Structure for the exact weights). A card can be tagged "deterministic" (the rule-engine template) or "AI-polished" (Haiku rewrote it, `--ai-polish` was used, and the call succeeded).
- **Triggered-Checklist Matrix**: every one of the 5 categories, with a `triggered` / `clear` / `n/a` badge. `n/a` means the underlying data field wasn't available for this ticker — it is never silently treated as "clear."
- **Real Data Summary** and **Insider Transactions**: the actual fetched numbers the critique is based on, so you can check the engine's math yourself.
- **Bear-Case Score Over Time**: appears once you've run 2 or more checks for the same ticker.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--db` | `thesisbreaker.db` (current directory) | SQLite file where every check is saved |
| `--out` | `report.html` | Path the HTML report is written to |
| `--ai-polish` | off | Send the deterministic findings to Claude Haiku for a narrative rewrite |
| `ANTHROPIC_API_KEY` (env var) | unset | Required for `--ai-polish` to do anything; silently falls back to deterministic text otherwise |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `ModuleNotFoundError: No module named 'yfinance'` | Dependency not installed | `pip install -r requirements.txt` |
| `check` runs but every field in the report says "n/a" | Ticker not recognized by Yahoo Finance, or you're offline | Try a well-known large-cap ticker first (e.g. `AAPL`) to confirm the setup works, or run `demo` |
| `--ai-polish` never shows "AI-polished" on any card | `ANTHROPIC_API_KEY` isn't set, or the network call failed | Confirm the env var is set in the shell you're running from; the tool always falls back safely, it never errors |
| `render --id N` says "No saved check with id N" | That id doesn't exist in the `--db` file you pointed at | Run `list` first to see valid ids |

---

## Known Limitations

- The "sector-average P/E" comparison used by Valuation Stretch is a static, hand-set reference table (see `src/rules.py`), not a live-fetched sector average — a genuinely different sector average API would need a second data source.
- Insider transaction data comes from `yfinance`'s own scrape of Yahoo Finance's insider-trading page, not a direct SEC EDGAR Form 4 parse — usually the same underlying filings, occasionally less complete for smaller-cap names.
- Narrative Fragility's "contradicted claim" check for the debt keyword bucket shares a single rule (`margin_debt_risk`) with the margin check, so a thesis claiming "low debt" can be flagged as contradicted by a margin-driven trigger even when the debt number itself is fine. Splitting margin and debt into two separate rule categories would fix this (see `FutureFeatures.md`).
- One ticker per run — no portfolio-wide batch mode yet.
- No brokerage or trade-execution integration; this tool only produces a written critique.
