# Build Log — Lexicon

> **Date:** 2026-08-02
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:05 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md
- Checked local `builds/` for an interrupted prior session: most recent local dated folder is `2026-06-18-regex-dojo`, whose BUILD_LOG.md ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume
- Resynced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-lfghy7`, PR #58, 2026-08-01) rather than the stale local `main` copy (5 folders locally vs. 51 total builds tracked in the catalog)
- Day of year 214 → category rotation index 6 → Category G — Game / Puzzle
- Lottery: 2 pending Category G backlog rows, both unrated (0 rated → 25% draw chance). Rolled 32 → fresh-idea path
- Decided to build: Lexicon — a daily letter-guessing word puzzle using real neuroscience/stats/AI/investing vocabulary
- Build folder created: `builds/2026-08-02-lexicon/`

### [08:12 UTC] PRD Written

- Goal: cross-domain technical-vocabulary Wordle-style daily puzzle with deterministic daily word, hint system, optional AI bonus hint, and persistent stats
- Scope: 48-word curated bank (12 each: neuro, stats, AI, finance), daily + practice modes, duplicate-letter-correct feedback logic, colorblind mode, share grid
- Notable decision: guesses are validated only as A–Z strings of the right length, not against an external dictionary — the word bank is small and domain-specific, so a "must be a real word" check would need a bundled dictionary for no real gameplay benefit

### [08:20 UTC] Build Phase — Word bank and core logic

- Wrote `src/words.js`: 48 entries across 4 categories, each with an accurate one-sentence clue. Verified no duplicate words, all uppercase A-Z, lengths 5-10.
- Wrote `src/main.js`: deterministic seeded shuffle (mulberry32 PRNG, fixed seed) fixes a 48-word cycle order once at load; day-of-cycle index = days since a fixed epoch date, mod 48. Guess evaluation implements the two-pass Wordle algorithm (greens first, then yellows against remaining letter counts) to handle duplicate letters correctly.

### [08:40 UTC] Build Phase — UI, hints, AI integration

- Wrote `index.html` + `src/style.css`: responsive dark-mode-first layout, on-screen + physical keyboard, guess grid sized to word length, colorblind-mode toggle (adds ✓/●/✗ shape markers to tiles).
- Hint system: deterministic clue auto-reveals after 2 wrong guesses. "AI bonus hint" button calls the Anthropic Messages API directly from the browser using a session-only key entered in a settings panel (never persisted, never sent unless the user opts in and clicks the button) — same direct-browser-call pattern used in this catalog's CircuitLab and Vizstract builds. Falls back to a deterministic hint string ("starts with ___, N letters, category: ___") with zero network calls when no key is present. All hint text (deterministic or AI) is rendered via `textContent`, never `innerHTML`.
- Result screen: win/loss modal with shareable emoji-grid text (🟩🟨⬛/⬜), stats dashboard (games played, win %, streaks, per-category accuracy) read/written to a single namespaced `localStorage` key.

### [08:55 UTC] Tests Written and Run

- Wrote `tests/lexicon.spec.js` covering word bank integrity, daily-word determinism (via `page.addInitScript` date mocking), duplicate-letter feedback edge case, max-guess formula, keyboard state aggregation, win/loss detection, hint-reveal timing, one-play-per-day gate, practice mode isolation from daily stats, share-text generation, invalid-input handling, AI-hint deterministic fallback with zero network requests, and an injected `<script>` payload in a mocked AI response verified inert.
- First run: 15 passed, 13 failed. Two real bugs found and fixed:
  1. `daysBetween()` passed 1-indexed `YYYY-MM-DD` month values straight into `Date.UTC`, which expects a 0-indexed month — silently shifting every computed date by up to a month and breaking the daily-word cycle's no-repeat guarantee. Caught by the `daysBetween` and `DAILY_CYCLE` pure-logic tests, not by manual play.
  2. Every "Live browser gameplay" test timed out because the page threw `Identifier 'WORD_BANK' has already been declared` on load. Root cause: `main.js`'s Node-only `require("./words.js")` shim declared `var { WORD_BANK, CATEGORY_LABELS }` at the top level, guarded by an `if (typeof module !== "undefined")` check — but `var` hoists to the top of its enclosing scope regardless of the guard, and classic `<script>` tags share one top-level lexical scope in the browser, so this collided with `words.js`'s `const WORD_BANK` and threw a SyntaxError before any game code ran, even though the guarded branch itself never executed in the browser. Fixed by wrapping the Node shim in its own function and assigning to `global.WORD_BANK`/`global.CATEGORY_LABELS` instead of declaring top-level bindings.
- Also fixed a genuine state-restoration bug caught during implementation (before the first test run): the daily round's exact guess sequence wasn't persisted, only a guess count, so reloading after finishing today's puzzle couldn't reconstruct the board or share text. Fixed by persisting the full `guesses` array per history entry.
- Second run after both fixes: 28 passed, 0 failed.

### [09:10 UTC] Verify — Step 7

- Manually exercised the game end-to-end in headless Chromium outside the test suite: played a full daily round to a win, reloaded to confirm the one-play-per-day gate, switched to practice mode, toggled colorblind mode, and confirmed the AI-hint fallback path makes zero requests with no key set. Zero console/page errors observed.
- Security checklist run against all created files: no `.env`, no hardcoded credentials/API keys, no `eval()`/`exec()`, no `innerHTML` from user- or API-controlled data, no `subprocess`/`os.system`, no file-path handling of user input, everything self-contained in the build folder.

PRD success criteria:
1. ✓ All tests pass — 28 passed, 0 failed (final run)
2. ✓ Full daily round playable end-to-end in a real browser — verified live in headless Chromium (test 18 + manual pass)
3. ✓ Same UTC date always produces the same word, no repeats within a 48-day cycle — verified by tests 2–4
4. ✓ Duplicate-letter Wordle edge case handled correctly — verified by tests 8–9 with hand-computed expected results
5. ✓ AI hint degrades to deterministic fallback with zero network calls with no key, and never executes untrusted content with a key — verified by tests 26–27

### [09:15 UTC] Documentation

- FutureFeatures.md: 7 concrete suggestions
- Manual.md: usage guide, mode explanations, test command, AI-hint setup instructions

Build complete. Success criteria reviewed. All tests passing.
