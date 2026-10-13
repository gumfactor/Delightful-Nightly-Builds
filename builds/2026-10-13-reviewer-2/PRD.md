# PRD — Reviewer 2

> **Build date:** 2026-10-13
> **Category:** G — Game / Puzzle
> **Complexity:** Ambitious Project

## Goal
A browser game where each round shows a short study summary with one planted methodological flaw and the player must name the flaw, with an optional Claude-powered mode that writes unlimited fresh cases.

## User Story
As a neuroscience professor who teaches AI Applications for Psychologists and supervises students, I want a fast, replayable critical-appraisal game, so that I (and my students) sharpen flaw-spotting skills and I can use it as a teaching aid.

## Scope
### In Scope
- 32 hand-written cases across 12 flaw types (circular analysis, reverse inference, multiple comparisons, optional stopping, underpowered, confound, selection bias, regression to the mean, base-rate neglect, ecological fallacy, correlation as causation, small-sample/outlier driven)
- Modes: Daily Review (8 cases, seeded by UTC date, same for everyone), Practice (weighted toward previously missed flaws), Fresh Case (Claude generates a new case via the Anthropic API from the browser)
- Scoring: 10 points, streak bonus, hint costs 4 points; rank titles
- Explanation after each answer; end-of-round per-flaw breakdown
- Persistent stats (localStorage): per-flaw accuracy, best streak, daily completion
- Mobile-readable, dark/light via prefers-color-scheme
- Fresh Case: user pastes key at runtime, kept in sessionStorage only; response validated before use
### Out of Scope
- Server, accounts, leaderboards; PubMed abstract ingestion (future)

## Tech Stack
- Vanilla HTML/CSS/JS, no dependencies at runtime; Playwright for tests
- Opens directly via file://

## Data Structure
Case: `{id, flaw, title, text, hint, explain}`. Flaw taxonomy: `{id, name, blurb}`.
Stats: `{flaws:{id:{seen,right}}, bestStreak, daily:{date:score}, total}`.
Generated case must contain a valid `flaw` id from the taxonomy, else rejected.

## Folder Structure
```
builds/2026-10-13-reviewer-2/
├── PRD.md WhyThis.md BUILD_LOG.md FutureFeatures.md Manual.md
├── index.html  style.css  cases.js  game.js
├── package.json  package-lock.json  playwright.config.js
└── tests/reviewer2.spec.js
```

## Testing Strategy
Playwright against file://. Core logic (seeded RNG, daily selection, scoring, weighted pick, case validation, AI response parsing) tested via page.evaluate; UI flow tested by clicking. Anthropic API mocked with page.route. No live calls.

## Success Criteria
1. Daily round plays 8 cases end to end with score and breakdown screen
2. Every case has a valid flaw id, non-empty explanation, and the correct answer is among the 4 choices
3. Daily selection is deterministic per date
4. Fresh Case mode works with mocked API and rejects malformed output
5. ≥15 Playwright tests pass
