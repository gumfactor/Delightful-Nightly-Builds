# Future Features — GradeLine

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **CSV grade export** — a `export csv <batch_id>` command that writes one row per submission (identifier, word count, citation count, each criterion's score, compliance flags) so the deterministic scores can be pasted straight into a grade book without retyping.
2. **Configurable heading patterns per rubric** — let a rubric specify a regex or a list of acceptable heading spellings per required section (e.g. "Discussion" / "Analysis" / "Results and Discussion") instead of GradeLine's current single-name, case-insensitive match.
3. **`--threshold` sweep report** — a flag that reruns the similarity check at several thresholds (0.6, 0.7, 0.8, 0.9) in one pass and shows how the flagged-pair count changes, so an instructor can calibrate the right threshold for a given assignment type without re-running `grade` by hand each time.

## Medium Effort (roughly one nightly build session)

4. **DOCX/PDF ingestion** — add `python-docx` and a PDF text extractor so submissions in the formats students actually turn in most often don't need a manual text conversion step first. This was deliberately deferred tonight to keep the parsing layer's test surface small and fully deterministic.
5. **Per-criterion instructor score override with audit trail** — a `score <batch_id> <identifier> <criterion_id> <value>` command that lets the instructor record their own manual score for `manual_only` (or any) criteria directly into the same batch record, with the deterministic auto-score kept alongside for comparison rather than overwritten.
6. **Rubric criterion library** — a small local SQLite library of reusable criteria (mirroring the pattern several prior Category C builds, e.g. Grant Vault, established for reusable text chunks) so a recurring assignment's rubric can be assembled from previously-used criteria instead of retyped each term.

## Ambitious Extensions (multi-session effort)

7. **Grade trend dashboard across a whole course** — extend `compare` into a full multi-batch view (a real Chart.js line chart of class-average-per-criterion across every assignment in a course, not just a two-batch text diff), turning GradeLine from a per-assignment tool into a semester-long instrument.
8. **LMS export integration** — write grades and per-student feedback directly into a Canvas- or Brightspace-compatible CSV/API format, closing the loop from "graded in GradeLine" to "posted in the grade book" without manual re-entry. Deliberately out of scope tonight since no LMS credential is listed in PROFILE.md's Data Sources.

---

## Possible Integration Points

- **Lecture Loom** (2026-08-24) shares GradeLine's deterministic-core-plus-optional-AI-polish pattern and Claude Code Skill wrapper; a future build could let a Lecture Loom-generated assignment prompt auto-generate a starting GradeLine rubric from its own stated learning objectives.
- **Waymark** (2026-08-07) and **Promptbook** (2026-09-03) both established a pattern of mining a local, already-existing corpus (git history, Claude Code transcripts) rather than requiring new manual entry — GradeLine's near-duplicate detector could be pointed at that same "mine what already exists" philosophy if a future build added a lightweight, opt-in way to feed the instructor's already-graded past submissions in as a reference corpus (never a live plagiarism-database API — no such credential exists in PROFILE.md).

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Section-heading detection requires the heading to be alone on its own line (optionally with 1-6 leading `#` and a trailing colon); a heading embedded mid-paragraph or numbered ("1. Introduction") is not recognized | Extend `find_sections`'s regex to accept an optional leading enumeration token, or add a second matching pass over the first N words of each line |
| Citation counting is a heuristic (Author-Year parenthetical and numbered-bracket styles only) and will under-count footnote-style or narrative ("Smith (2019) found...") citations | Add a narrative-citation pattern and document the heuristic's known blind spots directly in a rubric-level warning when citation count is near the minimum |
| Plain text/Markdown only — the most common real submission formats (`.docx`, PDF) require a manual conversion step first | Add `python-docx`/PDF extraction (see Future Features #4) |
| The similarity engine flags textual near-duplication only; it cannot detect paraphrased plagiarism or AI-generated near-identical prose with different wording | Document this limitation prominently in Manual.md (done) rather than overstating the tool's detection power |
