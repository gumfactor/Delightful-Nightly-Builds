# PRD — Neuro Arcade

> **Build date:** 2026-10-04
> **Category:** G — Game / Puzzle
> **Complexity:** Ambitious Project
> **Day of week:** Sunday (day 277, index 6)

---

## Goal

A browser game arcade that runs four validated cognitive-psychology paradigms (Stroop, 2-back, Go/No-Go, Ultimatum Game) with millisecond timing, scores them with real psychometrics (interference, d′, commission rate), compares results to published reference ranges, and exports/imports trial-level CSV so a whole class can pool data.

## User Story

As an associate professor who teaches Stress and Coping, Social Affective Neuroscience, and AI Applications for Psychologists, I want to open a file on my phone or laptop and run real experimental paradigms on myself or a class, so that I can demonstrate cognitive control, working memory, and social decision-making with live data instead of slides.

## Scope

### In Scope
- Four playable tasks: Stroop colour-word, 2-back letters, Go/No-Go, Ultimatum Game (accept/reject offers from a simulated proposer)
- Keyboard and on-screen button input (mobile friendly); response times measured with `performance.now()` from the first painted frame of the stimulus
- Seeded trial generation (reproducible; seed stored with each session)
- Scoring: mean RT by condition, Stroop interference, d′ with log-linear correction, commission error rate, Ultimatum reject-by-offer curve and minimum accepted offer
- Reference-range comparison (approximate teaching values) with percentile bar per metric
- Results tab: latest session per task with history sparklines
- Data tab: participant label, trial-level CSV export, CSV import (merge and de-duplicate), class view table grouped by label, clear data
- localStorage persistence (games category), dark/light via `prefers-color-scheme`
- URL test flags: `?fast=1&trials=N&test=1`

### Out of Scope
- Server, accounts, cloud sync
- Clinical interpretation or diagnostic claims (reference ranges are labelled as approximate)
- Anthropic API integration (no personal or research data leaves the browser)

## Tech Stack

- **Language:** HTML/CSS/JS (classic scripts, no modules, so `index.html` works from `file://`)
- **Framework:** None
- **Dependencies:** `@playwright/test` (dev only)
- **Runtime requirement:** Open `index.html` in a browser, no install

## Data Structure

Session: `{ id, task, ts, label, seed, trials: [Trial], metrics }`
Trial: `{ n, condition, stimulus, response, correct (bool|null), rt (ms|null) }`
CSV (long format, one row per trial): `session_id,task,timestamp,label,seed,trial,condition,stimulus,response,correct,rt_ms`. Metrics are recomputed from trials on import, so the CSV is the single source of truth.

## Folder Structure

```
builds/2026-10-04-neuro-arcade/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── package.json
├── package-lock.json
├── playwright.config.js
├── index.html
├── src/
│   ├── stats.js     (pure math: mean, sd, probit, d′, normal CDF)
│   ├── tasks.js     (RNG, trial generators, scorers, reference ranges)
│   ├── store.js     (localStorage, CSV export/import, merge)
│   ├── app.js       (UI, task runner, timing)
│   └── styles.css
└── tests/
    ├── logic.spec.js   (stats, generators, scorers, CSV)
    └── ui.spec.js      (play each task, results, export/import)
```

## Testing Strategy

- **Framework:** Playwright (logic tested in-page via `page.evaluate` against the UMD globals; UI tested by playing the tasks)
- **Test file location:** `tests/*.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - probit/normal CDF accuracy, d′ with perfect and zero hit/FA rates (finite), Stroop interference arithmetic
  - Trial generators: Stroop congruency balance, n-back target rate and target correctness, Go/No-Go ratio, Ultimatum offer coverage, seed determinism
  - Scorers on hand-built trial arrays, including empty and all-timeout input
  - CSV round trip including quotes/commas in the label; malformed CSV rejected gracefully; import de-duplication
  - UI: each task playable end-to-end in fast mode and writes a session; results render; export content; import merges; clear data; label is never injected as HTML

## Success Criteria

1. All tests pass (zero failures)
2. All four tasks are playable end-to-end and each saves a scored session
3. Exported CSV re-imported into an empty store reproduces identical metrics
4. Each metric is shown against a reference range with a percentile
5. Works at phone width (390px) with no horizontal scroll

---

## Scope Changes

(none)
