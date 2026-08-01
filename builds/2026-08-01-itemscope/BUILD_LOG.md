# Build Log — ItemScope

> **Date:** 2026-08-01
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:15 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md in full.
- Checked `ls builds/` for an interrupted build: most recent local dated folder is `2026-06-18-regex-dojo`. Its BUILD_LOG.md ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Local `builds/index.md` was stale (last entry 2026-06-24). Per CLAUDE.md's Step 1 instructions, resynced from the most recent open PR branch (`claude/cool-sagan-yfwo5m`, PR #57, 2026-07-31 "Signal Detection Lab") — true catalog runs through 2026-07-31, 50 total builds, 47 complete / 3 discarded. Copied that branch's `builds/index.md` and `builds/ideas.md` into the working tree before proceeding, as instructed.
- Today is 2026-08-01 UTC. `date +%j` = 213. `category_index = (213-1) % 9 = 5` → **Category F — Data Explorer**.
- Category F history in the synced catalog: Quick Data Profiler (06-08, discarded, 1/10 — "redundant with pandas"), Qualtrics Survey Data Inspector (06-17, complete, **9/10 — highest-rated build in the catalog**), GitHub Developer Activity Explorer (06-26), TrialScope Behavioral/RT QC Explorer (07-05), GrantScope NIH funding explorer (07-14). The 9/10 Qualtrics build is the clearest signal: research-data QC tools with a verifiable statistical core and a real report (not just a stdout printer) score well for this user.
- Checked `builds/ideas.md` for pending Category F rows: #1 "The Canada List CSV Quality Inspector" (rating 7) and #10 "SEC EDGAR Financial History Extractor" (rating —, unrated). R (count with numeric rating) = 1. `lottery_chance = min(75, 25 + 1*2) = 27%`. Rolled a random integer 1–100 via `python3 -c "import random; print(random.randint(1,100))"` → **54**. 54 > 27, so no draw — proceeding to fresh idea generation (Step 2d).
- Build folder created: `builds/2026-08-01-itemscope/`

### [08:25 UTC] Idea Generation

Reviewed the last 10 builds (2026-07-21 through 2026-07-31) for topic saturation: Bridgework (D, neuroscience analogies), Bayes Lab (E, Bayesian stats), Heuristic Hunt (G, cognitive bias game), BugTrace (H, git mining), TripKit (I, travel), SiliconWatch (A, AI-infra investing), Voiceprint (B, writing quality), Citation Vault (C, reading tracker), Vizstract (D, visual abstracts), Signal Detection Lab (E, SDT trainer). Investment/finance appears once (SiliconWatch) — not saturated (threshold is >2). No Category F entries at all in the last 10, so no direct duplicate risk within the recency window; checked the full catalog for all-time F duplicates instead (see above).

Three fresh Category F candidates generated:
1. **ItemScope** — CSV-in exam/quiz item-analysis tool: per-item difficulty (p-value), point-biserial discrimination, KR-20/Cronbach's alpha reliability, optional MCQ distractor analysis (upper/lower 27% split), flagged-item report, dark-mode HTML dashboard with a difficulty-vs-discrimination quadrant chart, optional Claude Haiku plain-English item-revision guidance.
2. SEC EDGAR Multi-Year Financial Trend Explorer — cross-ticker XBRL company-facts extraction and growth-trend comparison.
3. Neuroimaging Motion/QC Explorer — parses fMRIPrep-style confound TSVs across subjects, flags high-motion subjects for exclusion.

Selected **ItemScope**. Full rationale in `WhyThis.md`. Idea 2 and 3 appended to `builds/ideas.md` as new pending rows (IDs 27, 28) since they were not the winner.

### [08:40 UTC] PRD Written

- Goal: turn a CSV of student item-level exam/quiz responses into a psychometric quality report (item difficulty, discrimination, distractor health, test reliability) with a flagged-item action list.
- Scope: stdlib-only Python CLI, deterministic statistics (no AI required for the core), optional Claude Haiku narrative layer for the worst-scoring items with a template fallback, dark-mode self-contained HTML report, terminal/JSON output modes.
- Notable decision: point-biserial and KR-20 math will be implemented from scratch and cross-checked against hand-computed reference values in tests, following the pattern that produced the catalog's highest-rated build (Qualtrics Inspector, 9/10) and its closest analog (TrialScope).

### [09:40 UTC] Build Phase

Implemented `src/itemscope/stats.py` (p-value, point-biserial with corrected-item-total, KR-20, distractor upper/lower split, zero-variance guards), `src/itemscope/parser.py` (CSV response-matrix + optional answer-key + optional raw-option-letter loader with column auto-detection), `src/itemscope/report.py` (text/JSON/HTML renderers, HTML-escaped throughout), `src/itemscope/ai.py` (optional Claude Haiku narrative via `urllib`, deterministic template fallback, no key required), and `src/itemscope/cli.py` (argument parsing, `analyze` command).

