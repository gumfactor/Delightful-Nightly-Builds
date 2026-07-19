# Future Features — Protocol Forge

> Ideas for extending this build. The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`diff` command** — Show a section-by-section text diff between two versions of the same study (e.g. an original protocol vs. an amendment), so reviewers can see exactly what changed for a renewal/amendment submission.
2. **`--fail-on blocking|warning` flag on `check`** — Currently `check` always exits 1 on blocking findings; a configurable threshold (like Schema Sentinel's `--fail-on`) would let it gate a pre-submission script on warnings too, or be relaxed to blocking-only.
3. **Export to plain `.txt`** — Many institutional IRB portals want plain text pasted into web form fields, not Markdown. A `--format txt` flag on `draft` would strip Markdown syntax for direct paste.

## Medium Effort (roughly one nightly build session)

4. **Per-institution rule packs** — Externalize the checklist rules (currently hardcoded in `checklist.py`) into a loadable JSON rule pack, so the safeguard keywords and required fields can be tuned to a specific institution's actual IRB requirements rather than the generic set built tonight.
5. **Section-level edit-and-resave** — Right now a drafted section can only be reused wholesale from an approved protocol. Adding a `revise <id> <section_key> --text "..."` command would let the user hand-edit a section after their actual IRB feedback and save the corrected version back into the library as the new canonical boilerplate for that tag profile.
6. **Consent form generator** — A distinct, focused output (not the full protocol) that assembles just a participant-facing informed consent document from the same study JSON, since institutions often want the consent form as a separate submission artifact from the protocol narrative.

## Ambitious Extensions (multi-session effort)

7. **Cross-referencing with Deadline Guardian** — Read Deadline Guardian's SQLite database (if the user runs both tools) to auto-populate a study's renewal due date and flag protocols whose 90-day-out renewal window has opened, without duplicating Deadline Guardian's own recurrence-scheduling logic.
8. **Structured feedback ingestion** — Accept a pasted IRB reviewer feedback letter, use Claude to extract which specific sections/findings it addresses, and pre-fill a `revise` workflow that maps each piece of feedback to the exact section that needs to change — turning "what does the reviewer actually want changed" from a manual re-read into a structured checklist.

---

## Possible Integration Points

- **Deadline Guardian** (2026-07-17) — natural pairing for renewal-date tracking; Protocol Forge intentionally left scheduling out of scope to avoid duplicating that build's recurrence engine.
- **Worklog** (2026-07-10) — a `protocol-forge draft` or `approve` event could be logged as a Worklog checkpoint for cross-project activity tracking, since both are stdlib-only local SQLite tools with compatible data shapes.
- **Research Question Forge** (2026-07-12) — both tools share the "structured taxonomy input → optional Claude polish → persistent local library browsable via CLI" architecture; a shared boilerplate/reuse library pattern could be extracted if a third build in this family gets built.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Tag-based similarity matching can reuse a section from a study with very different procedures but the same coarse tag profile | Add a lightweight text-similarity secondary check (e.g. word-overlap ratio between `procedures` fields) as a tie-breaker or additional gate before the reuse threshold |
| No way to un-approve a protocol if it's later discovered the approved text was wrong | Add an `unapprove <id>` command |
| The AI drafting tier sends the full structured study JSON in one prompt per section (6 separate API calls per draft when no reuse match exists) | Batch all sections needing AI drafting into a single prompt/response to reduce API calls and cost |
| Compliance rules are generic, not institution-specific | See Medium Effort #4 above (rule packs) |
