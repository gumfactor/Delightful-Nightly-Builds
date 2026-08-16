# Build Log — Curriculum Atlas

> **Date:** 2026-08-16
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:12 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked the most recent build folder present locally (2026-06-18-regex-dojo) and, per CLAUDE.md's instruction that main is frequently weeks behind, resynced against the most recently opened PR branch (`claude/cool-sagan-ucmjrm`, PR #72, 2026-08-15 "Provenance") to find the true most recent build. Its `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — no incomplete build to resume.
- Read `builds/index.md` and `builds/ideas.md` from that same branch (66 builds catalogued, 30 open PRs currently unmerged — normal per this repo's review-before-merge workflow).
- Day of year 228 → category rotation index `(228-1) % 9 = 2` → Category C — Personal Knowledge Tool.
- `builds/ideas.md` backlog holds zero pending Category C rows → skipped the lottery, moved to fresh idea generation (Step 2d).
- Topic diversity check on the last 10 builds: investing appeared twice (Portfolio Lab, Quarter Call) — under the 2-build saturation threshold but noted; no other domain repeated.
- Generated 3 candidate ideas (teaching/curriculum knowledge base; lab SOP knowledge base; AI prompt/workflow cookbook) — chose the curriculum concept/objective knowledge base as the only one targeting a completely uncovered, explicitly-named PROFILE.md domain (teaching, three named courses, zero prior builds across 66). Full reasoning in `WhyThis.md`. The other two ideas appended to `builds/ideas.md`.
- Decided to build: **Curriculum Atlas**.
- Build folder created: `builds/2026-08-16-curriculum-atlas/`.

### [08:20 UTC] PRD Written

- Goal: cross-course concept-overlap and objective-gap knowledge base built from the user's own syllabi/lecture text.
- Scope: deterministic concept extraction (explicit `[[marker]]`, heading-derived, capitalized-phrase heuristic) + deterministic objective extraction + deterministic overlap/gap/diff analysis, all functional with zero network calls; optional Claude Haiku auto-marking (re-verified by the same deterministic parser, never trusted directly) and optional concept notes; self-contained dark-mode HTML dashboard; companion Claude Code Skill.
- Notable design decision: the AI auto-marking layer never invents a concept the deterministic parser doesn't independently re-parse — it only inserts `[[...]]` markers into a copy of the source text, which is then run back through the exact same parser used for hand-marked input. This keeps the tool's core correctness verifiable without any API key, per STANDARDS.md's "never let the LLM directly rank/decide" pattern used by several highly-rated prior builds (Snipvault, Provenance).

### [09:10 UTC] Build Phase — Core Implementation

- Built `src/store.py` (SQLite schema/CRUD), `src/parser.py` (deterministic marker/heading/heuristic concept extraction + objective extraction + name normalization), `src/analysis.py` (Jaccard-based gap scoring, cross-course overlap, term diff — all pure functions), `src/ai_enrich.py` (optional Claude Haiku auto-marking + concept notes via `urllib`, unconditional fallback), `src/report.py` (self-contained dark-mode HTML dashboard, `createElement`/`textContent`-only DOM construction, `</script>`-safe JSON embedding), and `src/cli.py` (argparse entry point wiring all 8 commands).
- Design decision made while implementing `normalize_name`: switched from stripping only the whole normalized string's trailing character to per-word naive singularization, so multi-word concept names like "Coping Strategies" singularize correctly on their plural word rather than only ever affecting the final word of the phrase.
- Wrote 3 hand-authored fixture syllabi (`tests/fixtures/`) with an intentionally shared concept ("HPA axis," present via `[[marker]]` in two different courses) and one intentionally uncovered objective (a saliency-map/interpretability objective in the AI Applications for Psychologists fixture with no matching concept anywhere in that document), so the overlap and gap success criteria could be verified against real parsed data, not just synthetic dicts.

### [09:25 UTC] Tests Written and Run

- Wrote 70 tests across `test_parser.py` (20), `test_analysis.py` (14), `test_store.py` (10), `test_ai_enrich.py` (12), `test_report.py` (6), `test_cli.py` (8) — covering the deterministic extraction sources independently, hand-computed Jaccard reference scores, re-ingest idempotency, mocked-network AI fallback paths (zero real network calls anywhere in the suite), and live XSS-payload string inspection of rendered HTML output.
- One test needed correction before the first full run: `test_extract_heuristic_phrases_filters_common_sentence_starters` used "The Following," but "Following" wasn't in the common-word filter list, so the run wasn't actually all-common-words and correctly wasn't filtered — rewrote the test to "This Is optional reading..." (both words genuinely in the filter list) to test the intended behavior.
- Tests: 70 passed, 0 failed.

### [09:35 UTC] Manual Verification — Real Bugs Found and Fixed

Ran the real CLI end-to-end against all three fixture files (not just mocked unit tests). Two genuine bugs surfaced that the 70 passing unit tests had not caught, because no test had exercised a document's own title line or a line-wrapped objective sentence:

1. **Spurious cross-course "concept."** Every fixture's title line (`# Stress and Coping — Fall 2026`) was being parsed as a heading with a separator (the em dash), producing a bogus concept literally named "Fall 2026" — and since all three fixtures shared that exact term, `overlap` falsely reported "Fall 2026" as a concept shared across all three courses, on top of the real, intended "HPA axis" overlap. Root cause: `extract_headings` didn't distinguish a document's h1 title line from a real h2+ section heading. Fixed by skipping bare h1 headings unless they also carry a `Week N`/`Session N`/etc. prefix (a real section, not a title) — added `H1_ONLY_RE` and the corresponding skip logic in `src/parser.py`, plus two new tests (`test_extract_headings_skips_h1_document_title_line`, `test_extract_headings_h1_with_named_prefix_still_extracts`).
2. **Objective text truncated at a line wrap.** A hand-written objective sentence that wrapped onto a second physical line (`Objective 1: Students will identify at least two risks of using large\nlanguage models in a clinical workflow.`) was captured only up to the first newline, because `OBJECTIVE_RE` matches per physical line. This silently produced a lower (still-not-wrong-direction, but understated) Jaccard gap score against a truncated 8-token objective instead of the full sentence. Fixed by adding `_flatten_soft_wraps`, which joins line-wrapped text within a paragraph (blank lines still separate distinct objectives) before running the objective regex — added two new tests confirming both the join and that blank-line-separated objectives are never merged.

Re-ran the full pytest suite after both fixes (74 tests) and re-verified live: `overlap` now reports only the intended "HPA axis" (2 courses); `gaps` now shows the full un-truncated objective text and correctly flags the two objectives with no matching concept (the AI-summary-critique objective and the saliency-map-interpretability objective) while correctly marking the large-language-models objective as covered.

Tests: 74 passed, 0 failed.

### [09:50 UTC] Manual Verification — Live Browser QA

`render` was run against the 3-course dataset plus a 4th course carrying deliberately injected payloads (`[[<img src=x onerror=alert(1)>]]` as a concept marker, `</script><script>alert(2)</script>` inside an objective sentence). Loaded the rendered file in real headless Chromium (the pre-installed `/opt/pw-browsers/chromium`, driven via a throwaway Playwright script, not committed) rather than only asserting on the HTML string:
- Zero `pageerror`/console-error events, zero `dialog` events (confirming the `onerror=alert(1)` payload never executed).
- `main script` count stayed at exactly the one static script block after render — no injected `<script>` element was ever added to the DOM.
- `main img` count was 0 — the `<img onerror>` payload never became a real image element.
- Both payloads were confirmed present as plain visible text (`bodyText.includes(...)`) in their respective tabs (Courses for the concept marker, Gaps for the objective), proving they render as inert content rather than being silently dropped.
- Exercised the tab switching (Courses/Overlap/Gaps), the live search filter ("HPA" correctly narrowed 4 course cards to 2), and confirmed the Overlap table showed exactly 1 row (the real "HPA axis" overlap) after the h1-title-parsing bug fix above.
All throwaway manual-QA artifacts (test databases, the ad hoc XSS fixture, the Playwright script) were removed before committing — nothing outside the files listed in the PRD's folder structure is part of this build.

### [09:55 UTC] Security Checklist

Grepped `src/` for `eval(`/`exec(`, `os.system`/`subprocess`, hardcoded `api_key=`/`password=`/`secret=` literals, and `innerHTML` — zero matches anywhere in `src/` (the HTML template builds the DOM exclusively via `createElement`/`textContent`/`removeChild`, confirmed both by `test_report.py`'s string assertions and by the live browser check above). No `.env` file. No credentials in source. `ANTHROPIC_API_KEY` is read only via `os.environ.get` in `ai_enrich.get_api_key()`, never hardcoded. No student names, grades, or enrollment data are ever stored — the schema only has courses/documents/concepts/objectives/concept_notes, all instructor-authored content. No file paths are built from unsanitized input beyond the CLI's own `--file`/`--db`/`--out` arguments, which is the same trust boundary as any other CLI tool. Nothing outside this build folder was modified.

### [09:58 UTC] Verify — Step 7

All 5 PRD success criteria reviewed:

1. **Cross-course overlap detection** — met; verified live (not just mocked) that "HPA axis," present via `[[marker]]` in both the Stress and Coping and Social Affective Neuroscience fixtures, is reported by `overlap` against both courses, and covered by `test_analysis.py`'s `test_find_overlap_detects_concept_shared_across_two_courses`.
2. **Objective gap flagging with hand-computed reference score** — met; `test_find_gaps_hand_computed_reference_example` cross-checks the exact Jaccard fraction (2/6) by hand, and the live run correctly flags the AI Applications fixture's saliency-map-interpretability objective (score 0.00, no matching concept anywhere in that document).
3. **Re-ingest does not duplicate** — met; `test_reingesting_same_document_replaces_not_duplicates` and `test_reingest_via_cli_does_not_duplicate_concepts` both assert identical row counts before/after a second identical ingest, and this was also confirmed live via the CLI's own concept listing showing "HPA axis" exactly once after two ingests of the same file.
4. **Zero network calls with no API key** — met; every AI-touching test (`test_ai_enrich.py`, plus `test_ingest_ai_mark_makes_zero_network_calls_with_no_key` and `test_concepts_ai_notes_makes_zero_network_calls_with_no_key` in `test_cli.py`) asserts `mock_urlopen.assert_not_called()`, and deterministic concept/objective output is unaffected by the flag being off.
5. **XSS payload inert in rendered HTML** — met; `test_report.py` unit-tests it via string/JSON inspection, and the live headless-Chromium pass above independently confirms zero dialogs, zero injected `<script>`/`<img>` elements, and the payload text visible only as literal text.

Security checklist: clean, see above.

### [10:00 UTC] Docs

- `FutureFeatures.md`: 7 concrete suggestions.
- `Manual.md`: quick start, command reference, marker syntax, AI-enrichment setup, known limitations, troubleshooting.
- `skill/SKILL.md`: companion Claude Code Skill for `ingest`/`concepts`/`overlap`/`gaps` from within a session.

Build complete. Success criteria reviewed. All tests passing.
