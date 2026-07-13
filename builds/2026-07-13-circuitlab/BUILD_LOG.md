# Build Log — CircuitLab: Affective & Forensic Neuroscience Circuit Trainer

> **Date:** 2026-07-13
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [Session Start]

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked local `builds/` for an incomplete build. Most recent local dated folder is `2026-06-18-regex-dojo`, whose `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume. (`2026-06-08-quick-data-profiler-DISCARDED` also ends complete; it predates the current folder-naming convention but is finished work, not an interrupted build.)
- Orientation resynced from the most recent open PR branch (`claude/cool-sagan-595da6`, PR #39, 2026-07-12) rather than `main`, per CLAUDE.md — `main` is far behind; 30 build PRs are currently open and unmerged (noted for awareness only; out of scope to fix tonight, and the 2026-07-09 Pipeline Pulse build already exists specifically to track this).
- Day of year 194 → category_index 4 → Category E — Learning Aid.
- `builds/ideas.md` (resynced copy) has no pending Category E rows → fresh idea generation.
- Selected: CircuitLab, an interactive brain-circuit trainer for affective/forensic neuroscience. Full reasoning in `WhyThis.md`.

### [PRD Written]

- Goal: interactive labeled-diagram + quiz trainer for the specific brain regions/circuits central to the user's own research (empathy, psychopathy, stress) and teaching (Social Affective Neuroscience).
- Scope: 13 regions across 2 SVG views, 3 quiz modes (Label / Function Match / Circuit Trace), local mastery tracking, and a Case Vignette mode with a curated fallback bank plus optional AI-generated vignettes gated behind a user-supplied Anthropic key.
- Key decision: no bundler, classic scripts, opens via `file://` directly — matches the pattern of prior successful browser builds (Regex Dojo, Power Lab, Synapse Sort).
- Key decision: the optional AI vignette call runs directly from the browser to `api.anthropic.com` using the `anthropic-dangerous-direct-browser-access` header with a user-pasted, session-only (never persisted) key, since this is a pure client-side build with no server component to proxy the call through. All tests mock this call — no live network access occurs in tests.

### [Build Phase — Content & Data]

- Curated 13 regions (6 lateral: dlPFC, vlPFC, anterior insula, STS, temporal pole, TPJ; 7 medial/subcortical: vmPFC, OFC, ACC, amygdala, hippocampus, hypothalamus, ventral striatum) with function + empathy/psychopathy/stress research-relevance notes, written from established, well-replicated findings (e.g. Blair's amygdala/psychopathy work, insula/ACC empathy-for-pain literature, HPA-axis stress circuitry) without inventing specific fabricated citations.
- Defined 6 circuits (fear conditioning & extinction, cognitive reappraisal, empathy for pain, reward-based decision making, HPA-axis stress response, mentalizing/theory of mind), each a 3–4 region ordered sequence built only from the 13 defined regions.
- Wrote 8 curated case vignettes with a target region, optional target circuit, and explanation, so Vignette Mode is fully usable with zero network access.

### [Build Phase — Diagram & App]

- Built two schematic SVG brain views (lateral surface, medial/subcortical cutaway) by hand in `index.html`, each region a clickable `<path>`/`<ellipse>` with `role="button"`, `tabindex="0"`, and `aria-label` for keyboard/screen-reader access.
- `src/mastery-store.js`: localStorage read/write/reset for the 0–3 mastery levels and last-session summary, isolated so it's easy to unit-exercise via the browser console and via Playwright's `page.evaluate`.
- `src/quiz-engine.js`: pure functions for building question queues and scoring each of the 3 modes plus vignette mode, kept side-effect-free from DOM code so mastery-update logic is directly testable.
- `src/brain-diagram.js`: view switching, region highlight/select/color-by-mastery.
- `src/ai-vignette.js`: builds the Anthropic request (model, headers, JSON-schema-constrained prompt) and parses the structured response; the actual `fetch` is the only network call in the whole build and only fires on explicit user action with a user-supplied key.
- `src/app.js`: wires everything, mode/view switching, session summary screen, reset control.

### [Tests Written]

- `tests/diagram.spec.js` (7 tests) — both views render, all 13 regions clickable/labeled, view switching, region detail content, keyboard reachability, no console errors while browsing every region.
- `tests/quiz-modes.spec.js` (13 tests) — Label Mode, Function Match Mode, Circuit Trace Mode correctness, choice/click answer paths, out-of-order rejection, mastery increment on success, double-click-after-answer guard.
- `tests/mastery.spec.js` (7 tests) — fresh-state defaults, localStorage persistence across reload, diagram mastery-N CSS class reflects stored level, incorrect-answer reset, Reset Progress clears storage, malformed localStorage handled without a crash, full 13-question session summary accuracy.
- `tests/vignette.spec.js` (10 tests) — offline curated bank works with no key and zero network requests; Generate button gated on key presence; mocked `page.route()` for the AI success and error paths (no live network calls); malformed/empty key handled without a call; direct-browser-access header present and the key never leaks into page HTML.

Ran the diagram spec first as an early smoke check before writing the rest — caught one test-authoring bug (a region click attempted against a region not in the currently-visible view) and fixed it immediately.

After all four spec files were written, took two manual headless-Chromium screenshots (lateral view, medial view) via a throwaway Node script to sanity-check the hand-authored SVG diagram actually reads as a brain and isn't visually broken. The first medial-view screenshot showed the amygdala/hypothalamus/hippocampus cluster overlapping and hard to read; repositioned those three regions plus vmPFC/OFC/ACC/ventral striatum with wider spacing (index.html region coordinates only — no logic changes), re-screenshotted to confirm the fix, then re-ran the full suite to confirm nothing broke.

### [Tests Run]

Tests: 37 passed, 0 failed (initial run: 36 passed, 1 failed on a test-authoring bug in diagram.spec.js, fixed and re-run clean; full suite re-run clean again after the medial-view layout fix).

### [Verify] Step 7 — Success criteria check

1. ✓ All 37 tests pass — confirmed above (final clean run: 37 passed, 0 failed)
2. ✓ All 13 regions across both views clickable/labeled with correct content — verified by diagram.spec.js, confirmed visually via headless-Chromium screenshots after the layout fix
3. ✓ All 3 quiz modes function with correct scoring/mastery updates — verified by quiz-modes.spec.js
4. ✓ Mastery persists across reload and reflects on diagram — verified by mastery.spec.js
5. ✓ Vignette Mode works fully offline; AI path gated and mocked — verified by vignette.spec.js

Re-ran the security checklist below directly against source (grep for eval/exec, innerHTML, hardcoded secrets) rather than by inspection alone: the 5 `innerHTML` occurrences in `src/app.js` are the `escapeHtml()` helper itself, two static string-literal placeholders, and two `= ''` clears — every dynamic value rendered anywhere in the app (including AI-generated vignette text) goes through `textContent`, confirmed by grep.

Security checklist:
- No `.env` files
- No hardcoded credentials — the Anthropic key field is a runtime-only, in-memory, session-scoped input; never written to localStorage or any file
- No `eval()`/`exec()` on user-controlled input
- No `innerHTML` assignment from unescaped user-controlled data (vignette/AI text is inserted via `textContent`/escaped helper)
- No file paths from user input
- Only outbound network call is the explicit, user-triggered Anthropic request; the user's own vignette answer is never sent anywhere
- All code self-contained in the build folder

### [Docs] Step 8 — Documentation complete

- FutureFeatures.md: 8 concrete suggestions
- Manual.md: usage guide, region/circuit reference, AI setup instructions, test command

Build complete. Success criteria reviewed. All tests passing.
