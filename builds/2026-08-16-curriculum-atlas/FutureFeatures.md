# Future Features — Curriculum Atlas

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **PDF/DOCX ingestion** — accept a syllabus PDF or Word doc directly (via `pdfplumber`/`python-docx`) instead of requiring a plain-text export first. The parser itself needs no changes; only a text-extraction step ahead of `parse_document`.
2. **`--min-course-count` on `overlap`** — currently any concept in 2+ courses is reported; a flag to require 3+ would help once the catalog grows past a handful of courses and 2-way overlaps become noisy.
3. **Export gaps/overlap as CSV** — a `--csv` flag on `gaps`/`overlap` for pasting straight into a course-prep spreadsheet.
4. **Configurable objective-phrase patterns** — expose `OBJECTIVE_RE`'s phrase list as a small JSON config file so a professor using different syllabus boilerplate ("Learning outcomes:", "SLOs:") can add their own patterns without editing source.

## Medium Effort (roughly one nightly build session)

5. **Term-over-term overlap trend on the dashboard** — currently `diff` is a CLI-only command; surfacing it as a fourth dashboard tab (concept churn per course, plotted across all ingested terms) would make curriculum drift visible without running a command.
6. **Fuzzy/normalized concept matching** — a documented limitation is that "HPA axis" and "hypothalamic-pituitary-adrenal axis" are only unified if hand-marked identically. An optional Claude Haiku pass that proposes concept-name aliases (never auto-merges, always shows a confirm-list) would close this gap while staying honest about the semantic-matching limitation.
7. **Objective coverage by concept source** — right now `gaps` treats all matching concepts equally regardless of source (marker/heading/heuristic). Weighting marker-sourced concepts more heavily in the Jaccard match (since they're author-confirmed) could reduce false "covered" results from a heuristic false-positive.

## Ambitious Extensions (multi-session effort)

8. **Multi-instructor / TA collaboration** — the current schema is single-user by design (no student data, no auth). A shared-course mode where a co-instructor's ingests merge into the same course record, with per-document attribution, would grow this into a real departmental curriculum-mapping tool.
9. **Accreditation-report generation** — many psychology programs need to demonstrate learning-objective coverage for accreditation reviews (e.g., APA). A report mode that rolls up gap analysis across every course in a program, with AI-assisted narrative summary, would turn this from a personal tool into something exportable for a department chair.

---

## Possible Integration Points

- **Panel Prep (2026-08-08)** shares the "deterministic checklist scored by a rule engine, AI only narrates" pattern this build follows for gap-flagging — a shared "coverage scoring" library could be extracted if a third build in this family gets built.
- **Bridgework (2026-07-21)** already generates cross-domain teaching analogies for this user's stress/empathy/psychopathy research; Curriculum Atlas's concept extraction could feed Bridgework a real list of concepts actually taught this term, rather than requiring manual topic entry.
- **Connectome (2026-07-11)**'s general-purpose note-indexing engine and this build's course-specific extraction are architecturally related (both extract and link named concepts from personal documents) — worth cross-referencing if either is extended, so effort isn't duplicated a third time.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Plain text/Markdown only, no PDF/DOCX | Quick Win #1 above |
| Semantic concept matching is not supported — only exact normalized-name matching | Medium Effort #6 above |
| The capitalized-phrase heuristic can pick up proper nouns that aren't concepts (e.g. cited author names) | Encourage `[[marker]]` use in Manual.md (done); consider a stoplist of common academic-citation patterns (et al., surname-year) as a future refinement |
| `gaps`'s Jaccard scoring treats every concept source equally | Medium Effort #7 above |
