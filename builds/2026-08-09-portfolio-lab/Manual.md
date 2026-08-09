# Manual — Portfolio Lab

## What it is

An interactive Modern Portfolio Theory trainer: diversification, the efficient frontier, and the Sharpe ratio, all computed from real historical prices for a fixed 12-asset teaching basket (8 equity sectors plus gold and long-term Treasuries).

## Quick start

1. Install the one dependency (needs internet access):
   ```bash
   pip install -r requirements.txt
   ```
2. Fetch real market data (needs internet access to Yahoo Finance):
   ```bash
   python fetch_data.py
   ```
   This writes `data.js` (used by the browser app) and `data/dataset.json` (a plain-JSON copy, handy if you want to inspect the numbers directly). It prints which tickers it successfully fetched.
3. Open `index.html` directly in any browser — double-click it, or `open index.html` / `xdg-open index.html`. No server, no build step.

If you open `index.html` before running `fetch_data.py`, you'll see an onboarding screen with these same instructions instead of fake data — Portfolio Lab never fabricates market numbers.

## Refreshing the data

Re-run `python fetch_data.py` any time to pull a fresh 3-year window. It overwrites `data.js` unconditionally — there's no accumulated history to lose (this is a teaching tool over the *current* dataset, not a research journal).

Options:
- `--years N` — years of daily history to fetch (default 3)
- `--out PATH` — where to write the generated file (default `./data.js`)

## The five tabs

**Explainer** — Pick any two of the 12 assets and drag the weight slider. The chart traces every possible blend from 100% Asset A to 100% Asset B using their *real* historical covariance. Watch how the curve bows to the left of a straight line between the two assets — that bow is the diversification benefit, and it's bigger the lower the correlation. The readouts compare the real portfolio volatility against a "naive average" (what you'd get with no diversification credit) so the effect is a concrete number, not just a shape.

**Efficient Frontier** — All 12 assets at once. Each gray dot is one randomly-weighted long-only portfolio (click "Resample cloud" for a new batch). The blue curve is the analytical efficient frontier — every portfolio that gets the best possible return for its risk, computed in closed form (not sampled), assuming unrestricted weights including short positions in the wings. It should visibly dominate (sit to the left of) the cloud.

**Sharpe & Risk-Free** — Drag the risk-free rate slider and watch the tangency portfolio (orange dot) slide along the frontier — it's the single portfolio with the best return-per-unit-of-risk for that rate, found via the closed-form tangency formula. The dashed line is the Capital Market Line.

**Correlation Matrix** — A full 12×12 heatmap of real correlations. Blue = moves together, red = moves apart. Click any cell to jump to the Explainer tab with that exact pair preselected.

**Quiz** — Two randomly-weighted two-asset portfolios (fixed 2% risk-free rate); guess which has the better Sharpe ratio. The correct answer is always computed live from the real data, never hardcoded. Your streak and accuracy are saved in your browser (`localStorage`) and survive a reload.

## Optional: AI plain-English explanations

Each of the Explainer and Efficient Frontier tabs has an "Explain this in plain English" button. If you paste an Anthropic API key into the field at the bottom of the page, it calls Claude Haiku directly from your browser to turn the current numbers into a short explanation. The key is kept in memory only for that page session — never saved to disk, never sent anywhere but Anthropic's API. Leave the field empty and you still get an explanation — a deterministic template built from the same real numbers, not a placeholder.

## Running the tests

```bash
python -m pytest tests/ -v          # fetch_data.py — 15 tests, all network calls mocked
npx playwright test                  # math.js + the browser app — 32 tests
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Onboarding screen won't go away after running `fetch_data.py` | The script errored before writing `data.js` | Check the terminal output — it prints which tickers failed and why |
| `fetch_data.py` says "Only N of 12 tickers returned usable data" | Network issue or fewer than 4 tickers succeeded | Check your internet connection; the script needs at least 4 successful tickers to build a meaningful covariance matrix |
| "Explain in plain English" always shows the template, never a real AI response | No API key entered, or the Anthropic call failed | Enter a valid key; check the browser console for the specific error |
| Frontier tab curve looks like it's cut off | Very unusual real-world data (extreme means) can occasionally need the view range widened — this happens automatically when you visit the Sharpe tab, since the chart there dynamically extends the range to keep the tangency point in view | Visit the Sharpe & Risk-Free tab once; the frontier view updates |
