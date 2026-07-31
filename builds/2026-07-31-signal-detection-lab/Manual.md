# Manual — Signal Detection Lab

> **Version:** 1.0 (built 2026-07-31)
> **Complexity:** Ambitious Project

---

## What This Is

Signal Detection Lab is an interactive browser trainer for Signal Detection Theory (SDT) — the framework behind d′ (sensitivity), criterion/bias, and ROC/AUC analysis used in recognition-memory, threat-detection, diagnostic-screening, and forensic-judgment research. It's built for two uses at once: as a quick, correct calculator when you need to turn a study's raw hit/false-alarm counts into publication-ready statistics, and as a teaching aid for building intuition about what sensitivity and bias actually mean, with scenarios grounded in forensic and affective neuroscience research paradigms.

---

## Quick Start

1. Open `index.html` directly in any modern browser (double-click the file, or `open index.html` / `start index.html`). No install, build step, or server required.
2. Use the tab bar at the top to switch between **Explainer**, **ROC Explorer**, **Calculator**, and **Scenario Quiz**.
3. On the Explainer tab, drag the white dashed vertical line to move the decision criterion, and use the slider to change d′ — the stats below update live.
4. On the Calculator tab, enter your own hit/miss/false-alarm/correct-rejection counts and click Compute.
5. On the Scenario Quiz tab, read a research scenario, pick a sensitivity bucket and bias direction, and click Check Answer.

---

## How to Use It

### Explainer Tab

Shows the standard 2×2 detection matrix (Hit / Miss / False Alarm / Correct Rejection) and a live Canvas plot of the noise distribution (cyan) and signal distribution (orange) under the equal-variance Gaussian SDT model. Drag anywhere on the plot to move the criterion line; the shaded regions show which area under each curve counts as a "yes" response (green = hits, under the signal curve; red = false alarms, under the noise curve). The d′ slider controls how far apart the two distributions are. All six stats below the plot (d′, criterion c, likelihood-ratio β, hit rate, false-alarm rate, and a plain-English bias label) are recomputed on every interaction.

### ROC Explorer Tab

Traces the full ROC curve for the d′ value currently set on the Explainer tab (both tabs share the same underlying d′, so changing the slider on one updates the other). The dashed diagonal is the chance line (d′ = 0). The white dot marks where the Explainer tab's current criterion sits on the curve. AUC is the closed-form area under the curve (Φ(d′/√2)) — a threshold-free summary of sensitivity that doesn't depend on where the criterion happens to be set.

### Calculator Tab

Enter raw hit/miss/false-alarm/correct-rejection counts from your own data. The "Apply loglinear correction" checkbox (on by default, and recommended) uses the Hautus (1995) correction — adding 0.5 to hits and false alarms and 1 to each condition's total — which prevents undefined (infinite) d′ values when a condition produces exactly 0% or 100% hit/false-alarm rates. Uncheck it only if you specifically want the uncorrected rates. Results include d′, criterion c, likelihood-ratio β, and the nonparametric A′/B″ measures (distribution-free alternatives to d′/c, useful when the equal-variance Gaussian assumption is questionable).

### Scenario Quiz Tab

Presents one of six hand-authored research scenarios (recognition memory, threat detection, eyewitness identification, diagnostic screening, deception judgment, radiological detection) with plausible hit/miss/false-alarm/correct-rejection counts. Pick a sensitivity bucket (poor/weak/moderate/good/excellent) and a bias direction (liberal/neutral/conservative), then click Check Answer — the correct answer is always computed live from the same math used elsewhere in the tool, never hardcoded. Your score (overall and per-scenario) is saved in your browser's `localStorage` and persists across sessions on the same device/browser. Click "Next Scenario" to move on.

**Generate a Practice Scenario:** type a short research context (e.g., "eyewitness identification under stress") and click Generate. With no API key, a deterministic scenario generator produces a new practice case with zero network requests — reproducible for the same context text. With a session-only Anthropic API key entered, Claude Haiku drafts a fresh scenario instead; the key is used only for that one request and is never saved anywhere.

---

## Configuration

No configuration required. The optional Anthropic API key field on the Scenario Quiz tab is session-only — cleared from the input immediately after each request and never written to `localStorage`, a file, or any other persistent storage.

| Setting | Default | Description |
|---------|---------|--------------|
| Loglinear correction (Calculator tab) | On | Recommended for real data; prevents infinite d′ at 0%/100% rates |
| d′ (Explainer/ROC tabs) | 1.50 | Starting distribution separation; adjustable via slider from 0 to 4 |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Calculator shows "Error" for all results | Hits + Misses is 0, or False Alarms + Correct Rejections is 0 (a condition with no trials) | Enter at least one trial for both the signal-present and signal-absent conditions |
| Quiz score resets unexpectedly | Browser cleared `localStorage`, or the tool was opened in a private/incognito window | Score persistence is tied to the browser profile and origin; use the same browser/profile each time |
| "Generate Scenario" says the AI request failed | No internet access, an invalid API key, or the Anthropic API is temporarily unavailable | The tool automatically falls back to the deterministic generator — no action needed unless you specifically want the AI-authored version |
| Dragging the criterion line does nothing | Clicked outside the canvas boundaries | Click and drag within the plot area itself |

---

## Known Limitations

- Only the equal-variance Gaussian SDT model is implemented (see `FutureFeatures.md` for the unequal-variance extension).
- The criterion control on the Explainer tab responds to mouse input only, not touch or keyboard.
- Quiz progress is stored per-browser via `localStorage`; it does not sync across devices or browsers.
