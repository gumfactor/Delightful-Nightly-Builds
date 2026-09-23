# Manual — Pooling Lab

> **Version:** 1.0 (built 2026-09-23)
> **Complexity:** Ambitious Project

---

## What This Is

Pooling Lab is a browser-based teaching tool for the core intuition behind multilevel/mixed-effects models: when you have data nested in groups (trials within participants, participants within sites, students within classes), how much should you trust each group's own raw average versus pulling it toward the overall average? The tool simulates nested data live and shows, side by side, what three different strategies — ignoring group structure entirely (complete pooling), trusting every group's raw mean fully (no pooling), and the compromise a real mixed-effects model actually uses (partial pooling / shrinkage) — produce for the exact same data. Dragging the between-group and within-group variance sliders shows, in real time, why small-sample groups get pulled harder toward the grand mean than large-sample groups.

---

## Quick Start

1. Open `index.html` in any modern browser (double-click it, or drag it into a browser window — no server or install required).
2. The page loads with a "one small group among large" sample-size profile already selected, so the shrinkage effect is visible immediately in the chart and table.
3. Drag the **τ (between-group SD)** and **σ (within-group SD)** sliders and watch the True ICC readout and the chart's partial-pooling markers move live.
4. Click **Regenerate Data** to draw a brand-new random sample (using the current seed, profile, and slider values as the new "true" generating parameters).
5. Try the 8-question quiz below the chart — three of the questions are generated fresh from whatever is currently on screen.

---

## How to Use It

### Simulation Controls

- **Random seed** — any integer. The same seed with the same profile and τ/σ always regenerates the identical dataset (useful for demonstrating something to students reproducibly).
- **Group sample-size profile** — three presets: equal-sized groups, one small group among large ones, or one large group among small ones. This is the single most important control for seeing shrinkage differ by group size.
- **τ (between-group SD) slider** — how much true group means vary around the grand mean. Dragging this updates the chart, the True ICC, and every partial-pooling estimate immediately, without drawing new random data — it lets you see the effect of *assuming* a different amount of between-group variance on the same sample.
- **σ (within-group SD) slider** — how noisy each individual observation is around its own group's true mean. Same live-update behavior as τ.
- **Regenerate Data** — draws a brand-new random sample from scratch, using the current seed/profile/τ/σ as the generating truth, and also refreshes the quiz.

### Results

- **True ICC** — the intraclass correlation implied by the current τ/σ slider values (`τ² / (τ² + σ²)`), computed instantly, no regeneration needed.
- **Empirical ICC** — the ICC estimated from the actual sample currently on screen (via a one-way ANOVA variance decomposition). This only changes when you click Regenerate Data, since it's a property of the drawn sample, not of the sliders.
- **Grand mean** — the complete-pooling estimate: the plain average of every observation in the current sample, ignoring group membership.
- **Chart** — one column per group. The dashed line is the complete-pooling estimate (same for every group). The hollow marker is each group's own no-pooling raw mean. The filled marker is the partial-pooling (shrinkage) estimate, connected to the raw mean by a line so you can see how far it moved and in which direction.
- **Table** — the same numbers as the chart, plus each group's shrinkage weight (0 = fully shrunk to the grand mean, 1 = fully trusts its own raw mean).

### Explain This

Optional. If you paste your own Anthropic API key into the password field, clicking "Explain These Results" sends the current simulation's numbers (group sizes, τ, σ, ICC, shrinkage weights — no personal data) directly from your browser to the Anthropic API and shows a short plain-English explanation from Claude. The key is never stored (not in `localStorage`, not sent anywhere except directly to Anthropic) and disappears when you close or reload the page. With no key entered, a deterministic explanation built from the same numbers is shown instead, and no network request is ever made.

### Quiz

Eight questions: five are fixed conceptual checks (shrinkage limits, ICC interpretation, random intercepts vs. fixed effects), and three are generated fresh from whatever data is currently loaded (e.g. "which group is shrinking the least right now?"). Click an answer to see it marked correct or incorrect immediately; the score updates live. Clicking "Regenerate Data" resets the quiz and rebuilds the three dynamic questions against the new sample.

---

## Configuration

No configuration required. The optional Anthropic API key is entered per-session in the browser and is never persisted.

| Setting | Default | Description |
|---------|---------|-------------|
| Seed | 42 | Starting random seed |
| Profile | One small group (n=3) among large (n=30) | Starting sample-size profile |
| τ (between-group SD) | 2.0 | Starting between-group variability |
| σ (within-group SD) | 3.0 | Starting within-group noise |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Chart looks empty or blank | Browser window very narrow before first paint | Resize the window or reload; the chart redraws on every resize event |
| "Explain These Results" just shows the deterministic text even with a key entered | Network request failed (bad key, no internet, or the API returned an error) | Check the key is correct; the fallback text is always accurate, just not AI-polished |
| Quiz score seems "stuck" after Regenerate Data | This is intentional — regenerating resets the score to 0/8 along with the new dynamic questions | Answer the fresh set of questions again |

---

## Known Limitations

- Only a single level of nesting is modeled (observations within groups) — no crossed or multiple-level random effects.
- The τ/σ sliders can be moved away from the values that actually generated the current sample; this is deliberate (it isolates the shrinkage formula's behavior from the random draw) but means the "True ICC" readout can temporarily disagree with what a real fit to the visible sample would estimate until you click Regenerate Data.
- No file upload or import of the user's own real data — this is a simulation/teaching tool, not an analysis pipeline for real datasets.
