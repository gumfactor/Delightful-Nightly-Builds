# Future Features — Bayes Lab

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Save/load session as JSON** — a button to export the current scenario/prior/trial log as a downloadable JSON file, and a matching "load session" file picker, so a real study's trial log can be resumed across browser sessions without re-entering everything.
2. **Copy-as-Markdown summary** — one-click copy of the current Bayesian summary, Bayes factor, and frequentist contrast as a formatted Markdown block, ready to paste into a manuscript's Results section or a lab notebook.
3. **Keyboard shortcuts** — bind `s` / `f` to `+ Success` / `+ Failure` and `u` to Undo, so a live data-entry session (e.g., watching a study run in real time) doesn't require mouse clicks for every trial.

## Medium Effort (roughly one nightly build session)

4. **Sequential-updating animation / playback** — replay the trial history as an animated sequence (posterior curve morphing frame by frame) instead of only the static history table, useful for teaching demonstrations or lecture recordings.
5. **Two-proportion comparison mode** — extend the Beta-Binomial engine to compare two independent groups (e.g., treatment vs. control), computing the posterior distribution of the difference in rates via Monte Carlo sampling from the two independent Beta posteriors, plus a Bayes factor for "groups differ" vs. "groups are equal."

## Ambitious Extensions (multi-session effort)

6. **Non-conjugate models via grid approximation** — generalize beyond the Beta-Binomial case to a small library of common models (e.g., Normal-Normal for continuous outcomes, Poisson-Gamma for count data) using numerical grid approximation instead of closed-form conjugacy, broadening this from "one specific model" to a general-purpose Bayesian teaching sandbox.
7. **Course-integration mode** — a facilitator view where a set of pre-built scenarios (with answer keys) can be assigned to students, each student's session state exported, and results aggregated into a simple gradebook-style summary — turning this from a personal trainer into teaching material for the "Stress and Coping" or "AI Applications for Psychologists" courses named in PROFILE.md.

---

## Possible Integration Points

- **Stats Coach** (2026-06-25, unmerged) already builds a frequentist test-selection decision tree with AI-generated R/Python code snippets; a natural pairing would be a shared "which framework should I use" landing screen that routes to either tool depending on whether the researcher wants a classical test or a Bayesian estimate.
- **Power Lab** (2026-07-04) covers frequentist power/sample-size planning; a future build could add a "Bayesian sample size" panel here — simulating how quickly the credible interval narrows to a target width under a given assumed true rate, directly complementing Power Lab's frequentist power curves.
- **CircuitLab** (2026-07-13) and **Connectome** (2026-07-11) both demonstrate the "own-research-grounded scenario + optional AI narrative with deterministic fallback" pattern this build reuses; any future teaching-tool build in Category E should keep following that same reliability contract (always functional without a key).

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Equal-tailed credible intervals are used instead of the Highest Density Interval (HDI); for very skewed posteriors (e.g., after very few or very lopsided trials) the equal-tailed interval can be a looser bound than the HDI would give | Add an HDI computation via a fine grid search over the posterior density (find the narrowest interval containing 95% of the mass) as an alternate, clearly-labeled interval option |
| Prior elicitation only supports the "target rate + equivalent sample size" method; a researcher with a specific target credible interval in mind (e.g., "I want my prior 95% CI to be exactly [10%, 40%]") has no direct way to solve for that | Add a numerical quantile-matching solver (bisection over equivalent sample size at a fixed target mean) as a third elicitation mode |
| The Bayes factor uses the Savage-Dickey method, which assumes the null is a single point value (`p0`); it cannot represent a "null region" (e.g., "no meaningful effect" defined as ±5 percentage points around p0) | Add a Region of Practical Equivalence (ROPE) option alongside the point-null Bayes factor |
| Session state is lost on page reload with no warning | Add a `beforeunload` warning when trials exist but haven't been exported, or auto-save to `localStorage` as a recovery mechanism (would need explicit user opt-in given the "no data leaves your machine" framing already used for the AI key) |
| Only proportions (Beta-Binomial) are covered — a researcher with a continuous outcome (e.g., a cortisol measurement) has no matching Bayesian workflow here | See Ambitious Extension #6 (Normal-Normal model) |
