# Manual — Regression Lab

> **Version:** 1.0 (built 2026-08-27)
> **Complexity:** Ambitious Project

---

## What This Is

Regression Lab is a browser-based trainer for ordinary least squares (OLS) regression and the diagnostic checks that reveal when its assumptions break. Drag points on a scatterplot and watch the fitted line, R², and coefficients react instantly; switch to the Diagnostics tab to see the same dataset's residual plot, Q-Q plot, and leverage/Cook's-Distance plot, along with real statistical tests for heteroscedasticity and non-linearity. A separate Multicollinearity Lab demonstrates — with a single slider — why correlated predictors inflate coefficient standard errors without necessarily hurting overall fit. A 12-question quiz tests both concept recall and live pattern recognition against real computed diagnostics.

---

## Quick Start

1. Open `index.html` directly in any modern browser (double-click it, or drag it into a browser window — no server or install needed).
2. On the **Scatterplot & Fit** tab, click one of the 5 preset buttons (or drag existing points) to explore how the fit responds.
3. Click the **Diagnostics** tab to see that same dataset's residual, Q-Q, and leverage plots plus the test results.
4. Click the **Multicollinearity Lab** tab and drag the correlation slider to see VIF and standard errors respond.
5. Click the **Quiz** tab and **Start Quiz** to test your understanding.

---

## How to Use It

### Scatterplot & Fit

- **Preset buttons** load one of 4 fixed datasets (Well-Behaved, Heteroscedastic, Non-Linear, Outlier/High Leverage) or switch to **Custom (Free Draw)**, which starts empty.
- **Click empty canvas space** to add a point — only works in Custom mode.
- **Drag any point** (in any mode, including the fixed presets) to move it; the fit updates live as you drag.
- **Double-click a point** to remove it, in any mode.
- **Clear Points** empties the canvas and switches to Custom mode.
- The stats panel shows n, intercept, slope, R², adjusted R², the slope's standard error, t-statistic, and two-tailed p-value — all recomputed on every change. With fewer than 3 points, the equation area explains that more points are needed rather than showing `NaN`.

### Diagnostics

- Runs on whatever dataset is currently loaded on the Scatterplot & Fit tab (shown in the panel note).
- **Residuals vs. Fitted**: look for a funnel shape (heteroscedasticity) or a curved band (non-linearity).
- **Normal Q-Q Plot**: standardized residuals should track the dashed 45° reference line if they're approximately normal.
- **Leverage vs. Cook's Distance**: the red dashed line is the 4/n rule-of-thumb threshold; a point far above it has outsized influence on the fit.
- The **Assumption Tests** table reports the actual Breusch-Pagan test (heteroscedasticity), a RESET-style test (adds x² and tests its coefficient — a linearity check), the most influential point's Cook's Distance, and residual skewness/excess kurtosis.
- The verdict banner names the single most likely issue, computed live — not a canned label per preset.
- **Explain This Result**: paste an Anthropic API key (session-only — never stored, never sent anywhere but `api.anthropic.com`) and click to get a plain-English explanation from Claude Haiku. Leave the key blank (or if the request fails for any reason) and you still get a full explanation from a deterministic template built from the same numbers.

### Multicollinearity Lab

- Drag the slider to set how strongly two predictors, X1 and X2, are correlated (0.00 to 0.99).
- Watch VIF and both predictors' standard errors climb sharply as correlation rises, while the joint model's R² barely moves — the key lesson: multicollinearity threatens the precision of individual coefficient estimates, not overall predictive fit.

### Quiz

- 12 questions per session: 4 ask you to look at a real dataset's residual plot and diagnose the issue (the correct answer is computed live from the exact same tests used in the Diagnostics tab); 8 are fixed conceptual questions about what the diagnostics mean.
- Each answer shows immediate feedback with an explanation, then a **Next Question** button.
- Your best score is saved locally (`localStorage`) and shown the next time you open the Quiz tab.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| Anthropic API key | none | Optional, entered per-session on the Diagnostics tab. Never persisted; cleared on page reload. |

No other configuration required.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Diagnostics tab shows "Add at least 4 points" | The current dataset (often Custom) has fewer than 4 points | Add more points on the Scatterplot & Fit tab, or switch to a preset |
| "Explain This Result" always shows the deterministic template | No API key entered, the key is invalid, or the network request failed | Enter a valid Anthropic API key; the app never blocks on this — the fallback is intentional and always available |
| Dragging feels imprecise on a very zoomed browser window | Canvas coordinates are scaled from CSS pixels to the canvas's internal 640×440 (or panel-specific) resolution | Resize the browser window to a normal zoom level, or use a larger viewport |

---

## Known Limitations

- Only 2 predictors are exposed in the Multicollinearity Lab UI (the underlying regression engine supports any number).
- The Cook's Distance 4/n rule-of-thumb can occasionally flag a point on genuinely well-behaved data — this is a known property of that specific heuristic threshold, not a bug; the app's quiz classifier instead uses a dominance-ratio check (the top point's influence relative to the second-highest) to avoid misreading this as a real outlier scenario.
- Skewness/excess kurtosis are used as a normality heuristic rather than a formal statistical test (e.g., Shapiro-Wilk).
- No dataset persistence across page reloads beyond the quiz best score.
