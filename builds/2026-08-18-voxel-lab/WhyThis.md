# Why This — Voxel Lab

## Path: fresh idea generation, not lottery
`(day_of_year - 1) % 9 = (230-1) % 9 = 4` → Category E (Learning Aid) for 2026-08-18. The remote `builds/ideas.md` backlog (synced from the most recent open PR branch, `claude/cool-sagan-wramd3`, per Step 1's instruction that `main` runs weeks behind) has 17 rows and **zero** are Category E. Per Step 2c, an empty matching pool skips the lottery entirely — no roll to record — and goes straight to fresh generation (Step 2d).

## Topic diversity check
Scanned the last 10 builds (2026-08-08 → 2026-08-17): Panel Prep(D), Portfolio Lab(E), Ingest Gate(F), Quarter Call(G), Snipvault(H), Macro Kitchen(I), Earshot(A), Provenance(B), Curriculum Atlas(C), Maple Press(D). Investment/finance appears twice (Portfolio Lab, Quarter Call) — at, not over, the "more than twice" saturation threshold, so no domain was excluded outright. None of the 10 touch neuroimaging methodology.

## Why this idea over the alternatives
Five prior Category E builds exist: Power Lab (statistical power/sample size), CircuitLab (neuroanatomy structures/circuits), Bayes Lab (Bayesian inference on proportions), Signal Detection Lab (SDT/d-prime/ROC), and Portfolio Lab (Modern Portfolio Theory). Every one of them is either a general statistics trainer or a static-anatomy quiz. **None cover neuroimaging analysis methodology** — the actual technical pipeline the user runs studies through — despite PROFILE.md explicitly naming "Neuroimaging methods and forensic neuroscience" as a rabbit-hole topic and "conduct neuroimaging and behavioral studies" as a literal day-to-day duty. That is a real, named, and until-tonight-untouched gap, not a rationalization backfilled onto a generic idea.

Three candidates were generated:

1. **Voxel Lab** (selected) — interactive fMRI preprocessing pipeline walkthrough (motion correction → slice timing → normalization → smoothing → HRF/GLM → thresholding) plus a from-scratch multiple-comparisons Monte Carlo simulator demonstrating the "dead salmon" false-positive problem (uncorrected vs. Bonferroni vs. Benjamini-Hochberg FDR vs. cluster-extent correction), plus a quiz.
2. GLM & Regression Diagnostics Trainer — live-manipulable regression scatterplot with assumption-violation diagnostics (heteroscedasticity, leverage, multicollinearity). Rejected: this would be the *third* general-statistics trainer in Category E (after Power Lab and Bayes Lab), with no PROFILE.md-named domain tie stronger than "general research methods," which the category already has ample coverage of.
3. Attention Mechanism Visualizer — from-scratch self-attention/transformer walkthrough on a toy sentence. Rejected: ties to PROFILE.md's "Agentic AI systems and workflows" interest, but more loosely — it's a generic ML-education tool rather than something tied to the user's own lab work or day-to-day duties, and the calibration note in CLAUDE.md flags that builds not grounded in the user's actual named friction points have scored lower historically.

Voxel Lab won because it is the only candidate with a genuine "no prior build touches this, and it maps to a literal job duty" argument, and because its flagship feature — the multiple-comparisons simulator — is real Monte Carlo computation (independently-drawn Gaussian noise, real p-value correction math, live false-positive counting) rather than a prose wrapper around a concept. This directly avoids the failure mode that scored 2026-06-24's AI Lecture Builder a 2/10 ("a power user replicates this with one prompt") — there is no single prompt that *simulates* thousands of noise voxels and shows you, live, how many survive uncorrected thresholding versus FDR.

## Idea Brief
Fresh idea, not a lottery draw — no linked Idea Brief exists for this row (Step 2e is not applicable).

## Non-winning ideas
Candidates 2 and 3 above were appended to `builds/ideas.md` as new pending rows (IDs 18–19, Category E, complexity `ambitious`) for a future lottery draw, per Step 2d.

## Scope decision
The PRD's in-scope list already reflects the ceiling of what one session can deliver well: three tabs (Pipeline, Multiple Comparisons Lab, Quiz), all-from-scratch math, zero external dependencies. A fourth tab — a full interactive GLM design-matrix builder as a standalone feature — was considered and folded into a single pipeline step (HRF convolution + least-squares beta recovery demo) instead of a separate tab, to keep the build complete and polished rather than spreading effort across a fourth half-finished surface. No AI integration was added: unlike editorial/summarization builds, an AI prose layer would not differentiate this build — the value is entirely in the live, verifiable computation, and adding an optional AI tab here would be scope for its own sake rather than a genuine improvement.
