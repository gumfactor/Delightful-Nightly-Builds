# WhyThis — dep-check

## Category & Date

- **Date:** 2026-06-19
- **Day of year:** 170
- **Category index:** (170 − 1) % 9 = 7 → **H — Developer Tool**

---

## Lottery

- **H-category pending ideas in backlog:** 0 (none — all backlog entries are A, B, C, F categories)
- **Pool empty → lottery skipped → fresh ideas path**
- **Roll:** N/A

---

## Fresh Ideas Generated

Three candidates evaluated:

| # | Idea | Why considered | Why kept/dropped |
|---|------|----------------|-----------------|
| 1 | **Python Dependency Auditor (`dep-check`)** | Directly useful for lab and personal Python projects; connects to real public data (PyPI API); clean pure-function design; CI-compatible | **Selected — strongest value/testability ratio** |
| 2 | Git History Visualizer | Visually impressive; surfaces code archaeology insights | Requires subprocess git calls which complicate testing; less immediately actionable than dep-check |
| 3 | Python Test Coverage Gap Finder | Addresses code quality | Pure-stdlib analysis but output is less decision-ready than package audit |

Non-winners appended to `builds/ideas.md` as IDs 9 and 10.

---

## Why dep-check?

The user manages multiple Python projects — nightly builds, lab data pipelines, The Canada List ingestion code — all of which accumulate pinned dependencies that drift behind PyPI. Checking these manually means opening pypi.org for each package, which nobody actually does consistently. `dep-check` makes the answer one command away.

The build connects to a real public data source (PyPI JSON API, no credentials needed), produces actionable categorized output (up-to-date / patch / minor / major / yanked), and is CI-compatible via exit-code contract. The HTML report gives a sharable snapshot of a project's dependency health.

The previous H-category build (Jun 7 Git Standup Reporter) covered a different dimension of developer workflow (commit history). This build covers dependency hygiene — no overlap.

---

## Idea Brief

No idea brief — this was a fresh-generated idea.

---

## Rating Prior Signals

The user rated the Qualtrics Survey Data Inspector 9/10 — a build that takes a messy real-world format, parses it cleanly, computes meaningful derived metrics, and produces a report. `dep-check` follows the same pattern: parse a messy format (requirements files), derive meaningful metrics (version delta, staleness, yanked), report clearly.
