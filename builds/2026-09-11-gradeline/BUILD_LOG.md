# Build Log — GradeLine

> **Date:** 2026-09-11
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:11 UTC] Session Start

- Checked Step 0: most recent dated folder in the local checkout is `2026-06-18-regex-dojo`, whose BUILD_LOG.md ends with "Build complete. Success criteria reviewed. All tests passing." — done, no resume needed.
- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- `builds/index.md` on the local `main`-derived checkout was stale (last entry 2026-06-24, 19 builds). Per Step 1/Step 9, resynced from the most recently opened PR branch (`claude/cool-sagan-l789eu`, PR #95, "Dominion Index", 2026-09-10) — the real catalog has 88 builds through 2026-09-10. Copied that branch's `builds/index.md` and `builds/ideas.md` into the working tree before doing anything else, so tonight's lottery/fresh-idea decision is based on the real history, not the stale local copy.
- Today's UTC date: 2026-09-11. Day of year 254. `category_index = (254-1) % 9 = 1` → **Category B — Productivity Utility**.
- Last 10 builds (2026-08-30 → 2026-09-10): Layer Guard(H), Fleet Drift(A), CiteForge(B), Promptbook(C), CaseForge(D), Mediation & Moderation Lab(E), Almanac(F), True Course(G), Secrets Sentinel(H), Headroom(I), Dominion Index(A). No topic domain appears more than twice — no saturation flag.
- Category B backlog (from the resynced `builds/ideas.md`): 2 pending rows — idea #39 (SubmitCheck: journal formatting compliance checker) and idea #40 (Batch Release Notes Drafter). Both unrated (R=0) → `lottery_chance = min(75, 25 + 0*2) = 25%`.
- Rolled `random.randint(1,100)` (Python `random`, unseeded) → **41**. 41 > 25 → lottery misses, routing to **fresh idea generation** (Step 2d).
- Reviewed Category B's build history (10 prior builds: AI Session Context Bridge 3/10, Morning Briefing 5/10, BIDS Dataset Organizer, Worklog, Protocol Forge, Voiceprint, Manuscript Pipeline, Provenance, Lecture Loom, CiteForge) and PROFILE.md's named friction points. "Student evaluation workflows" is named verbatim in PROFILE.md and has zero prior direct coverage (ItemScope, 2026-08-01, analyzes exam *item* psychometrics, not written-submission grading).
- Generated 3 fresh candidate ideas (see WhyThis.md for full comparison table); selected **GradeLine** — a batch rubric-grading assistant with a genuinely deterministic core (structural compliance checks + from-scratch TF-IDF near-duplicate/similarity detection across a submission batch) and an optional, privacy-conscious Claude Haiku feedback-drafting layer.
- Build folder created: `builds/2026-09-11-gradeline/`.

### [08:22 UTC] PRD Written

- Goal: batch-check a folder of student written submissions against a rubric (structure/word-count/citation/keyword-coverage compliance, deterministic partial scoring, near-duplicate flagging) and optionally draft grounded per-criterion feedback via Claude Haiku.
- Scope: rubric schema + loader/validator, submission parser (folder-of-files or single delimited file), deterministic checks module, from-scratch TF-IDF cosine similarity module, SQLite batch persistence, terminal + HTML report, optional AI feedback layer with unconditional deterministic fallback, CLI, Claude Code Skill wrapper.
- Notable constraints/decisions: AI layer never receives the student identifier/filename in the prompt — only the anonymized submission text and the rubric criterion text — stronger than several prior builds' precedent, to minimize any risk of sending identifiable student data to a third-party service per STANDARDS.md's "no sending user-entered or personal data to a third-party service" hard standard. AI layer is opt-in (`--ai` flag) and requires the user's own `ANTHROPIC_API_KEY`.

### [08:40 UTC] Build Phase — Core deterministic engine

- Implemented `src/rubric.py` (rubric load/validation from JSON), `src/parser.py` (folder-of-files and single-delimited-file submission loading), `src/checks.py` (word count, section/heading detection, citation counting, keyword-coverage scoring, Flesch reading ease), `src/similarity.py` (from-scratch TF-IDF vectorization + cosine similarity, no numpy).
- Cross-checked the TF-IDF/cosine implementation by hand: two identical documents → similarity 1.0; two documents sharing zero vocabulary → similarity 0.0; a partial-overlap pair computed by hand on paper matched the function's output to 4 decimal places before any test was written.

### [09:05 UTC] Build Phase — Persistence, AI layer, rendering, CLI

- Implemented `src/storage.py` (SQLite: batches, submissions, criterion scores, similarity pairs — schema mirrors the `references_lib`/upsert pattern used by prior Category B/C builds in this catalog), `src/ai.py` (Claude Haiku feedback drafting via `urllib.request` against `https://api.anthropic.com/v1/messages`, model `claude-haiku-4-5-20251001`, transport-injected for testing, unconditional deterministic-template fallback, structurally never given the student identifier), `src/render.py` (self-contained dark-mode HTML report — JSON-in-`<script type="application/json">` payload with `</` escaped, DOM built exclusively via `createElement`/`textContent`, Chart.js 4.4.4 per-criterion class-average bar chart with a DOM-table fallback), `src/cli.py` (argparse: `init-rubric`, `grade`, `list`, `show`, `render`, `compare`), `main.py` entry point.
- Ships a companion Claude Code Skill (`skill/SKILL.md`) so a session can run a grading batch on request, following the precedent set by Snipvault/Provenance/Lecture Loom/Promptbook/CiteForge.

### [09:35 UTC] Tests Written and Run

First run: 98 passed, 1 failed (`test_flesch_reading_ease_returns_none_without_sentence_terminator` — the test's own assumption was wrong: text with no `.`/`!`/`?` is correctly treated as one implicit sentence by `flesch_reading_ease`, not `None`; fixed the test to assert the real, correct behavior and added a genuine `None` case, whitespace-only text, instead).

Tests: 99 passed, 0 failed.

### [09:40 UTC] Manual Verification

- Ran the real CLI end-to-end against `sample_data/submissions/` (6 real student fixture files: 4 independent compliant submissions, one planted near-duplicate pair, one deliberately sparse/non-compliant submission): `python3 main.py grade sample_data/submissions --rubric sample_data/rubric_example.json` correctly reported "Non-compliant: 1" (`dan_okafor`: word count, missing sections, citations) and "Similarity flags: 1" (`alice_chen <-> carla_diaz`: 97.6%), exactly as designed. `render` produced a working HTML dashboard.
- Confirmed the `--ai` zero-network-call path live (not just via pytest mocks): monkeypatched `urllib.request.urlopen` at the real module level to raise `AssertionError` if ever called, unset `ANTHROPIC_API_KEY`, and ran `cli.grade_batch(..., use_ai=True)` through the real code path — completed successfully with zero exceptions, confirming zero network calls.
- Live-checked a rendered report in the container's pre-installed headless Chromium (global npm Playwright 1.56.1, `executablePath` pointed at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`, matching this catalog's established pattern for Python-only builds needing a one-off browser check) against a fixture with an identifier containing `</script><script>window.__xss=true;</script>` (using the single-file delimited-submission format, whose `=== NAME ===` identifier is free text — unlike a folder filename, which the filesystem itself would reject for containing `<`/`>`): zero dialogs, the only console message was the CDN request itself failing (`ERR_TUNNEL_CONNECTION_FAILED`, expected/documented), `window.__xss` was never set, exactly 3 `<script>` tags were present in the DOM (the page's own CDN/JSON-payload/inline-logic tags — no 4th, injected one), and the payload rendered as inert visible text. The live search filter was also exercised (2 cards → 1 on a matching query).
- Confirmed the Chart.js CDN is genuinely blocked by this build container's egress proxy (`window.Chart` was `undefined`, and the request errored with `ERR_TUNNEL_CONNECTION_FAILED`) and that the DOM-table fallback rendered correctly instead (2 criterion rows, `hidden` attribute correctly cleared). A 375px mobile viewport check showed zero horizontal overflow (`scrollWidth === clientWidth === 375`).

### [09:55 UTC] Verify — Step 7

Security checklist run against all created files: no `.env`, no hardcoded credentials/secrets, no `eval()`/`exec()`, no `innerHTML` from user data, no `os.system()`/`subprocess` with user-controlled arguments, no path traversal (submission folder path is user-supplied via CLI arg but only ever read, never written outside the target SQLite db the user names), all files within the build folder.

Success criteria reviewed against PRD.md — all met (see Manual.md/PRD.md for detail).

Build complete. Success criteria reviewed. All tests passing.
