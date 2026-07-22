# Build Log — Bayes Lab

> **Date:** 2026-07-22
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:15 UTC] Session Start

- Checked `builds/` on the local branch for an interrupted build: the most recent local folder (2026-06-18-regex-dojo) ends with "Build complete. Success criteria reviewed." — nothing to resume.
- Read PROFILE.md and STANDARDS.md. Local `builds/index.md` was badly out of date (last real merge only through 2026-06-24); resynced from the most recently created open PR branch (`claude/cool-sagan-ioczhc`, PR #48, 2026-07-21 "Bridgework") per CLAUDE.md Step 1/9 instructions. That branch's index.md shows 41 total builds through 2026-07-21.
- Noted a pre-existing data-hygiene gap: a 2026-06-25 build ("Stats Coach", PR #20) never made it into any subsequent branch's index.md — the resync-from-most-recent-PR approach only carries forward whichever single branch happened to be picked each night, so a branch can be silently dropped from the lineage. Confirmed its existence and content directly from its branch to inform tonight's topic-diversity check, but did not attempt to repair the historical index gap — out of scope for tonight.
- Day-of-year check: 2026-07-22 is day 203 (2026 is not a leap year). `(203-1) % 9 = 4` → Category E — Learning Aid.
- Lottery: 2 pending Category E backlog ideas (#17, #18), both blank rating → R=0 → lottery_chance = 25%. Rolled 82 → fresh-idea path.
- Generated 3 fresh Category E ideas, selected "Bayes Lab" (Bayesian Beta-Binomial inference trainer). Full reasoning in WhyThis.md.
- Before writing any JS, derived and cross-checked the core statistics (Beta posterior, equal-tailed credible interval via bisection on the regularized incomplete beta function, Savage-Dickey Bayes factor, Wilson score interval, exact two-sided binomial test) against an independent stdlib-only Python reference implementation, to guarantee the pedagogical numbers are actually correct.
- Build folder created: `builds/2026-07-22-bayes-lab/`

### [08:30 UTC] PRD Written

- Goal: interactive Beta-Binomial Bayesian trainer with psychology-research-grounded scenarios, live posterior updating, credible intervals, Savage-Dickey Bayes factors, and a side-by-side frequentist contrast panel.
- Scope: 5 scenarios, two prior-elicitation modes (Belief / Advanced), sequential + batch trial entry with Undo/Reset, live Canvas 2D chart, history table, optional session-only-key AI narrative with deterministic fallback.
- Notable constraints/decisions: no ES modules (opens via file://), no CDN dependency, equal-tailed CI (not HDI) and method-of-moments prior elicitation (not quantile-matching optimization) chosen deliberately for correctness and scope discipline — recorded in PRD Out of Scope, not a mid-build cut.

### [08:45 UTC] Build Phase — Math Core

- Implemented `src/beta-math.js`: log-gamma (Lanczos), regularized incomplete beta via continued fraction (Numerical Recipes `betacf` algorithm), Beta pdf, quantile via bisection, credible interval, posterior tail probability, Savage-Dickey Bayes factor (BF10/BF01) with a Jeffreys/Lee & Wagenmakers strength label, Wilson score interval, and exact two-sided binomial test p-value (point-probability-threshold method, matching R's `binom.test`).
- Verified module load with Node directly against the Python reference values computed earlier (see BUILD_LOG entry below under Tests).

### [09:10 UTC] Build Phase — AI Narrative + App Wiring

- Implemented `src/ai-narrative.js`: builds a prompt from only the already-displayed computed numbers (scenario label, prior, n, successes, posterior mean/CI, BF10, p-value — no personal data), calls `api.anthropic.com` directly from the browser with a session-only key (never persisted, never logged), and falls back to a deterministic template that reads the same numbers into prose when no key is present.
- Implemented `src/app.js`: scenario picker, Belief/Advanced prior-mode toggle kept in sync, trial entry (single + batch) with Undo/Reset, Canvas 2D prior/posterior overlay chart, history table, Bayesian + frequentist panels. All dynamic text inserted via `textContent`/`createElement`, never `innerHTML`.
- Implemented `index.html` and `src/styles.css`: dark-mode-first, mobile-responsive layout.

### [09:35 UTC] Tests Written

- `tests/bayes-lab.spec.js` (Playwright): math functions checked directly via `page.evaluate` against the independently-derived reference values; scenario/prior/trial-entry UI flows; Undo/Reset; invalid-input rejection; AI narrative template-fallback (zero network calls) and mocked-key path (network intercepted, never live); script-injection inertness; mobile viewport layout.

### [09:50 UTC] Tests Run

Tests: 24 passed, 0 failed.

### [10:00 UTC] Verify — Step 7 success criteria + security checklist

- All 5 PRD success criteria reviewed and met (see final entry below for detail).
- Security checklist: no `.env`, no hardcoded credentials/secrets, no `eval`/`exec`, no `innerHTML` from user/AI-controlled data, no `subprocess`/`os.system`, no file-path handling from user input, everything self-contained in the build folder, the only network call is opt-in and carries no personal data.

### [10:10 UTC] Documentation

- FutureFeatures.md: 7 concrete suggestions.
- Manual.md: quick start, feature walkthrough, configuration, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.
