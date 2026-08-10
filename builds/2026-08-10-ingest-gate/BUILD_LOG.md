# Build Log — Ingest Gate: CSV Quality Inspector for The Canada List

> **Date:** 2026-08-10

---

### [Orient] Step 0–2 — Session start
- [08:20 UTC] Checked `builds/` for interrupted sessions: last dated local folder (`2026-06-18-regex-dojo`) has a completed `BUILD_LOG.md` ("Build complete. Success criteria reviewed. All tests passing."). No resume needed.
- [08:20 UTC] `gh` CLI unavailable in this environment; used GitHub MCP `list_pull_requests` + `git fetch`/`git show` against the most recent open PR branch (`claude/cool-sagan-8259vy`, PR #66, 2026-08-09) to pull the current `builds/index.md` (95 catalog rows) and `builds/ideas.md` into the local working tree before proceeding, per CLAUDE.md Step 2/Step 9 resync instructions.
- [08:20 UTC] Read `PROFILE.md`, `builds/index.md`, `STANDARDS.md` in full.
- [08:21 UTC] Day of year 222 → category index `(222-1) % 9 = 5` → **Category F — Data Explorer**.
- [08:21 UTC] Category F backlog: 2 pending rows (ID 1, rated 7; ID 10, unrated → 5 tickets). R=1 rated idea → lottery_chance = 27%. Roll 9 ≤ 27 → draw. Weighted roll 5/12 → ID 1 (The Canada List CSV Quality Inspector) wins. Marked `built` in `builds/ideas.md`.
- [08:22 UTC] Referenced an existing catalog build (`2026-07-31-signal-detection-lab`, on remote branch `claude/cool-sagan-yfwo5m`) via `git show` to confirm the established convention for direct-browser Anthropic API calls (endpoint, headers, model id, session-only-key/never-persisted pattern, Playwright `page.route` mocking) before writing this build's own AI module, for consistency with the rest of the catalog.

### [Plan] Step 3–4 — PRD
- [08:25 UTC] `PRD.md` written and complete — no placeholders.

### [Build] Step 5 — Implementation
- [09:05 UTC] Built `src/csv-parser.js` — from-scratch RFC4180-style tokenizer (quoted fields, embedded commas/newlines, `""` escapes, CRLF/LF, BOM strip, ragged-row detection).
- [09:15 UTC] Built `src/schema.js` — default Canada-List-style preset (business_name, website, category, province_territory, canadian_ownership_pct, notes), localStorage load/save, JSON import/export, "infer from header" helper.
- [09:30 UTC] Built `src/validator.js` — header-level + per-row + per-type validation engine, error/warning severities.
- [09:35 UTC] Built `src/dedupe.js` — exact full-row duplicate detection + per-unique-column normalized-key duplicate detection (case/whitespace/URL-protocol-insensitive).
- [09:40 UTC] Built `src/history.js` — aggregate-only localStorage run history (no raw row content ever stored).
- [09:45 UTC] Built `src/report.js` — cleaned-CSV-with-QC_Flags generator and issues-only CSV generator.
- [09:50 UTC] Built `src/ai-briefing.js` — direct-browser Anthropic Messages API call (Claude Haiku, session-only key, `fetchImpl` injectable for testing) sending only aggregate counts, with an unconditional deterministic template fallback. Matches the established repo convention confirmed against `signal-detection-lab`.
- [10:10 UTC] Built `src/app.js` — DOM wiring: drag-drop/file upload, encoding selector, tab switching (Validate / Schema / History), results table render with search/filter/sort, row detail view, download buttons, AI briefing button.
- [10:15 UTC] Built `src/styles.css`, `index.html`.
- [10:20 UTC] `package.json` / `playwright.config.js` created following the `regex-dojo` build's established pattern (pinned `@playwright/test`, local chromium executable path).

### [Test] Step 5–6 — Tests
- [10:45 UTC] Wrote `tests/ingest-gate.spec.js` covering parser edge cases, validation rules, dedupe, encoding, summary counts, CSV export content, UI interactions, XSS-safety, and the three AI-briefing paths (no key / mocked success / mocked failure), plus history persistence.
- [10:50 UTC] Bug found and fixed during test-writing: `app.js`'s original summary-folding logic patched `errorRows`/`validRows` with a delta that assumed every row newly flagged by dedupe had previously been *valid* — but a row can move from *warning* (e.g. whitespace) straight to *error* (duplicate key), which the delta got wrong (could under/over-count and even go negative). Rewrote it to recompute a combined per-row severity array from scratch (validator severity, upgraded to `error` by any dedupe finding) and derive all three counts from that array, verified against the seeded fixture (1 valid / 5 errors / 0 warnings across 6 rows).
- [10:52 UTC] `npm install` succeeded (registry reachable from this container for `@playwright/test`), `package-lock.json` committed.
- [11:05 UTC] Ran `npx playwright test`.
- [11:05 UTC] Tests: 44 passed, 0 failed.

- [11:10 UTC] Manual visual QA in headless Chromium (screenshots of all three tabs against the seeded fixture) per session guidance to verify UI changes in a real browser, not just tests. Found and fixed a real bug the automated tests missed: `validator.js`'s `makeIssue()` message-templating conflated a generic "extra" parameter with the (column, value) pairing most message templates need, so `invalid_url`/`invalid_enum`/etc. messages rendered `"undefined" in column "X"...` instead of the actual offending value, and `malformed_row` rendered `expected null` instead of the real header length (the header length was never even passed to the message function). Rewrote `makeIssue` to default to `(column, value)` templating and take an explicit `messageArgs` override only for `malformed_row`'s `(expected, actual)` shape; re-ran the full suite (still 44/44) and re-screenshotted to confirm correct text.
- [11:12 UTC] Re-verified all 3 tabs (Validate results/row-detail, Schema editor, History) visually — correct layout, dark-mode default rendering, zero console/page errors.

### [Verify] Step 7 — Success criteria check
1. ✓ All tests pass (44/44) — confirmed above
2. ✓ Seeded fixture with malformed row, missing required value, bad URL, duplicate business name, and invalid enum surfaces every one of those issues with correct row/column attribution — verified by "validateFile computes correct total/valid/error/warning counts" and the full "App integration" upload tests
3. ✓ A fully-valid CSV produces zero errors/warnings and 100% valid rows — verified by "a clean file with no issues reports 100% valid rows"
4. ✓ Cleaned-CSV download contains a correctly populated `QC_Flags` column — verified by "buildCleanedCsv appends a QC_Flags column" (unit) and "downloading the cleaned CSV produces a file containing the QC_Flags column" (integration)
5. ✓ No CSV row content is ever sent over the network — the AI briefing module's only input is the aggregate `summary` object (counts + issue-code tallies, never a row or cell); verified structurally by "the AI prompt contains only aggregate counts, never a raw cell value" and behaviourally by "generateBriefing with no API key... makes zero network calls" (route-hit counter assertion)

Security checklist (STANDARDS.md):
- No `.env` files
- No hardcoded credentials, API keys, or secrets (the Anthropic key is a runtime-only, session-held browser variable, never written to storage or source)
- No `eval()`/`exec()` on user-controlled input
- No `innerHTML` assignment from user-controlled data — all row/issue/history rendering uses `textContent`/`createElement`; the only `innerHTML` writes in the codebase are `= ''` clears, verified live against an `<img onerror>` + `</script><script>` payload in a CSV cell with zero dialogs and zero injected DOM nodes (see the XSS test)
- No `os.system()`/`subprocess`/shell calls anywhere (pure client-side JS)
- No file-path traversal — all file access is via browser File/Blob APIs, no server-side paths
- All files confined to this build folder

### [Docs] Step 8 — Documentation
- `FutureFeatures.md`: 6 concrete enhancements
- `Manual.md`: usage guide, schema configuration walkthrough, test command

Build complete. Success criteria reviewed. All tests passing.

### [Post-review] PR #67 automated review follow-up
GitHub Copilot and Codex both auto-reviewed the PR. Five substantive, correct findings across the two, all fixed:

1. **`report.js` — ragged rows exported un-padded.** `buildCleanedCsv` appended `QC_Flags` to the raw row array as-is, so a malformed (ragged) row produced a structurally ragged line in the "cleaned" CSV export too — exactly the kind of file this tool exists to prevent. Added `normalizeRowWidth()` to pad short rows / truncate long rows to `header.length` before export. New tests: padding and truncation cases.
2. **`csv-parser.js` — unterminated quoted field silently accepted (P1).** If EOF was reached mid-quote (e.g. a truncated file ending in `"unterminated`), the tokenizer flushed the partial field as if the quote had closed cleanly, and since the field count still matched the header, the row could pass as fully valid. `tokenize()` now reports `unterminatedQuote`, and `parseCSV()` flags the affected (last) row as ragged. New test confirms it's caught.
3. **`app.js` — encoding dropdown had no effect after upload (P2).** The encoding-warning banner tells the operator to "switch to Windows-1252 and re-upload," but changing the dropdown didn't re-run anything — the file object was never retained. Now stores `state.currentFile` and re-invokes `handleFile` on an encoding-select `change` event. New test uses a byte (`0xE9`) that's invalid UTF-8 but valid Windows-1252 `é`, confirming the error count and warning banner actually change after switching, not just cosmetically.
4. **`validator.js` — missing required header didn't propagate to row/file totals (P1).** When a required column was entirely absent from the header, `validateRow` silently skipped it (nothing to check per row), so a file missing a required column could have every row reported as valid, and History/the AI briefing could both claim the file was ready to ingest despite the blocking header-level error. Now every row also gets an explicit `missing_required_value` issue for a required-but-absent column, so the summary/history/briefing all correctly reflect the failure. New test asserts `errorRows` covers every row and `validRows` is 0.
5. **`dedupe.js` — exact-row duplicate check wasn't actually exact (P2).** `findExactRowDuplicates` normalized (lowercase + whitespace-collapse) every field before comparing, contradicting the documented "exact" vs. "unique-column" (normalized) distinction in the PRD/Manual — two rows differing only in case, with no unique column configured, were wrongly flagged as duplicates. Switched to literal field values; also fixed a latent join-collision bug (`['ab','c']` and `['a','bc']` could hash to the same key) by joining with a control-character separator instead of `''`. Two new tests cover both.

Added 7 new regression tests (44 → 51) plus updated `playwright.config.js` to fall back to Playwright's default browser resolution when the pinned CI Chromium path doesn't exist (a 6th, lower-severity Copilot finding about contributor-machine portability). Re-ran the full suite: 51 passed, 0 failed. Re-ran the byte-level control-character scan across every source/test/doc file after these edits — clean.

Tests: 51 passed, 0 failed.
