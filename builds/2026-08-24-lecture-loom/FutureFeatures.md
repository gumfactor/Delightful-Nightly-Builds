# Future Features — Lecture Loom

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Per-course config file** — a small `loom.json` in the notes folder pinning `--target-minutes`/`--wpm` per course (e.g. a 75-minute graduate seminar vs. a 50-minute undergrad lecture) so the right values apply automatically instead of being retyped on every run.
2. **`--strict` exit code** — an optional flag that makes `check`/`format`/`render` return a non-zero exit code if any lecture is `over_budget` or `missing` objectives, so it can be wired into a pre-semester CI-style sanity pass over a whole course folder.
3. **Markdown-to-clipboard shortcut** — a `--stdout` flag on `format` that prints the outline/handout to stdout instead of writing files, for quickly pasting into a slide tool without touching the filesystem.

## Medium Effort (roughly one nightly build session)

4. **Measured speaking-rate calibration** — let the user paste in an actual delivered-lecture transcript with a known duration once, compute their real words-per-minute from it, and persist that as the default instead of the generic 130 wpm assumption — turning the timing engine from a documented guess into a personally-calibrated one.
5. **Slide-count estimate** — beyond a time budget, estimate a recommended slide count per section from bullet density and a configurable bullets-per-slide target, closer to an actual deck outline rather than just a Markdown outline.

## Ambitious Extensions (multi-session effort)

6. **Direct .pptx export** — generate an actual PowerPoint file (title slide, one slide per section, speaker notes from the handout prose) using `python-pptx`, so the outline doesn't need manual re-entry into a slide tool at all.
7. **Cross-lecture pacing history** — persist each `render` run's timing numbers to local SQLite (matching this catalog's established snapshot pattern) so a professor can see, over a whole semester, whether their lectures are trending long or short against the same course's target, and whether their actual in-class pace (if logged back in) diverges from the wpm assumption.

---

## Possible Integration Points

- **Curriculum Atlas** (2026-08-16) already builds a cross-course concept knowledge base from syllabi — a future version of that build could ingest Lecture Loom's per-lecture objective lists directly instead of re-extracting them, giving one consistent objective-extraction path across both tools.
- **Panel Prep** (2026-08-08) established the "deterministic rule-engine checklist, AI as a polish layer only" pattern this build followed for lecture content instead of grant proposals — a natural third application of the same shape would be course syllabi themselves (a "Syllabus Prep" checking required-section completeness).

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Words-per-minute is a fixed, documented assumption (130), not measured from the user's actual delivery | Future Feature #4 above — calibrate from a real transcript-plus-duration sample |
| Objective extraction only recognizes English "Objectives" headings and "By the end of this lecture/class/session/unit, students will..." phrasing | Add configurable regex patterns via the (not-yet-built) per-course config file, or a second sentence template for less common phrasings ("Students should be able to...") |
| Section-density and objective-sparsity thresholds (2x mean bullets, 1 objective per 3 sections) are fixed constants, not user-tunable | Expose both as CLI flags once real usage shows the defaults are miscalibrated for a specific course's style |
| No .pptx/.key export — output is Markdown only | Future Feature #6 above |
