# Why This Build

## Category and Date

2026-09-05, day of year 248, `(248-1) % 9 = 4` → Category E — Learning Aid.

## Lottery

Category E's backlog held exactly one pending, matching row: idea #19, "Attention Mechanism Visualizer" (unrated, blank rating = 5 tickets). With R=0 rated matching ideas, `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled 33/100 (via `secrets.randbelow`) — missed the 25% gate, routing to fresh idea generation per Step 2d.

## Fresh Ideas Considered

1. **Attention Mechanism Visualizer** (existing backlog idea #19) — from-scratch interactive transformer self-attention walkthrough with real matrix math, no library. Ties to PROFILE.md's "Agentic AI systems and workflows" interest, but this row has already been passed over twice with the same standing critique: it reads as generic ML education disconnected from the user's own lab work, and it doesn't touch any of the specifically-named courses or research areas. Left pending in the backlog rather than built again tonight.

2. **Mediation & Moderation Analysis Lab** (new) — interactive drag/slider trainer for the two most common multivariate techniques in social/affective/stress psychology, computing OLS regression, bootstrap confidence intervals, Sobel tests, simple slopes, and Johnson-Neyman regions of significance live from freshly generated synthetic samples. **Selected.**

3. **Meta-Analysis / Forest Plot Trainer** (new) — interactive fixed-vs-random-effects meta-analysis trainer with a live forest plot, heterogeneity statistics (Q, I²), and a funnel-plot publication-bias demo. Logged as new backlog idea #44 (not built tonight).

## Why Mediation & Moderation Analysis Lab Won

PROFILE.md names two specific courses the user currently teaches — Stress and Coping, and Social Affective Neuroscience — and mediation/moderation models are the standard analytic backbone of both literatures (e.g. "stress predicts poor health outcomes, mediated by rumination"; "trait empathy moderates the link between provocation and aggression in psychopathy research"). Despite seven prior Category E builds (Power Lab, CircuitLab, Bayes Lab, Signal Detection Lab, Portfolio Lab, Voxel Lab, Regression Lab), none cover mediation or moderation — Regression Lab's OLS diagnostics are the closest relative, but stop at single-predictor assumption-checking and never touch an indirect effect or an interaction term, which is a genuinely different (and, for this user, more directly relevant) topic.

The Meta-Analysis idea was passed over because none of the three named courses or the research-lab friction points in PROFILE.md are meta-analysis-specific, whereas mediation/moderation maps onto named course content directly. The Attention Mechanism Visualizer was passed over for the reason already recorded against it twice in the backlog — it's a good idea, but keeps losing to ideas with a tighter PROFILE.md tie, and this build had a tighter one.

## Ambition and Real-Data Note

Every displayed number — path coefficients, bootstrap CI, Sobel z, simple slopes, and the Johnson-Neyman region boundary — is computed live from a freshly drawn synthetic sample using a from-scratch OLS/matrix engine (no charting or stats library), never hardcoded. This build has no external live-data source to connect to (it is a statistics-education simulator over synthetic data, the same design shape as Power Lab, Bayes Lab, Signal Detection Lab, and Voxel Lab, none of which have a live-data dependency either) — the "genuine computation, never a script" bar applies to the math engine instead of an external API, consistent with how those four prior Category E builds satisfied the same standard. The optional AI-interpretation layer sends only already-computed aggregate statistics (never raw sample rows) to Claude Haiku, following the aggregate-only pattern established across the catalog's other optional-AI builds.

## Idea Brief

The selected backlog row (idea #19, ultimately not built) carried no linked Idea Brief, and this build was freshly generated rather than drawn from the backlog, so no Idea Brief Traceability section applies.