Obstacles:
- Point-biserial is undefined when an item has zero variance (everyone right or everyone wrong) — guarded with a explicit "undefined (zero variance)" result rather than a NaN/crash, and the item is still flagged as too-easy/too-hard on the p-value alone.
- KR-20 requires the sum of item variances vs. total-score variance; for a single-item test the reliability is not meaningful — guarded to report `None` with an explanatory note rather than dividing by (k-1)=0.
- Upper/lower 27% split needs at least 2 students in each group to be meaningful; for small classes it widens to whatever split is available and labels the result as "small-N" so the report never claims false precision.

### [10:05 UTC] Tests Run

Tests: 47 passed, 0 failed (`/root/.local/bin/pytest tests/ -v`, using `conftest.py` to put `src/` on `sys.path`). One test assertion (`test_html_report_escapes_script_injection_in_item_id`) was initially wrong about which half of a `<script>...</script>` payload gets escaped — fixed the assertion to match the actual (correct) behavior: the `_safe_embed` escape only rewrites `</` sequences, so an opening `<script>` tag in an item ID stays literal while the closing `</script>` is neutralized to `<\/script>`, which is sufficient to prevent the embedded JSON from breaking out of its surrounding `<script type="application/json">` block.

### [10:15 UTC] Sample Data + Live Verification

Generated two deterministic sample datasets (`sample_data/`): a 24-student, 8-item binary-scored CSV with one item of each interesting type (well-behaved, hard-but-good, too-easy, too-hard, negatively-discriminating/miskeyed, moderate, all-correct, all-wrong), and a 24-student, 6-item raw-option CSV + answer key designed to exercise both distractor flags. The first raw-option design accidentally assumed the upper/lower 27% scoring groups would align with simple student-index order; computing total scores from the actual item design showed the real upper group didn't include the students I'd targeted, so the reversed-distractor-pull demo didn't trigger. Redesigned the item thresholds so total score is monotonic in student index (verified by directly computing `_upper_lower_split` on the resulting totals before finalizing the CSV), then re-ran `analyze()` and confirmed both `non_functioning_distractor` (item q1, option C) and `reversed_distractor_pull` (item q2, option D) fire as intended, alongside `too_hard` on q4/q5.

Ran both sample CSVs through the actual CLI (`--format json` and `--format text`) and hand-verified every p-value and discrimination sign against the deterministic design (e.g. q5's negative discrimination of -0.634 on the binary sample matches its "low-ability students get it right" construction; the zero-variance items q7/q8 correctly report `"undefined (zero variance)"` instead of a number).

Verified the HTML report live in headless Chromium (via the system Playwright Node install at `/opt/node22/lib/node_modules/playwright`, since no Python Playwright binding was available in this container): 6-row item table populated, flagged-items panel listed exactly the 4 expected flagged items, column sort and item-ID search both worked, zero page errors, zero dialogs. Separately rendered a report with an `<img src=x onerror="window.__pwned=true">` payload as an item ID and confirmed live that `window.__pwned` stayed `undefined`, zero page errors, zero dialogs fired, and the payload appeared as inert row text — the JSON-embedding + `textContent`-only rendering approach holds up against a real injection attempt, not just a string-matching test.

### [10:35 UTC] Verify — Step 7

Checked all 5 PRD success criteria against the working build:
1. All 47 tests pass — confirmed above.
2. Sample-data p-values/discrimination/KR-20 hand-verified against the deterministic design — confirmed above.
3. HTML report renders with populated quadrant chart, sortable/searchable table, and flagged panel; injected payload verified inert live in headless Chromium — confirmed above.
4. Zero-variance items (q7/q8 in the binary sample) report `"undefined (zero variance)"`; single-item KR-20 and zero-variance-total KR-20 both covered by `test_kr20_single_item_not_meaningful` / `test_kr20_zero_variance_total_not_meaningful` — no crash, no NaN.
5. Ran with no `ANTHROPIC_API_KEY` set (deterministic template path, `test_template_fallback_used_when_no_api_key` asserts `urlopen` is never called) and separately with a mocked `urlopen` (`test_ai_path_used_when_key_provided_and_call_succeeds`) — no live network call in either path.

Ran the STANDARDS.md security checklist: no hardcoded credentials, no personal data, no `eval`/`exec`, no `os.system`/`subprocess` with user input, no file paths built from unsanitized user input, HTML report escapes/neutralizes every user-supplied string (verified both by unit test and live in headless Chromium against two different injection payloads), no calls to non-listed paid APIs (Anthropic call is optional/runtime-only per PROFILE.md, and disabled by default unless `--ai` is passed or the key is present).

### [10:45 UTC] Documentation

- `Manual.md` — usage guide, both CSV format specs, flag-meaning table, run commands, `--ai` usage, known limitations.
- `FutureFeatures.md` — 6 concrete enhancements.

Build complete. Success criteria reviewed. All tests passing.
