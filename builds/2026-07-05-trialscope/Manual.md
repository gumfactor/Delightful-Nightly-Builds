# Manual — TrialScope: Behavioral & Reaction-Time Data QC Explorer

> **Version:** 1.0 (built 2026-07-05)
> **Complexity:** Ambitious Project

---

## What This Is

TrialScope takes a trial-level CSV export from a behavioral or cognitive task (one row per trial — the standard export shape from PsychoPy, jsPsych, E-Prime, or a custom experiment script) and turns it into an interactive data-quality report: per-subject and per-condition statistics, automatically flagged trials and subjects (anticipatory guessing, attention-lapse outliers, chance-level performance, incomplete data, implausible ceiling performance), a recommended exclusion list with reasons, and a ready-to-adapt "Participants & Data Quality" paragraph for a methods section. It replaces manually eyeballing a spreadsheet to decide which participants to drop before running an analysis.

---

## Quick Start

1. Have a trial-level CSV ready — one row per trial, with columns for subject ID, condition, reaction time, and correct/incorrect.
2. From this build folder, run:
   ```
   python3 src/trialscope.py path/to/your_data.csv --out-dir output
   ```
3. Open `output/report.html` in any browser.
4. Review the flagged subjects and the recommended exclusion list.
5. Use `output/cleaned_data.csv` (has a `QC_Flag` column per trial) and `output/exclusions.csv` for downstream analysis.

---

## How to Use It

### Column Detection

TrialScope tries to auto-detect your columns from common naming conventions:

| Role | Recognized column names |
|------|--------------------------|
| Subject | subject, subject_id, subj, subj_id, participant, participant_id, id, pid |
| Condition | condition, cond, group, condition_name, trial_type |
| Block (optional) | block, trial_block, block_num, block_number |
| Trial number (optional) | trial, trial_num, trial_number, trial_index |
| Reaction time | rt, reaction_time, response_time, latency, rt_ms |
| Accuracy | accuracy, correct, acc, is_correct, response_correct |

If your file uses different names, or auto-detection picks the wrong column, override it explicitly:

```
python3 src/trialscope.py data.csv --subject-col ppt --rt-col latency_ms --accuracy-col hit
```

Block and trial number are optional — if absent, TrialScope infers trial order from row order within each subject and treats all trials as one block.

### QC Flags

Every flag is computed live from your data using configurable thresholds — nothing is hardcoded to a specific dataset:

| Flag | Default rule | Override |
|------|--------------|----------|
| `fast_guess` (trial-level) | RT below the floor | `--rt-floor-ms` (default 150) |
| `outlier` (trial-level) | Modified z-score (median/MAD) beyond the threshold, or RT above the ceiling | `--sd-outlier` (default 3.5), `--rt-ceiling-ms` (default 5000) |
| `chance_level` (subject-level) | Binomial test: can't reject "performing at chance" at the configured alpha | `--chance-rate` (default 0.5), `--chance-alpha` (default 0.05) |
| `incomplete` (subject-level) | Completed trials below the completion fraction of expected trials | `--expected-trials` (no default — flag is skipped unless set), `--min-completion` (default 0.8) |
| `ceiling_implausible` (subject-level) | 100% accuracy combined with implausibly fast mean RT | `--rt-floor-ms`, a fixed 1.5&times; multiplier on the floor |
| `high_fast_guess_rate` (subject-level) | 20%+ of a subject's trials are fast-guess trials | derived from `--rt-floor-ms` |

A subject is recommended for exclusion when their flag count reaches `--exclude-threshold` (default 2) — a single anomaly alone doesn't trigger exclusion by default, but two or more do.

### The Report

- **Summary header** — subject/trial/condition counts and malformed-cell warnings from parsing.
- **Participants & Data Quality** — the generated methods paragraph, with a note on whether it came from the Anthropic API or the deterministic template.
- **Subjects table** — sortable (click any column header) and searchable (filter box), with flag badges per subject; excluded-candidate rows are subtly highlighted.
- **Conditions table** — per-condition accuracy/RT summary.
- **Accuracy by condition** and **RT distributions** — hand-drawn inline SVG charts (no external chart library, no network requests — the report works fully offline).
- **Learning curves** — accuracy and RT trend across binned trial position, per condition.
- **Configuration Used** — every threshold that produced the flags in this specific run.

### AI-Generated Methods Paragraph

If `ANTHROPIC_API_KEY` is set in your environment, TrialScope sends the *computed statistics only* (never raw data or participant identifiers) to Claude Haiku to draft the paragraph in publication-ready prose. If the key isn't set, or the request fails for any reason, TrialScope falls back to a deterministic template built directly from the same statistics — the report is complete either way. Use `--no-ai` to always use the template.

---

## Configuration

All thresholds are CLI flags with defaults:

| Setting | Default | Description |
|---------|---------|--------------|
| `--rt-floor-ms` | 150 | Anticipatory/fast-guess RT floor |
| `--rt-ceiling-ms` | 5000 | Absolute RT outlier ceiling |
| `--sd-outlier` | 3.5 | Modified z-score (median/MAD) outlier threshold |
| `--chance-rate` | 0.5 | Chance performance rate for the binomial test |
| `--chance-alpha` | 0.05 | Alpha for the chance-level test |
| `--min-completion` | 0.8 | Minimum fraction of expected trials to avoid the incomplete flag |
| `--expected-trials` | (none) | Expected trial count per subject — the incomplete flag is skipped unless this is set |
| `--exclude-threshold` | 2 | Number of flags needed to recommend exclusion |
| `--no-ai` | off | Always use the deterministic template, skip the Anthropic API call |
| `--out-dir` | `trialscope_output` | Output directory |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "Could not auto-detect required column(s)" | Your column names don't match the recognized aliases | Pass `--subject-col`, `--rt-col`, etc. explicitly |
| A subject with high accuracy still gets a `chance_level` flag | With very few trials, the binomial test has low statistical power and can't rule out chance performance even at high observed accuracy — the report shows the exact p-value so you can judge for yourself | Interpret alongside trial count; consider `--chance-alpha` if it's too strict/lenient for your design |
| AI paragraph didn't appear, template was used instead | No `ANTHROPIC_API_KEY` set, or the API call failed | This is expected fallback behavior, not an error — the template paragraph uses the same computed statistics |
| Report shows "No trial data found" | Input CSV had a header but zero data rows | Check the input file |

---

## Known Limitations

- Long-format data only (one row per trial) — wide-format exports (one row per subject) aren't supported.
- The chance-level test is a simple one-sample binomial test against a fixed chance rate; it doesn't model 3+ alternative-forced-choice designs beyond a single configurable rate, and has low power at very small trial counts (see Troubleshooting).
- Outlier detection uses each subject's own correct-trial RTs; a subject with very few correct trials produces an unstable or undefined median/MAD, in which case only the absolute RT ceiling applies to that subject.
- No between-condition statistical inference (ANOVA, mixed models) — only descriptive comparison.
