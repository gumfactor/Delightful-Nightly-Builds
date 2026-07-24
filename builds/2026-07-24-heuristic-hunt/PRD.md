# PRD — Heuristic Hunt

> **Build date:** 2026-07-24
> **Category:** G — Game / Puzzle
> **Complexity:** Ambitious
> **Day of week:** Friday

---

## Goal

A browser game that trains recognition of 12 common cognitive biases and decision-making heuristics through short real-world vignettes, multiple-choice identification, and immediate explanatory feedback.

## User Story

As a psychology/neuroscience researcher and quantitative-investing hobbyist who wants to sharpen judgment about decision-making errors in both research and investing contexts, I want to practice spotting specific cognitive biases in realistic scenarios, so that I build faster, more reliable pattern recognition for these errors when they show up in my own work and financial decisions.

## Scope

### In Scope
- A taxonomy of 12 named cognitive biases/heuristics, each with a short definition (anchoring, confirmation bias, sunk cost fallacy, availability heuristic, loss aversion, overconfidence bias, hindsight bias, framing effect, base rate neglect, bandwagon effect, recency bias, survivorship bias)
- 30 hand-authored vignettes (2-3 sentences each) spanning research/lab, investing, and everyday-life domains, each tagged with its correct bias, 3 plausible distractor biases, and a teaching explanation
- 3 campaign chapters of increasing subtlety (10 vignettes each), gated by a 70% accuracy requirement to unlock the next chapter
- Multiple-choice question screen: vignette text, 4 shuffled answer buttons, immediate right/wrong feedback with explanation before advancing
- A date-seeded Daily Challenge: 5 vignettes deterministically selected from the full pool by UTC date, playable once per UTC day, ending in a shareable emoji-grid result copyable to clipboard
- A Practice mode: drill any single bias type on demand, independent of campaign unlock state
- A per-bias Mastery Dashboard: attempts/correct/accuracy per bias type, persisted in localStorage, color-coded by mastery level (green ≥80%, yellow 50-79%, red <50%, gray = not attempted)
- Reset Progress control (with confirmation) that clears all localStorage state
- Mobile-responsive layout; dark-mode-first styling with adequate contrast

### Out of Scope
- Server-side/multiplayer leaderboards (no backend — localStorage only, appropriate per PROFILE.md's data-source guidance for games)
- AI-generated vignettes at runtime (all 30 are hand-authored and fixed; this keeps the "correct answer" defensible and testable, unlike open-ended AI grading)
- Audio/animation beyond simple CSS transitions
- Account system or cross-device sync

## Tech Stack

- **Language:** HTML/CSS/JS (vanilla, classic `<script>` tags — no ES modules, no bundler)
- **Framework:** None
- **Dependencies:** None (no CDN libraries needed; native Canvas/SVG not required, native DOM + CSS suffice for the mastery bars)
- **Runtime requirement:** Opens directly via `file://` in any modern browser, no build step, no install

## Data Structure

All data lives in `src/data.js` as plain JS objects/arrays assigned to a single global namespace object `window.HH` to avoid polluting the global scope while still working with classic (non-module) scripts.

```js
HH.BIASES = [
  { id: 'anchoring', name: 'Anchoring Bias', definition: '...' },
  // ... 12 total
];

HH.VIGNETTES = [
  {
    id: 1,
    chapter: 1,               // 1, 2, or 3
    biasId: 'anchoring',      // correct answer, must match a HH.BIASES id
    text: '...',              // the scenario
    distractors: ['framing', 'overconfidence', 'loss_aversion'], // 3 other bias ids
    explanation: '...'        // shown after answering, explains why correct + why distractors are close-but-wrong
  },
  // ... 30 total, 10 per chapter
];
```

Persisted state (localStorage, JSON-serialized under key `heuristicHunt_v1`):

```js
{
  chapterProgress: { 1: { attempted: 10, correct: 8, unlocked: true }, 2: {...}, 3: {...} },
  biasMastery: { anchoring: { attempts: 5, correct: 4 }, ... },  // one entry per bias id
  dailyChallenge: { lastPlayedDate: 'YYYY-MM-DD', lastResult: { score: 4, total: 5, grid: '🟩🟩🟥🟩🟩' }, history: [...] },
  bestStreak: 0,
  currentStreak: 0
}
```

## Folder Structure

```
builds/2026-07-24-heuristic-hunt/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html
├── playwright.config.js
├── src/
│   ├── styles.css
│   ├── data.js
│   ├── storage.js
│   ├── daily.js
│   └── app.js
└── tests/
    └── heuristic-hunt.spec.js
```

## Testing Strategy

- **Framework:** Playwright
- **Test file location:** `tests/heuristic-hunt.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - Main menu renders with all navigation options (Campaign, Daily Challenge, Practice, Mastery Dashboard)
  - Data integrity: every vignette's `biasId` and all `distractors` reference a valid `HH.BIASES` id, no vignette lists its own correct answer as a distractor, every vignette has exactly 3 distractors, chapters contain exactly 10 vignettes each
  - Chapter 1 is unlocked by default; Chapters 2 and 3 are locked until the prior chapter's accuracy gate is met
  - Answering a question correctly shows correct feedback and increments the running score
  - Answering a question incorrectly shows incorrect feedback with the correct answer revealed
  - Completing a chapter below 70% accuracy does not unlock the next chapter
  - Completing a chapter at or above 70% accuracy unlocks the next chapter and persists that state across a page reload
  - Daily Challenge selects exactly 5 questions and is deterministic for a given date (mocked via `page.addInitScript` to override `Date`)
  - Daily Challenge cannot be replayed twice on the same UTC date (button disabled / message shown)
  - Daily Challenge result screen renders a shareable emoji grid matching the actual right/wrong sequence
  - Practice mode allows drilling a single bias type outside of chapter-unlock constraints
  - Mastery Dashboard reflects accumulated attempts/correct counts and color-codes mastery level correctly
  - Reset Progress clears all localStorage state and returns the UI to its first-run state
  - No console errors/page errors occur during a full campaign playthrough
  - Layout does not break at a narrow (375px) mobile viewport width

## Success Criteria

1. All tests pass (zero failures)
2. All 3 campaign chapters are playable end-to-end with correct accuracy-gated unlocking
3. The Daily Challenge is deterministic per UTC date, playable exactly once per day, and produces a correct shareable result grid
4. The Mastery Dashboard accurately reflects per-bias performance and persists across reloads
5. Every one of the 30 vignettes has a unique, unambiguous correct answer verified by an automated data-integrity test (no vignette's distractor set contains its own correct bias id)

---

## Scope Changes

None — full scope as planned was completed.
