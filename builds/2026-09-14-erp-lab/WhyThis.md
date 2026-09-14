# Why This — ERP Lab

## Category & rotation

Day of year 257 → `(257 - 1) % 9 = 4` → Category E — Learning Aid.

## Lottery

Category E's pending backlog held 2 rows: idea #19 (Attention Mechanism Visualizer) and idea #44 (Meta-Analysis / Forest Plot Trainer). Both have blank ratings, so `R = 0` and `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled 56/100 → missed the gate → fresh idea generation (Step 2d).

## Topic diversity check (last 10 builds)

09-04 CaseForge (D, legal/course-material case generator) · 09-05 Mediation & Moderation Analysis Lab (E, stats) · 09-06 Almanac (F) · 09-07 True Course (G, boating navigation) · 09-08 Secrets Sentinel (H, git-history secret scanner) · 09-09 Headroom (I, grant/CRA limits) · 09-10 Dominion Index (A, Canada List/Wikidata) · 09-11 GradeLine (B, similarity/grading) · 09-12 Throughline (C, grant/manuscript writing) · 09-13 Preprint Pulse (D, arXiv trend digest). No domain repeats more than twice; no conflict with tonight's pick.

## All 8 prior Category E builds (full catalog history)

Power Lab (statistical power/sample size) · CircuitLab (neuroanatomy) · Bayes Lab (Bayesian inference) · Signal Detection Lab (SDT/ROC) · Portfolio Lab (Modern Portfolio Theory, the only one using real external data) · Voxel Lab (fMRI preprocessing pipeline + multiple-comparisons problem) · Regression Lab (OLS diagnostics) · Mediation & Moderation Analysis Lab (path analysis). All are strong, well-executed "Lab" builds: from-scratch math cross-checked against hand-worked reference values, native Canvas 2D visualization, and a live-computed quiz mode. None have been rated yet, so there is no direct rating signal for this specific sub-pattern — but CLAUDE.md's calibration note (low scores come from missing visual interfaces, mock-only data, or duplicated functionality) is already satisfied by this format, so tonight follows the same proven shape rather than reinventing it.

## Three candidates considered

1. **ERP Lab** (chosen) — EEG/ERP methodology (averaging, artifact rejection, FFT/filtering) applied to the P300 Concealed Information Test, a real forensic-neuroscience paradigm.
2. **Multilevel Modeling Lab** — nested/hierarchical data, intraclass correlation, random intercepts vs. fixed effects, partial pooling/shrinkage. Genuinely useful for real repeated-measures lab data and completely untouched by any prior Category E build; logged to `builds/ideas.md` as a strong future candidate.
3. **Psychometrics / Item Response Theory Lab** — classical test theory vs. IRT, item characteristic curves, test information functions, reliability. Ties to the Qualtrics QC build and actual scale-construction work; logged to `builds/ideas.md`.

## Why ERP Lab won

- **Untouched modality, not just an untouched topic.** Voxel Lab already covers fMRI/neuroimaging analysis, but ERP/EEG is a structurally different data type (a time series with a frequency-domain component, not a spatial voxel grid), so this isn't a rehash — it required a genuinely new engine (FFT, filtering, peak-to-peak artifact detection) none of the prior 8 builds implement.
- **Directly named in PROFILE.md twice over**: "neuroimaging methods" is an explicit rabbit-hole interest, and "forensic and affective neuroscience" is the user's literal job title/lab focus. The P300 Concealed Information Test (Farwell & Donchin's Guilty Knowledge Test paradigm) sits precisely at that intersection — it is real, well-published forensic-neuroscience methodology, not a generic stats topic bolted onto a forensic label.
- **Real statistical honesty, not just data-generation UI.** The permutation test is the actual inferential engine (not a canned significance flag), and the tool explicitly teaches the test's false-positive/specificity limitations via the "innocent suspect" toggle — appropriate academic framing for a real forensic method, consistent with how CircuitLab and Signal Detection Lab already handle sensitive clinical/forensic content responsibly.
- Multilevel Modeling Lab and the IRT Lab were both strong and are preserved in the backlog rather than discarded, but neither had as sharp a PROFILE.md tie as ERP/CIT's direct forensic-neuroscience match.

## Idea Brief

No linked Idea Brief — this was freshly generated tonight, not drawn from a backlog row with a brief.
