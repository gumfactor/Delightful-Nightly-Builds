# Why This — Voiceprint

## Category & Selection Path

Day of year: 209. `category_index = (209-1) % 9 = 1` → **Category B — Productivity Utility**.

## Backlog Correction (before the lottery)

`builds/ideas.md` had exactly two `pending` rows tagged Category B:

- **#4 — Cross-Agent Project Activity Workstreams** (rating 9) — this is, verbatim, the Idea
  Brief that **Worklog** (2026-07-10) already implemented as its first release. The
  2026-07-10 catalog row says so explicitly ("Implements the highest-rated backlog idea (9/10,
  Idea Brief)..."). The backlog row was simply never flipped to `built` at the time.
- **#7 — Morning Briefing** (rating 8) — matches, by title and description, the already-built
  **Morning Briefing** (2026-06-22): GitHub activity + portfolio pulse + weather, combined into
  one daily digest.

Both are stale bookkeeping errors, not live candidates — building either tonight would produce a
zero-differentiation duplicate, the exact failure mode last night's session (SiliconWatch) hit
and worked around. Rather than run a lottery over two ideas that are already-built duplicates, I
corrected both rows to `built` with rationale (see `builds/ideas.md`) first. That leaves the
Category B pending pool empty, so per Step 2c ("If empty: go to Step 2d") this is a **fresh-idea
session**, not a lottery draw.

## Fresh Ideas Considered

Scanned the last 10 builds (2026-07-17 through 2026-07-27) for topic saturation: academic
admin/deadlines, Canadian economics (×2), research ethics, Canadian ownership, research analogies,
Bayesian stats, cognitive-bias game, bug-pattern mining, trip planning, AI/semiconductor stocks.
No domain repeats more than twice — no saturation constraint applies to tonight's candidates.

Checked PROFILE.md's "Things you do manually that you suspect could be automated" list against
the full build catalog. Two items on that list are still completely untouched by any of the 46
builds to date: **"Blog writing and editing"** and **"Student evaluation workflows."**

1. **Voiceprint — AI-Tell & Human Voice Auditor** *(winner)* — a batch CLI that audits a writing
   draft (blog post, book chapter, manuscript prose) for the lexical and structural patterns that
   make prose read as AI-generated or formulaic, scores it, and calls Claude for a holistic
   second opinion on the worst passages. Targets "Blog writing and editing" directly, and also
   the explicitly-remembered preference "I dislike writing that sounds obviously AI-generated" —
   both are named verbatim in PROFILE.md and neither has a prior build.

2. **Student Evaluation Feedback Assistant** — batch-compiles rubric scores into polished
   individual feedback paragraphs via Claude. Passed over: the input is inescapably real student
   names and submission text — sending that to a third-party API, even the user's own key, sits
   uncomfortably close to the STANDARDS.md line on personal data and FERPA-adjacent risk for an
   academic. A tool whose only path to being useful requires feeding it real students' personal
   work isn't a safe design for an unsupervised nightly build. Worth revisiting with a
   privacy-first design (e.g., operating only on anonymized rubric codes, never on student names
   or verbatim submissions) in a future session with more room to think through the safeguards.

3. **Citation/Reference Batch Formatter** — CLI that takes a folder of citation strings or DOIs,
   resolves metadata via the free Crossref API (no auth), reformats to a consistent style, dedupes,
   and emits BibTeX. Genuinely useful for "literature reviews" and "research administration," but
   mechanically thinner than Voiceprint — it's a formatting/lookup pipeline without a real
   judgment layer, closer to the pattern that scored builds like the discarded Quick Data Profiler
   low ("trivially handled by existing tools"). Kept as a backlog idea for a night when Category F
   or B needs a lower-lift, more focused build.

**Winner: Voiceprint.** It's the strongest match for the AI-integration signal (Claude doing real
judgment — identifying *why* a passage reads as formulaic — not mechanical data transformation),
it's self-contained with no external API dependency required for the deterministic core, it
directly serves two named PROFILE.md items with zero prior coverage, and the local SQLite score
history makes it a tool worth re-running across the actual "Stress and Coping" book project over
many sessions rather than a one-off.

## Idea Brief Traceability

No linked Idea Brief — this is a freshly generated idea, not drawn from the backlog.
