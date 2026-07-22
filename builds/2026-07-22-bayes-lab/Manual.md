# Manual — Bayes Lab

> **Version:** 1.0 (built 2026-07-22)
> **Complexity:** Ambitious

---

## What This Is

Bayes Lab is a browser-based, hands-on trainer for Bayesian inference on proportions — the Beta-Binomial model. Instead of reading about priors and posteriors, you set a prior belief, feed in trial outcomes one at a time (or in a batch), and watch the posterior distribution, its 95% credible interval, and a Bayes factor update live on a chart. A frequentist contrast panel computes the classical answer to the same question from the same data, so you can see directly where the two frameworks agree and where their interpretations diverge. It exists because "develop advanced Bayesian statistical workflows" is a named learning goal that no prior tool in this catalog addressed.

---

## Quick Start

1. Open `index.html` directly in any modern browser (double-click the file, or `open index.html` / `xdg-open index.html`). No install or server needed.
2. Pick a scenario from the dropdown (or choose **Custom** to write your own).
3. Set your prior belief using the **Believed rate** and **Prior confidence** sliders (or switch to **Advanced mode** to type α/β directly).
4. Click **+ Success** / **+ Failure** as trials come in, or enter counts in the batch fields and click **Add batch**.
5. Read the Bayesian and frequentist panels below the chart — they update after every trial.

---

## How to Use It

### Scenarios

Five built-in scenarios pre-fill a description and a threshold/null value (`p0`) relevant to psychology and neuroscience research: Clinical Response Rate, Screening Tool Positive Rate, Manipulation Check Pass Rate, Replication Success Rate, and Custom (fully free-form — edit the description and `p0` directly). Switching scenarios resets the trial history so each scenario starts from a clean slate; the prior itself can still be adjusted afterward.

### Setting a Prior

**Belief mode** (default) asks two plain-language questions: "what rate do you believe is true?" and "how much prior confidence does that represent, in equivalent sample size?" A prior confidence of 2 is very weak (barely more informative than a flat/uniform prior); 50–100 represents strong prior conviction. The tool converts these directly into Beta(α, β) parameters using α = rate × weight, β = (1 − rate) × weight.

**Advanced mode** lets you type α and β directly if you already know the shape you want. Both modes always describe the same underlying prior — switching modes recomputes one from the other, it never resets your prior.

### Adding Trial Data

`+ Success` / `+ Failure` add one trial at a time. The batch fields add many trials in a single step (e.g., entering the full result of a completed study at once). `Undo` removes the most recently added trial (single or batch) and recomputes everything. `Reset trials` clears the trial history but keeps your current prior, so you can replay the same prior against different hypothetical data.

### Reading the Results

- **Bayesian Summary** — posterior mean/mode/SD, the 95% *credible* interval (a direct probability statement: "there is a 95% probability the true rate is in this range, given this prior and this data"), and P(true rate > p0).
- **Bayes Factor** — BF10 and BF01 via the Savage-Dickey density ratio at your chosen `p0`, with a plain-language strength label (Jeffreys / Lee & Wagenmakers scale: anecdotal → moderate → strong → very strong → extreme).
- **Frequentist Contrast** — the same data's MLE point estimate, a 95% Wilson score *confidence* interval (a statement about the long-run behavior of the procedure across repeated samples, not a probability about the true rate), and an exact two-sided binomial test p-value against `p0`.

### Plain-English Interpretation

Paste your own Anthropic API key (never stored, never sent anywhere but `api.anthropic.com` directly from your browser) and click **Generate interpretation** for an AI-written paragraph synthesizing the current numbers. Without a key, a deterministic template produces an equivalent plain-English paragraph from the same numbers — the tool is always fully functional with no key.

---

## Configuration

No configuration file is required. The only optional setting is the Anthropic API key entered directly in the page (session-only; cleared on reload).

| Setting | Default | Description |
|---------|---------|-------------|
| Anthropic API key | (empty) | Optional. When set, `Generate interpretation` calls Claude directly from the browser. When empty, a deterministic template is used instead. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "Generate interpretation" shows an "AI narrative unavailable" message appended to the template | The API key is invalid, rate-limited, or the request failed for another reason | Check the key is correct and has available quota; the template text below the message is still a fully valid summary of the same numbers |
| Posterior mode shows "undefined at this shape" | The posterior Beta(α, β) has α ≤ 1 or β ≤ 1, where the mode is either undefined or at a boundary (0 or 1) rather than a unique interior point | This is mathematically expected for weak/lopsided posteriors (e.g., very few trials); use the posterior mean or credible interval instead |
| Chart shows a very tall, narrow spike | The prior or posterior is highly concentrated (e.g., very low "prior confidence" weight combined with an extreme believed rate, or a very lopsided run of trials) | This is an accurate rendering of a concentrated distribution, not a bug — the y-axis autoscales to the actual peak density |

---

## Known Limitations

- Only the Beta-Binomial (proportion) model is implemented — no support yet for continuous outcomes or count data.
- Credible intervals are equal-tailed, not the (slightly narrower, for skewed posteriors) Highest Density Interval.
- Session state lives only in the current browser tab; reloading the page loses all entered trials.
- Prior elicitation via "believed rate + equivalent sample size" is simple and always correct, but cannot solve for an exact target credible-interval width the way a full quantile-matching optimizer could.
