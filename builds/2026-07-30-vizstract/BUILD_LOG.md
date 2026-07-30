# BUILD_LOG — Vizstract: Visual Abstract Generator

### [Step 0] Incomplete-build check
Most recent dated folder locally was `2026-06-18-regex-dojo`; its BUILD_LOG.md ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume. Proceeding to tonight's new build.

### [Step 1] Orient
Read `PROFILE.md`, `STANDARDS.md`. Resynced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-4agz2q`, PR #55, created 2026-07-29) rather than the stale local copy on `main` (which only went up to 2026-06-24 / 19 builds; the resynced copy shows 48 builds through 2026-07-29).

### [Step 2] Decide
Day-of-year 211 → category index 3 → Category D (Creative/Generative). Category D backlog in `builds/ideas.md` held zero pending rows → lottery skipped, fresh generation. Full reasoning, saturation check, and 3 candidate ideas logged in `WhyThis.md`. Selected: Vizstract, a deterministic SVG visual-abstract layout engine with optional AI field extraction.

### [Step 3] Build folder created
`builds/2026-07-30-vizstract/` with `src/` and `tests/` subfolders.

### [Step 4] PRD written
Full PRD.md completed before any code — goal, scope, tech stack, data structure, folder structure, testing strategy (19 planned tests), success criteria.

### [Step 5] Build
Implemented in this order: `src/icons.js` (22 hand-authored inline SVG icons), `src/templates.js` (5 declarative design-type templates: compare, correlate, process, survey, prepost — each an array of generic iconBox/connector/iconBadge regions), `src/render.js` (the core layout engine: canvas-based text measurement, a deterministic wrap → shrink-font → ellipsis-truncate `fitText` algorithm, 5 light-background color themes, and the generic region interpreter that turns any template + form data into a full SVG string), `src/library.js` (localStorage CRUD), `src/export.js` (SVG → downloadable .svg; SVG → Canvas → downloadable .png), `src/extract.js` (deterministic regex/keyword extractor + optional direct-browser Anthropic call, `claude-haiku-4-5-20251001`, with `anthropic-dangerous-direct-browser-access` header and a session-only key never persisted), `src/app.js` (form wiring, live preview, library panel, a "New / Clear Form" action added mid-build so one session can independently save multiple abstracts without reloading — reflected back into PRD.md's scope).

Deliberate deviation from this catalog's usual dark-mode dashboard convention: the generated visual-abstract graphic itself is always light/white-background, because it is meant to be embedded in a manuscript, grant PDF, or slide deck, where a dark-mode export would be wrong on arrival. The surrounding page *chrome* (form, buttons, panels) does respect `prefers-color-scheme: dark` via CSS custom properties — STANDARDS.md's "dark/light mode considered" bar is met at the page-chrome level; the export itself is print-convention light-only by design, not an oversight.

Manual visual QA: rendered all 5 templates with representative data and screenshotted each. Two coordinate issues found and fixed — the `process` template's direction-icon badge overlapped the third box by ~20px, and the `survey` template's badge overlapped the "Outcome" box's top edge by ~20px. Both fixed by widening the gap the badge sits in (process) and moving the badge fully above the box with clearance (survey). Re-screenshotted after the fix — all 5 templates now render with no overlapping elements.

### [Step 6] Test run
`npm install` (3 packages, 0 vulnerabilities, cached). `npx playwright test` — 19/19 passed on the second run (first run had 1 failure: a test's sample abstract text didn't actually contain an "N = " pattern the deterministic extractor could match — fixed the test fixture text, not the extractor).

[08:47 UTC] Tests: 19 passed, 0 failed.

### [Step 7] Verify — success criteria check
1. ✓ All 5 templates render non-overlapping, correctly text-fitted layouts — verified by tests 3, 5, 6, 7 and manual screenshot QA of all 5 templates (two overlap bugs found and fixed during that QA).
2. ✓ SVG and PNG downloads produce valid, openable files — verified by tests 11–12 (well-formed SVG markup, non-empty PNG file via real download events).
3. ✓ Local library persists across reload, supports reload/edit/delete — verified by tests 8–10, 18 (independent multi-entry addressability).
4. ✓ AI extraction works against a mocked endpoint; deterministic fallback works with zero network calls when no key is supplied — verified by tests 13–14.
5. ✓ All 19 Playwright tests pass, including both script-injection safety tests (15, 16 — live-typed and library-persisted payloads both verified inert, zero dialogs, zero executed script/img-onerror).

Security checklist (STANDARDS.md):
- No `.env` files, no hardcoded credentials/API keys/secrets — the Anthropic key field is a runtime-only, in-memory browser input, never written to localStorage or disk.
- No personal data hardcoded anywhere.
- No calls to paid/auth-required APIs without credentials listed in PROFILE.md — the only external call (Anthropic) is optional, user-key-gated, and PROFILE.md lists Anthropic API as available.
- No `eval()`/`exec()` on user-controlled input.
- No unsafe `innerHTML` from user-controlled data — every user string reaches markup exclusively through `render.js`'s `escapeXml()`, verified live by tests 15–16 against `<script>` and `<img onerror>` payloads in both the live-typing path and the localStorage-persisted/reload path.
- No `os.system()`/`subprocess`/shell calls anywhere (pure browser JS + a static file server used only for tests).
- No file-path traversal — `test-server.js` normalizes and bounds-checks every requested path to the build root.
- No code reads from paths outside this build's own folder.

### [Step 8] Documentation
FutureFeatures.md (7 suggestions) and Manual.md written.

Build complete. Success criteria reviewed. All tests passing.
