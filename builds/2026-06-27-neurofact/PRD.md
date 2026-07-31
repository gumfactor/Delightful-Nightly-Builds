# PRD — Neurofact

## Goal

A polished browser quiz game that challenges players to distinguish real neuroscience research findings from AI-generated plausible fakes — teaching scientific literacy through play.

## User Story

As a neuroscience professor and researcher, I want a browser game I can play to test and sharpen my ability to spot plausible-sounding but false neuroscience claims — and one I can use in class to teach students critical evaluation of research claims.

## Scope

### In scope
- 30 questions per game session: 15 real neuroscience findings + 15 AI-generated plausible fakes
- Each question: a 1–2 sentence scientific claim, displayed one at a time
- Player presses REAL or AI GENERATED
- Reveal: correct/incorrect feedback with full explanation (1–2 sentences)
- Score tracker, streak counter, accuracy %, and progress bar throughout
- Final results screen: score, grade (A–F), accuracy breakdown, and replay button
- Question difficulty labels (Foundational / Advanced / Expert) and topic category tags
- Dark-mode, mobile-responsive, self-contained HTML game (no server, no external CDN)
- `src/generator.py`: Python regeneration script that calls Anthropic API to refresh questions when `ANTHROPIC_API_KEY` is set
- Playwright browser tests (15+) and pytest unit tests for generator logic

### Out of scope
- Multiplayer or leaderboard
- User accounts or persistent history across sessions
- Backend server
- Fetching live content from arXiv at game time (content is embedded in HTML)

## Tech Stack

- Vanilla HTML5 / CSS3 / ES6 — self-contained `index.html` (all CSS and JS inline)
- Python 3 stdlib + `urllib.request` for generator (`src/generator.py`)
- `@playwright/test` for browser tests
- `pytest` for Python generator tests
- No CDN dependencies (game must run from `file://` without internet)

## Data Structure

Game questions are embedded as a JavaScript constant in `index.html`:

```js
const QUESTIONS = [
  {
    id: 1,
    statement: "...",        // 1–2 sentence scientific claim
    answer: "real",          // "real" | "fake"
    category: "Memory",      // topic category
    difficulty: "Advanced",  // "Foundational" | "Advanced" | "Expert"
    explanation: "..."       // shown after answering
  },
  ...
]
```

`src/generator.py` outputs `game_data.json` in the same schema, which can be pasted back into the HTML constant.

## Folder Structure

```
builds/2026-06-27-neurofact/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html                   ← Self-contained game (no server needed)
├── playwright.config.js
├── package.json
├── requirements.txt
├── src/
│   └── generator.py             ← Anthropic API question regenerator
└── tests/
    ├── neurofact.spec.js        ← Playwright browser tests (15+)
    └── test_generator.py        ← pytest tests for generator logic
```

## Testing Strategy

### Playwright (browser game)
Tests run against `index.html` via `file://` URL. Covers:
- Page loads correctly (title, first question visible)
- UI elements present (REAL button, AI GENERATED button, score, progress)
- Answering a question triggers feedback reveal
- Correct answer feedback uses green accent; wrong answer uses red
- Next question advances progress
- All 30 questions cycle through to final screen
- Final screen shows score, grade, and restart button
- Streak counter updates correctly
- Category and difficulty tags visible per question

### pytest (generator)
Tests cover:
- Seed question data integrity (count, required fields, valid answer values)
- Score and grade calculation functions
- Streak tracking logic
- Question shuffling produces different order
- API prompt structure
- Graceful fallback when API key absent

## Success Criteria

1. **Playable**: the game loads from `index.html` via `file://`, shows all 30 questions, and reaches the final screen without errors.
2. **Functional feedback**: each answer reveals whether it was correct, highlights the correct button (green), and shows the explanation — before the player can proceed.
3. **Score integrity**: final score equals number of correct answers out of 30; grade maps correctly to accuracy percentage.
4. **Content quality**: the 30 questions span at least 5 neuroscience topic categories and include both foundational and expert-level items.
5. **All tests pass**: 15+ Playwright tests and 15+ pytest tests pass with zero failures.
