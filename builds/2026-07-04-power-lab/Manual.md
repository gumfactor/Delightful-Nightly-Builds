# Manual — Power Lab

## What it is
A browser tool with four tabs:

1. **Power Explorer** — move sliders for effect size (Cohen's d), sample size per group, alpha, design (two-sample vs. one-sample/paired), and tails; see the sampling distributions overlap, the rejection region shade in, and a power-vs-N curve, all updating live.
2. **Sample Size Calculator** — enter a target power, effect size, alpha, design, and tails; get the required N per group, plus a copy-ready summary sentence for a grant methods section.
3. **Effect Size Converter** — convert Cohen's d ↔ Pearson's r, or a reported t-statistic + N → Cohen's d.
4. **Power Intuition Quiz** — 18 realistic study scenarios; guess the power bucket before the tool reveals the exact computed power. Score and streak are saved in your browser (`localStorage`) and persist across visits.

## How to open it
No build step, no server, no install. Just open `index.html` directly in a browser (double-click it, or `open index.html` / `xdg-open index.html` from a terminal).

The app is intentionally plain HTML/CSS/JS loaded as classic (non-module) `<script>` tags rather than ES modules — Chromium (and other browsers) refuse to load `type="module"` scripts at all when a page is opened via a bare `file://` URL with no local server, so this app avoids that entirely rather than requiring you to run a server just to use a calculator.

## Running the tests
```bash
cd builds/2026-07-04-power-lab
npm install        # one-time, installs @playwright/test
npx playwright test
```
39 tests across 5 spec files, all should pass in well under a minute.

## Accuracy note (read this before using it for a real grant/pre-registration number)
Power and required-N are computed with a **normal approximation** to the noncentral-t distribution — the same approach behind quick textbook power tables. It's accurate to within roughly ±1–3 percentage points of exact values for N ≥ 20 per group. That's good enough for planning, teaching, and a first-pass grant methods paragraph. It is **not** a substitute for exact software (G*Power, R's `pwr` package) when a pre-registration or a reviewer specifically requires exact noncentral-t figures — the in-app note next to the power readout says the same thing.

## Design decisions worth knowing
- **No Chart.js, no CDN.** Both charts (distribution overlap, power curve) are hand-drawn with the native Canvas 2D API. This build's own test run discovered that this session's sandboxed network policy can't reliably load CDN scripts, and the same failure mode was already documented in a prior build (WeatherSong, 2026-07-03). Removing the dependency removes the risk for you too, not just for CI.
- **No AI.** `ANTHROPIC_API_KEY` was checked and confirmed absent from this session's environment before any code was written, so this build doesn't depend on it anywhere — every number on screen is exact, reproducible client-side math.
- **Quiz answers are never hardcoded.** The "correct" power bucket for each of the 18 quiz scenarios is computed live from the exact same `computePower()` function the Explorer tab uses, so the quiz can never silently drift out of sync with the calculator.
