# Future Features — Pooling Lab

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **CSV/data export** — a "Download this sample as CSV" button exporting every observation with its group id, so a generated dataset can be dropped straight into R/Python for a follow-up demo of an actual `lme4`/`statsmodels` mixed-model fit against the numbers this tool already computed.
2. **"Match slider to sample" button** — a one-click action that snaps the τ/σ sliders back to the values that actually generated the currently-displayed sample, undoing any manual slider exploration without needing a full Regenerate.
3. **Copy-to-clipboard for the Explain This output** — small affordance so the plain-English explanation can be pasted straight into lecture notes or a slide.

## Medium Effort (roughly one nightly build session)

4. **A second grouping factor (crossed random effects)** — extend the engine to two independent grouping factors (e.g. participant × testing site) so the tool can demonstrate crossed vs. nested random effects, a common point of confusion once students move past the single-factor case.
5. **Covariate-adjusted pooling** — add one continuous predictor per observation and show how partial pooling on the *intercept* interacts with a shared *slope*, moving one step closer to a real mixed-effects regression rather than just group-mean pooling.
6. **Persisted "best run" gallery** — let the user save a few named (seed, profile, τ, σ) configurations that produce especially illustrative charts (e.g. "dramatic shrinkage demo"), stored in `localStorage`, for quick recall when teaching the same concept in different course sections.

## Ambitious Extensions (multi-session effort)

7. **Bayesian posterior view** — alongside the empirical-Bayes point-estimate shrinkage this build already computes, add a full Bayesian treatment (e.g. via a small from-scratch Gibbs sampler, following the same "from-scratch, cross-checked math engine" pattern as Bayes Lab) showing posterior credible intervals per group instead of just point estimates — turning "how much to trust each group" into a visible distribution rather than a single shrunk number.
8. **Real-data mode** — accept a small CSV upload (group id + value columns) and run the exact same no-pooling/partial-pooling/complete-pooling comparison against the user's own actual repeated-measures or multi-site lab data, turning this from a teaching simulator into an actual first-pass analysis tool for real data.

---

## Possible Integration Points

- **ERP Lab (2026-09-14)** and **Regression Lab (2026-08-27)** are the two most similar prior Category E builds — both are from-scratch, verified statistics engines driving a live chart. A shared "Stats Lab" landing page linking all Category E builds together (power analysis, Bayesian inference, SDT, portfolio theory/MPT, fMRI pipeline, OLS diagnostics, ERP/EEG, and now nested-data pooling) would turn eight-plus scattered single-purpose tools into a genuine personal stats-teaching library — worth considering as a future Category C (Personal Knowledge Tool) build.
- **CiteForge / course-material builds** — the deterministic explanation text this build generates (`buildDeterministicExplanation` in `src/explain.js`) could feed directly into a future course-material generator as a worked example of shrinkage, without needing an API key at all.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Only one grouping factor is supported | Add crossed/nested multi-factor support (see Ambitious Extension #4 above) |
| τ/σ sliders can drift away from the sample's actual generating values without an obvious visual cue | Add a small indicator showing whether the sliders currently match the last-generated sample's true parameters |
| No persistence of quiz results across sessions | Add optional `localStorage`-backed best-score tracking, matching the pattern already used in other Category E builds (e.g. ERP Lab's `erplab_quiz_best`) |
