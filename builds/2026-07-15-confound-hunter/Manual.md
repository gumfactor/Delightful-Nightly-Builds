# Manual — Confound Hunter

## What it is
A single-page browser game that trains research-methods literacy. You read a short, fictional
research-study vignette and pick which single methodological flaw undermines it, from four options.

## How to run it
No build step, no server, no dependencies to install for play. Just open the file:

```
builds/2026-07-15-confound-hunter/index.html
```

directly in any modern browser (double-click it, or `open index.html` / `xdg-open index.html` from
this folder). Everything — game logic, data, and progress — runs and persists locally in your browser.

## How to run the tests

```bash
cd builds/2026-07-15-confound-hunter
npm install
npx playwright test
```

## How to play

### Practice
Three chapters of 10 questions each, in increasing order of subtlety:
- **Chapter 1 — Classic Flaws**: flaws stated fairly plainly.
- **Chapter 2 — Level Up**: same 10 flaw types, subtler wording.
- **Chapter 3 — Detective Finals**: near-miss distractors — the wrong options sound very plausible.

Score 70% or higher (7/10) on a chapter to unlock the next one. Each question gives instant feedback:
the option you picked is highlighted green (correct) or red (incorrect), the actual correct flaw is
always highlighted green, and a short explanation follows.

### Daily Challenge
A 5-question round drawn from the same 30-vignette pool. The 5 vignettes are chosen deterministically
from today's date — everyone who plays on the same UTC calendar day gets the same 5 questions, and you
get one attempt per day. After finishing, you can copy a shareable result string, e.g.:

```
Confound Hunter Daily 2026-07-15: 4/5
✅✅❌✅✅
```

### Mastery Dashboard
Tracks your accuracy on each of the 10 flaw types across every question you've ever answered (practice
and daily combined), so you can see exactly which flaw types trip you up most.

### Reset Progress
Clears chapter unlocks, mastery stats, and today's daily-challenge result back to a fresh install.
This cannot be undone.

## The 10 flaw types
Confound · Selection Bias · No Control Group · Demand Characteristics · Ceiling/Floor Effect ·
Regression to the Mean · Correlation ≠ Causation · Underpowered Sample · Lack of Blinding ·
Overgeneralization

## Data & privacy
All data (progress, mastery stats, daily results) lives in your browser's `localStorage` under keys
prefixed `confoundHunter_`. Nothing is sent anywhere — there is no network activity in this build at all.
