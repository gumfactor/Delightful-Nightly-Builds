# Future Features — Power Lab

1. **Exact noncentral-t power** via numerical integration or the regularized incomplete beta function, replacing the normal approximation for users who need pre-registration-grade precision without leaving the browser.
2. **More test families** — one-way ANOVA (f effect size), chi-square tests of independence, and correlation/regression power, so the tool covers the designs actually run in a psychology lab beyond the t-test family.
3. **Pilot-data effect size estimator** — paste or upload a small CSV of pilot data and have the tool compute Cohen's d directly, feeding straight into the Sample Size Calculator instead of requiring a hand-typed guess.
4. **Exportable grant-ready report** — a "Copy full power analysis paragraph" button that stitches together the design, effect size justification, and required N into pre-registration-style prose, not just the current single summary sentence.
5. **Saved scenario comparisons** — let a user save 2-3 named designs (e.g. "pilot" vs. "full study") side by side to compare power tradeoffs, persisted in `localStorage` like the quiz state already is.
6. **Spaced-repetition quiz mode** — track which quiz scenarios a user consistently misjudges and resurface those more often, instead of the current fixed round-robin order.
7. **Bayesian power / precision-based sample size planning** — an alternate mode based on expected posterior width rather than null-hypothesis rejection, directly extending the Bayesian-reasoning learning goal noted in `PROFILE.md`.
