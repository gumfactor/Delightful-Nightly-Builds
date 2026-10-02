# Manual — Replication Lab

## Run it
Open `index.html` in a browser. No server, install or network needed. Works on a phone.

## Use it
1. Pick a lab from the tab strip: Power, Peeking, Many outcomes, Winner's curse, Bayes.
2. Set the sliders.
3. In the first four labs, move the **Predict first** slider to your guess and press **Lock in guess and run**. The simulation runs in the browser and shows how far off you were. The footer keeps your average miss across all predictions.
4. **New random sample** reruns with a fresh seed. The same seed always reproduces the same numbers; type a seed in the footer to share an exact result.
5. The Bayes lab updates live as you move the sliders.

## What each lab shows
- **Power:** share of 2,000 identical studies reaching p < alpha (red bars), sample size needed for 80% power, and the chance a significant result is true given the share of true hypotheses.
- **Peeking:** no effect exists; the line shows how false positives accumulate when you test after every batch and stop at the first hit.
- **Many outcomes:** no effect exists; the chance that any of k outcomes is significant, with outcome correlation and Bonferroni or Holm correction.
- **Winner's curse:** observed effect sizes across 3,000 studies; the published average is the mean of the significant ones.
- **Bayes:** posterior of a success rate with prior choices, 95% equal-tailed credible interval, probability inside a practical-equivalence zone, Bayes factor against 50% with a flat alternative.

## Tests
```
npm install
npx playwright test
```
Chromium is read from `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`; set `CHROMIUM_PATH` to override.

## Notes
- Power uses a two-sample pooled t-test with equal n and normal data. "Analytic power" is a normal approximation with the exact t critical value.
- Simulations run on the main thread and take well under a second at default settings.
