# FutureFeatures.md — Qualtrics Survey Data Inspector

> Concrete enhancements to a working, useful tool. All are additive — none are required for the build to deliver value today.

---

## 1. Multivariate Outlier Detection (Mahalanobis Distance)

Compute Mahalanobis distance for each respondent across all numeric scale items. Flag respondents whose distance exceeds a chi-squared cutoff (e.g., p < .001) as potential outliers. This is the gold-standard outlier check in psychology research and would complement the current straight-lining detection.

**Why:** Straight-lining catches extreme careless responders; Mahalanobis catches subtler statistical outliers (e.g., respondents who use only extreme values in varied patterns).

---

## 2. Attention Check Auto-Detection

Scan question text (from the Qualtrics row 1 header) for phrases like "please select X", "attention check", "validity item". Flag respondents who failed identified attention check items. Output a summary of pass rates per attention item.

**Why:** Attention checks are near-universal in online research. Auto-detection would work on any Qualtrics export without requiring the researcher to manually identify the column names.

---

## 3. Longitudinal Multi-Wave Comparison

Accept two CSV files from the same study (e.g., Time 1 and Time 2) and produce a comparison report: matched respondent count, attrition rate, response quality changes across waves, item-level mean shift summary.

**Why:** Many neuroscience lab studies use pre/post or repeated-measures designs. Comparing data quality across waves is otherwise a manual process.

---

## 4. HTML Report: Respondent-Level Flags Table

Add a drill-down table to the HTML report showing every flagged respondent with their flags (incomplete, fast_response, straight_liner, duplicate_ip), response time, completion %, and a row of responses for identified scale items. Allows researchers to spot-check borderline cases before deciding to exclude.

**Why:** The current report gives aggregate counts. Researchers often need to review individual rows before making exclusion decisions.

---

## 5. Configurable Exclusion Rules via JSON

Add support for a `rules.json` file that specifies:
- Custom timing threshold
- Scale groups (already partly supported via `--scales`)
- Attention check columns + expected values
- Minimum Progress threshold (default 100)
- Maximum allowed missing data rate per respondent before exclusion

This would let a lab define study-specific QC rules once and reuse them across data collection waves.

---

## 6. Export: Exclusion Summary Report (Plain Text / CSV)

Produce a separate `exclusions_log.csv` listing every excluded respondent, the reason(s) for exclusion, and their key metadata (ResponseId, IP, timing, completion). Useful for the Methods section of a manuscript ("X participants were excluded due to incomplete responses; Y were excluded for straight-lining").

---

## 7. Cronbach's Alpha If Item Deleted

For each scale, compute the alpha that would result from removing each item. Present as a table: item name, alpha-if-deleted, and a flag if deletion would substantially improve the scale (e.g., > 0.05 improvement). This is standard output in scale development research.

---

## 8. Claude Code Skill: `/survey-qc`

Package the inspector as a Claude Code skill that accepts a CSV path and returns a formatted quality summary directly in a Claude Code session. This would make the tool available in any Claude coding context without launching a terminal.

**Why:** The most natural place to do data QC decisions is while exploring data in a coding session. A skill invocation would be faster than a terminal switch.

---

## 9. Batch Directory Mode

Add a `batch` subcommand: `python3 main.py batch ./data/` that processes all `.csv` files in a directory and produces a comparison table showing quality metrics across all surveys side-by-side. Useful for labs running multiple concurrent studies.
