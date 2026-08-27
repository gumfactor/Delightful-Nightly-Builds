# Why This? — Regression Lab

> **Date:** 2026-08-27

---

## How This Idea Was Selected

**Selection method:** Lottery draw.

Day of year 239 → `category_index = (239-1) % 9 = 4` → Category E — Learning Aid. The Category E backlog held 2 pending, unrated ideas (#18 GLM & Regression Diagnostics Trainer, #19 Attention Mechanism Visualizer), both added 2026-08-18 as runners-up to that night's Voxel Lab. With `R = 0` rated ideas in the pool, `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled 13 (≤25) → draw. Both ideas were unrated (blank = 5 tickets each), so the weighted draw was an even 1-10 roll: rolled 2, landing in idea #18's 1-5 range. Idea #18 won.

## The Decision

This was a lottery draw, not fresh generation, so the "decision" was really about not overriding it. Idea #18's own rating notes (written 2026-08-18) called it "a solid, testable idea on its own merits," passed over that night only because Voxel Lab had a stronger direct tie to the user's day job. Nothing has changed since to make it weaker — if anything, Category E's backlog is now down to one remaining idea (#19), so building #18 tonight keeps the category's idea pipeline from stagnating on unrated leftovers.

## Connection to User Context

PROFILE.md names "Develop advanced Bayesian statistical workflows" and "Become substantially stronger as a Python developer" as explicit learning goals, and the user teaches "Stress and Coping" and other courses where regression and its assumptions are bread-and-butter material. OLS regression diagnostics — the specific gap this build fills — sit underneath nearly every quantitative method the user's own research and teaching depend on, yet no prior build addresses them directly.

## Why Tonight

Category E has been built 6 times before tonight (Power Lab: statistical power; CircuitLab: neuroanatomy; Bayes Lab: Bayesian inference; Signal Detection Lab: SDT; Portfolio Lab: Modern Portfolio Theory; Voxel Lab: fMRI preprocessing pipeline). None of them touch ordinary least squares or its diagnostic assumptions, despite OLS regression being the most commonly taught and used statistical model in the user's own field — a real, until-tonight-untouched gap in the catalog, the same kind of gap-filling logic that steered several recent Category E and other-category builds (Voxel Lab's neuroimaging-pipeline gap, Bayes Lab's Bayesian-workflow gap).

## What I Hope the User Gets From This

1. A hands-on way to build intuition for what heteroscedasticity, non-linearity, and influential outliers actually look like in a residual plot — something static textbook figures don't convey as well as dragging a point and watching the diagnostics react live.
2. A concrete, numeric demonstration of multicollinearity's real cost (inflated standard errors, not necessarily worse R²) that could directly sharpen how the user reads or teaches regression output in their own research and courses.
3. A small, reusable piece of verified statistical code (the OLS-via-Gauss-Jordan engine, t-distribution CDF, Cook's Distance) that is honest about what it computes and cross-checked against known values — useful as a reference even outside the trainer itself.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|-----------------|
| Attention Mechanism Visualizer (idea #19) | E | Lost the weighted lottery draw (rolled 2/10, needed 6-10). Its own 2026-08-18 rating notes already flagged a weaker PROFILE.md tie than a lab-work-anchored idea — reads as generic ML education rather than something tied to the user's own research or teaching. |
| A fresh Category E idea (e.g., a t-test/ANOVA assumption-checking trainer) | E | Not generated — the lottery drew before reaching the fresh-idea path, and idea #18 was still a strong, unbuilt candidate rather than a stale duplicate. |
| GLM in the sense of Generalized Linear Models (logistic/Poisson regression) | E | The backlog idea's own description scoped this specifically to OLS assumption diagnostics (residual/QQ/leverage plots, heteroscedasticity, non-linearity, outliers, multicollinearity) — broadening to logistic/Poisson regression would have diluted an already-ambitious single-session scope rather than deepening it. |
