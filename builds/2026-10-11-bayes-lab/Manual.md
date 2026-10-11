# Bayes Lab — Manual

## Run
Open `index.html` in any modern browser (double-click works; no server, build step or network needed). Works on a phone.

## Lessons
1. **Update a belief** — pick a prior (or set Beta α, β), enter your own successes/trials or click +success / +failure / Simulate 10 trials. Shows prior, rescaled likelihood and posterior; posterior mean, 95% HDI, P(θ > 0.5), posterior-predictive for the next 10 trials, and the probability inside an adjustable ROPE.
2. **Base-rate trap** — set prevalence, sensitivity, specificity or choose a scenario (illustrative numbers). The 1,000-dot grid and P(condition | flagged) update live.
3. **Two researchers** — skeptic vs enthusiast priors see the same data; slide the sample size to watch them converge and read how many observations are needed for agreement within 5 points.
4. **Bayes factor vs p-value** — enter successes, trials, null value and the prior under H1. See exact p, BF10, BF01, a verbal label, and a Savage–Dickey check. Use the Lindley preset to see p < .05 coexist with evidence for the null.
5. **Shrinkage** — combine a prior mean/SD with a new estimate and its standard error (any effect-size metric). Shows the posterior, the weight on the new data and the amount of shrinkage.
6. **Calibration quiz** — eight true/false statements, each with a confidence slider (50–100%). Scored with the Brier score; explanations appear after scoring. Attempts are saved in your browser (localStorage); if storage is blocked the quiz still works.

## Notes
- Invalid number entries are outlined in red and the last valid value is used; successes above trials are clamped with a message.
- HDI uses the narrowest-interval search for unimodal Betas; for U-shaped Betas it falls back to the equal-tailed interval.
- Bayes factor labels follow Lee & Wagenmakers (2013).

## Tests
```
cd builds/2026-10-11-bayes-lab
npm install
npx playwright test
```
Tests use Chromium; `playwright.config.js` points at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` — edit `executablePath` (or remove it after `npx playwright install chromium`) on your machine.
