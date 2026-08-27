# Future Features — Regression Lab

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Confidence/prediction interval band on the fit line** — Draw a shaded band around the regression line on the Scatterplot & Fit canvas using the standard error of prediction at each x, so users see uncertainty widen away from x̄, not just the point estimate.
2. **Export current dataset as CSV or JSON** — A "Download Data" button on the Scatterplot & Fit tab that serializes the current `points` array, so a custom-drawn dataset can be reused elsewhere (e.g. pasted into a stats package).
3. **Keyboard-accessible point editing** — Tab to a point and use arrow keys to nudge it, as an alternative to mouse dragging, for accessibility and for precise adjustments.

## Medium Effort (roughly one nightly build session)

4. **A residual-transformation sandbox** — Add log/sqrt/Box-Cox transform buttons that re-run the regression on transformed y and show the diagnostics before/after side by side, directly teaching the standard fix for heteroscedasticity rather than only detecting it.
5. **Weighted Least Squares mode** — Once heteroscedasticity is flagged, offer a one-click WLS refit (weights = 1/fitted variance from the Breusch-Pagan auxiliary regression) and show how the coefficient SEs shrink back toward what OLS would report under homoscedasticity.
6. **A third predictor in the Multicollinearity Lab** — Extend from 2 to 3 correlated predictors using the existing `multipleRegression` engine (already general), with a small correlation-matrix heatmap instead of a single slider.

## Ambitious Extensions (multi-session effort)

7. **Logistic regression companion module** — A sibling trainer for binary-outcome GLMs (logit link, odds ratios, a confusion-matrix/ROC diagnostics tab) using the same drag-to-fit interaction pattern, extending "OLS assumption diagnostics" into the generalized-linear-model space the original backlog idea's title referenced but this build deliberately scoped out.
8. **Bring-your-own-data mode** — A CSV file-drop that maps two numeric columns onto the Scatterplot & Fit tab, letting the user run these exact diagnostics against their own research data instead of only synthetic presets — the natural next step once the teaching mechanic is proven.

---

## Possible Integration Points

- **Bayes Lab** (2026-07-22) and **Signal Detection Lab** (2026-07-31) share this build's from-scratch-math-with-cross-checked-tests pattern; a future "Stats Toolkit" umbrella build could link all three (plus Power Lab, Voxel Lab, Portfolio Lab) from one entry page rather than leaving each as an isolated `file://` HTML page.
- **Ledger Lens** / **ItemScope** / other CSV-ingesting builds already have RFC4180-style CSV parsing (Ingest Gate, 2026-08-10) that a future "bring your own data" mode (see above) could reuse directly rather than reimplementing.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| The Cook's Distance 4/n rule-of-thumb can flag a point on genuinely well-behaved data (see BUILD_LOG.md) | Show both the raw threshold crossing AND the dominance-ratio signal (already computed for quiz grading) directly in the Diagnostics tab UI, not just the boolean flag |
| Only 2 predictors are exposed in the Multicollinearity Lab UI, though the underlying engine supports any number | Extend to a 3-predictor correlation-matrix UI (see Medium Effort #6) |
| No confidence/prediction interval visualization on the fit line | Add the shaded-band Quick Win above |
| Skewness/excess kurtosis are a heuristic, not a formal normality test | Implement a proper Shapiro-Wilk or Anderson-Darling test if a future session wants harder normality evidence |
