# Build Log — Voiceprint

## [08:15 UTC] Step 0 — Incomplete build check
`ls builds/` showed only local folders through 2026-06-18-regex-dojo, all with a completed
`BUILD_LOG.md` ("Build complete. Success criteria reviewed."). No resumption needed. Fetched the
most recent open PR branch (`claude/cool-sagan-zyfkw2`, PR #53, 2026-07-27 SiliconWatch) per
Step 2's instruction and synced local `builds/index.md`/`builds/ideas.md` from it — local main was
30 builds behind (last local entry: 2026-06-24; actual last build: 2026-07-27, total 46 builds).

## [08:20 UTC] Step 1 — Orient
Read PROFILE.md and STANDARDS.md. Noted: named untouched friction points "Blog writing and
editing" and "Student evaluation workflows"; explicit remembered preference "I dislike writing
that sounds obviously AI-generated."

## [08:25 UTC] Step 2 — Category & selection
Day of year 209 → `(209-1) % 9 = 1` → Category B (Productivity Utility). Both pending Category B
backlog rows (#4, #7) turned out to be undocumented duplicates of already-completed builds
(Worklog 2026-07-10, Morning Briefing 2026-06-22) — corrected both to `built` status with
rationale in `builds/ideas.md`. That leaves the Category B pending pool empty, so per Step 2c this
proceeds as a fresh-idea session (Step 2d), not a lottery draw. Full reasoning, 3 candidates
considered, and why Voiceprint won: see `WhyThis.md`. Two non-winning ideas appended to
`builds/ideas.md` as #19 and #20.

## [08:35 UTC] Step 4 — PRD written
`PRD.md` complete with Testing Strategy section, before any code.

## [08:40 UTC] Step 5 — Build

Built in dependency order: heuristics → scoring → storage → ai_review → report → cli.
Wrote 67 tests alongside the code, one test module per source module.

Environment note: this container's `python3` has no importable `pytest` (`pip install` is
blocked by the sandbox policy), but a standalone `pytest` 9.0.2 launcher (installed via `uv tool`)
is on `PATH` and works fine with its own bundled interpreter. Added `conftest.py` at the build
root so `pytest` (run from the build folder) resolves `from src.X import ...` correctly without
needing `python -m pytest`. `requirements.txt` pins `pytest==9.0.2` to match. Documented the
actual working command (`pytest tests/ -v`) in Manual.md instead of `python -m pytest`, since that
form isn't usable in this container. Deviation from STANDARDS.md's example command table — not a
scope reduction, just what's runnable here; the user's local `python -m pytest` will also work
once they `pip install -r requirements.txt` since it install pytest into their own interpreter.

## [08:50 UTC] Step 6 — Tests
Tests: 67 passed, 0 failed. `pytest tests/ -v` from `builds/2026-07-28-voiceprint/`.

## [09:05 UTC] Manual verification (beyond the automated suite)
Ran the real CLI end-to-end against a hand-written draft loaded with AI-tell phrases, passive
voice, and a repeated rule-of-three sentence: scored 44.0/100, correctly named 17 AI-tell phrases
with line numbers, flagged passive voice (-10.0) and rule-of-three (-6.0), and the deterministic
`--ai` fallback (no `ANTHROPIC_API_KEY` set) produced paragraph-specific advice with zero network
calls. Rewrote the same file path as a clean, varied paragraph about real lab research — score
rose to 96.2/100, and `history` correctly showed both runs with a +52.2 delta.

Rendered the generated HTML report in headless Chromium
(`/opt/pw-browsers/chromium_headless_shell-1194`, since no Python/Node Playwright package is
importable in this container — used the browser binary directly via `--dump-dom`): zero page
errors. The Chart.js CDN was in fact blocked by this container's egress policy, and the fallback
engaged correctly — `<canvas id="history-chart" ... style="display: none;">` — while the plain
history table below it still rendered both runs' data. Confirmed via the automated
script-injection tests (`test_render_html_escapes_script_injection_in_excerpt`,
`test_render_html_escapes_malicious_file_path`) that no user-controlled text (excerpts, file
paths) reaches the page unescaped.

## [09:15 UTC] Step 7 — Verify

Success criteria (from PRD.md):
1. ✓ Named AI-tell phrases with line number and count — `test_find_ai_tell_phrases_*`,
   `test_render_terminal_lists_ai_tell_phrase_hits`, confirmed live above.
2. ✓ Deterministic, reproducible score; stripped-phrase version scores strictly higher —
   `test_score_is_deterministic_across_repeated_calls`, `test_removing_ai_tell_phrases_strictly_increases_score`,
   confirmed live above (44.0 → 96.2).
3. ✓ Two runs record two history rows with a computed delta —
   `test_cmd_history_records_two_runs_with_delta`, confirmed live above.
4. ✓ `--ai` with no key completes via fallback, zero network calls —
   `test_get_review_uses_fallback_when_no_api_key_and_makes_no_network_call` (asserts the tracked
   call list stays empty), `test_cmd_analyze_with_ai_flag_uses_fallback_with_no_key`.
5. ✓ HTML report has zero unescaped user content and renders correctly, including on a narrow
   viewport (media query in `report.py`'s `<style>`) — script-injection tests plus the live
   headless-Chromium render above.

Security checklist (STANDARDS.md):
- No `.env` files; grepped `src/`, `tests/`, `main.py` for password/secret/private_key/api_key
  literals — only the string `"fake-key"` in test fixtures, no real credentials.
- No `eval()`/`exec()`; no `os.system()`/`subprocess` calls at all — the tool never shells out.
- No dynamic `innerHTML`-equivalent from user data — every user-derived string (excerpts, phrases,
  file paths) goes through `html.escape()` before insertion into the HTML report; the only inline
  `<script>` embeds are numbers and our own generated ISO timestamps, not arbitrary user text.
- File paths (`--db`, `--html`, the draft path itself) are direct CLI arguments the user supplies
  when running the tool locally, the same pattern as every prior CLI build in this catalog (Ledger
  Lens, Deadline Guardian, etc.) — not an externally-facing ingestion path.
- No credentials hardcoded; `ANTHROPIC_API_KEY` is read from the environment only, matching
  PROFILE.md's runtime-only credential model.

## [09:20 UTC] Step 8 — Documentation complete
- `FutureFeatures.md`: 8 concrete enhancements.
- `Manual.md`: setup, full command reference, score interpretation, test command, known
  limitations.

Build complete. Success criteria reviewed. All tests passing.
