# Why This? — Pooling Lab

> **Date:** 2026-09-23

---

## How This Idea Was Selected

**Selection method:** Fresh generation (lottery gate missed).

Tonight is day-of-year 266, so `category_index = (266-1) % 9 = 4` → **Category E — Learning Aid**. The backlog (`builds/ideas.md`, resynced from the most recent open PR branch, `claude/cool-sagan-j1h4o4`, since `main` is many builds behind) had four pending Category E rows, all unrated: #19 Attention Mechanism Visualizer, #44 Meta-Analysis/Forest Plot Trainer, #59 Multilevel/Mixed-Effects Modeling Lab, #60 Psychometrics/IRT Lab. With `R=0` rated ideas among them, `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled a random integer 1–100 → **29**. 29 > 25, so the lottery gate missed and the process routed to fresh idea generation (pool size: 4 pending Category E rows considered as candidates alongside the option of a wholly new idea).

## The Decision

Following the precedent set by prior fresh-generation sessions in this catalog (e.g. Star Atlas, 2026-09-21), the still-pending backlog rows were treated as legitimate fresh-generation candidates rather than discarded. Idea #59 (Multilevel/Mixed-Effects Modeling Lab) was the strongest: it had already been passed over twice — on 2026-08-18 (in favor of Regression Lab) and again on 2026-09-14 (in favor of ERP Lab) — with both prior notes explicitly flagging it as "worth building on a future Category E night." Two deferrals is a real signal that this idea keeps losing narrow, close calls rather than being weak, so tonight it won outright.

## Connection to User Context

PROFILE.md names the user as a lab director who runs "a forensic and affective neuroscience lab" and supervises "research assistants and graduate students" collecting data that is naturally nested — repeated trials within participants, participants within lab sessions or sites, students within course sections. Multilevel/mixed-effects reasoning (random intercepts, intraclass correlation, and why partial pooling beats either ignoring group structure or treating every group as fully independent) is directly load-bearing for real analysis of that kind of data, and for teaching it — PROFILE.md also lists "AI Applications for Psychologists" and course development among the user's actual job duties.

## Why Tonight

Category E has produced eight prior builds (Power Lab, CircuitLab, Bayes Lab, Signal Detection Lab, Portfolio Lab, Voxel Lab, Regression Lab, ERP Lab), and the most recent one (ERP Lab, 2026-09-14) explicitly noted that all seven before it were "synthetic client-side statistics of one kind or another" — but none had touched nested/hierarchical data or shrinkage estimators specifically. This build continues that successful pattern (a from-scratch, verifiable math engine driving a live interactive chart) while filling a real, previously-identified gap rather than repeating an existing mechanic.

## What I Hope the User Gets From This

1. A concrete, draggable-slider intuition for *why* partial pooling works — watching a small-sample group's estimate visibly snap toward the grand mean while a large-sample group barely moves, under the exact same tau/sigma, is a much stronger teaching moment than the formula alone.
2. A ready-made teaching aid: this can be projected in "Stress and Coping" or "Social Affective Neuroscience" methods sessions, or used to explain to a new RA why a multilevel model, not a plain ANOVA, is the right tool for their nested data.
3. A working, from-scratch reference implementation of the empirical-Bayes shrinkage formula and an ANOVA-based ICC estimator, in case it's useful as a starting point for a real analysis script later.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Psychometrics / Item Response Theory Lab (#60) | E | Real tie to the user's Qualtrics scale-construction work, but it was passed over most recently (2026-09-14) for a narrower reason (ERP's modality was fresher that night) than #59's two-time deferral; #59 had the stronger accumulated case. |
| Attention Mechanism Visualizer (#19) | E | Ties to the user's AI interests, but per its own 2026-08-18 note it "reads as generic ML education rather than something anchored to the user's own lab work" — a weaker PROFILE.md tie than nested data's direct connection to the lab's actual repeated-measures/multi-site data. |
| Meta-Analysis / Forest Plot Trainer (#44) | E | A real, untouched statistical topic, but per its own 2026-09-05 note none of PROFILE.md's three named courses are meta-analysis-focused, giving it a looser curricular tie than multilevel modeling's direct relevance to nested lab data. |
