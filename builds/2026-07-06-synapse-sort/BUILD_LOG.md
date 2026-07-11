# Build Log — Synapse Sort

> **Date:** 2026-07-06
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:05 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Checked Step 0: local `builds/` folder on branch `claude/cool-sagan-qc8qor` has no incomplete build — the newest local dated folder (2026-06-18-regex-dojo) is already `complete` and merged. No resume needed.
- Fetched the most recent open PR branch (`claude/cool-sagan-fo421t`, PR #30, 2026-07-05 TrialScope) to read the current `builds/index.md` and `builds/ideas.md`, since main lags behind (22 open PRs currently unmerged, most recent build 2026-07-05).
- Day of year 187 → category index `(187-1) % 9 = 6` → **G — Game / Puzzle**.
- Backlog had 2 pending G-category ideas (both blank rating, R=0). Lottery chance = 25%. Rolled 88/100 → fresh-idea path.
- Generated 3 fresh candidates; selected **Synapse Sort** — a Connections-style daily category-sorting puzzle with a hand-authored, personally-themed 30-puzzle bank. Full reasoning in WhyThis.md.
- Build folder created: `builds/2026-07-06-synapse-sort/`.
- Noted: `ANTHROPIC_API_KEY` is NOT set in this session's environment (checked directly). Dropped any plan to call the API at build time; puzzle content is hand-authored instead, and the PRD documents this as the actual plan, not a mid-build deviation.

### [08:10 UTC] PRD Written

- Goal: personalized daily Connections-style puzzle game.
- Scope: 4x4 grid, 30-puzzle curated bank across 5 domains, daily deterministic selection, archive/practice mode, one-away hint, mistakes limit, win/lose, share grid, localStorage stats, colorblind-safe difficulty labels, dark/light mode.
- Notable decision: no bundler, classic scripts, so the whole thing opens via `file://` with zero setup.

### [08:12 UTC] Build Phase — Puzzle Content

- Hand-authored 30 puzzles in `src/puzzles.js` across 5 personal-interest domains (neuroscience/psychology, AI & agentic workflows, investing/markets, Canadian business, running/golf/boating), mixing single-domain "deep dive" puzzles with cross-domain puzzles that intentionally reuse a few overlapping words as red herrings.
- Validated the full bank immediately with an inline Node check (before writing any UI code): 30 puzzles, each with exactly 4 categories, 4 unique items per category, 16 unique items total, and one of each difficulty tier (yellow/green/blue/purple). All 30 passed on the first validation run.
- Verified the date→puzzle-index logic (`getPuzzleIndexForDate`) manually: anchor date 2026-07-06 → index 0, next day → index 1, 30 days later → wraps back to index 0, and a date a year earlier still resolves to a valid non-negative index.

### [08:40 UTC] Build Phase — Game Code

- Built `src/storage.js` (localStorage stats: games played, wins, streak, best streak, per-date history, idempotent per-date recording so a reload can't double-count) and `src/game.js` (tile grid rendering, selection, one-away detection, mistake tracking, win/lose flow, share-grid text generation, archive/practice mode, stats panel, dark/light theme toggle).
- Wrote `index.html` and `src/styles.css` — vanilla, classic `<script src>` tags (no bundler, no ES modules) so the whole game opens via `file://` with zero setup, per the PRD's tech-stack decision.
- Obstacle: initial manual QA in a headless browser showed dark mode leaving the page background white instead of switching. Root-caused it to the `transition: background 0.2s ease` rule on `body` racing with `getComputedStyle` reads immediately after the theme attribute changed (confirmed via a minimal isolated repro). Fixed by dropping that transition — cosmetic only, no functional loss — and re-verified with screenshots in both themes plus a re-run of the full test suite (still 31/31 passing).
- Verified visually via Playwright screenshots at both mobile (420px) and desktop (1000px) viewports, light and dark themes, and a full win-flow screenshot showing the solved-category rows and the emoji share grid rendering correctly.

### [09:05 UTC] Tests Run

Tests: 31 passed, 0 failed. (`npx playwright test`, `tests/*.spec.js` — puzzle-data.spec.js, daily-selection.spec.js, gameplay.spec.js, win-lose.spec.js, stats-archive.spec.js)

### [09:10 UTC] Documentation

- Wrote `Manual.md` (quick start, daily/archive/stats usage, dark mode, troubleshooting, known limitations) and `FutureFeatures.md` (9 concrete suggestions across quick-win/medium/ambitious tiers, plus integration points and a known-limitations table).

### [09:15 UTC] Verification

- Reviewed all 5 PRD success criteria and the full STANDARDS.md hard-standards checklist (safety, completeness, tests, documentation) and the security checklist — all satisfied. Details in the final PRD/BUILD_LOG review pass below.

Build complete. Success criteria reviewed. All tests passing.
