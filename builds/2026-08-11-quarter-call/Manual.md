# Manual — Quarter Call

> **Version:** 1.0 (built 2026-08-11)
> **Complexity:** Ambitious Project

---

## What This Is

Quarter Call is a browser game that shows you a real historical stock price chart — six months up to a fixed decision date — and asks you to call whether the price went up, down, or stayed flat (±5%) over the following quarter. Every round uses genuine daily closing prices from Yahoo Finance for a well-known company, and every decision date is years in the past, so the outcome is always fully settled by the time you play. It's a pattern-recognition trainer, not a forecasting tool: the point is to get a sharper, humbler sense of how (un)predictable a single quarter really is, not to build a trading edge.

---

## Quick Start

1. `cd builds/2026-08-11-quarter-call`
2. `pip install -r requirements.txt`
3. `python3 fetch_data.py` — this fetches real historical data for 48 curated tickers from Yahoo Finance and writes `data/rounds-data.js`. Takes under a minute; prints each round's outcome as it goes.
4. Open `index.html` directly in any browser (double-click it, or `file://` the path) — no server, no build step.
5. Pick **Practice** (random rounds) or **Daily Challenge** (5 rounds, same for everyone that day, one playthrough per UTC day) and start guessing.

---

## How to Use It

### Practice Mode

Shows one round at a time from the full 48-round bank in a shuffled order that never repeats a round until the whole bank has been seen once. Guess Up, Down, or Flat, then see the real outcome — the chart extends into the actual forward quarter, colored green (up) or red (down), alongside the exact percent move and an optional AI note (see below). Click "Next round" to continue.

### Daily Challenge

A fixed set of 5 rounds, chosen deterministically by the current UTC date — every player who opens Quarter Call on the same day gets the same 5 rounds in the same order, so results are comparable. You get one playthrough per UTC day; returning later the same day shows your completed summary and a shareable emoji result (🟩 correct / 🟥 wrong) instead of new rounds. A new set unlocks the next UTC day.

**Note:** progress within an in-progress Daily Challenge isn't saved across a reload — reloading mid-run restarts that day's same 5 rounds from the beginning rather than resuming; completion is only recorded once all 5 are answered in one sitting.

### Sector & Metrics Context

Each round shows the company's sector and industry, plus two numbers computed directly from the same chart you're looking at: the trailing 6-month return and the annualized volatility. These are never a separate, possibly-stale data source — they're recalculated from the exact closes drawn on screen.

### Optional AI Historical Context

On the reveal screen, paste an Anthropic API key (session-only — typed into memory, never written to disk, never sent anywhere except directly to Anthropic's API from your browser) to get a 2-3 sentence plain-English note on the round's historical context. Leave it blank and you'll get a deterministic template note instead — the game is fully playable with zero network calls if you never enter a key.

### Stats

Streak, best streak, overall accuracy, and a per-sector accuracy breakdown persist in your browser's `localStorage` across sessions. Nothing is sent anywhere; clearing your browser's site data resets them.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| Anthropic API key | none | Session-only text field on the reveal panel; enables the AI historical-context note. Never persisted. |
| `FLAT_BAND_PCT` (in `fetch_data.py`) | 5.0 | The ± percent-change band classified as "flat" rather than up/down. Change and re-run `fetch_data.py` to reclassify all 48 rounds. |
| `CURATED_ROUNDS` (in `fetch_data.py`) | 48 hand-picked (ticker, date) pairs | Edit this list and re-run `fetch_data.py` to change which companies/periods appear in the game. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|---------------|-----|
| "No data yet" banner never goes away after running `fetch_data.py` | The script failed to fetch enough tickers (e.g. no internet connection) and exited with an error before writing the file | Re-run `python3 fetch_data.py` with a working internet connection; check the printed per-ticker log for `!` failure lines |
| AI note always shows the fallback template even with a key entered | Invalid or expired API key, or no internet connection | Check the key is correct; the game always degrades gracefully to the fallback on any API error, so gameplay is unaffected either way |
| Daily Challenge shows different rounds on different days than expected | This is by design — the round set is seeded by the current UTC date, so it changes at UTC midnight, not local midnight | No fix needed; this matches the "same challenge for everyone that day" design |
| Stats reset unexpectedly | Browser cleared `localStorage` (private/incognito window, manual site-data clear, or a different browser/profile) | Stats are local to one browser profile by design; there is no cloud sync |

---

## Known Limitations

- Fundamentals-at-decision-date (P/E, market cap as of that historical date) are not shown — only chart-derived technical metrics, which are always internally consistent with what's on screen.
- The 48-round bank is fixed by `fetch_data.py`'s curated ticker list; there's no in-app way to add tickers without editing the script and re-running it.
- Daily Challenge progress isn't saved mid-run (see above) — a reload restarts the current day's 5 rounds from the top.
- No multiplayer or cloud leaderboard — this is a single-player, fully local tool by design.
