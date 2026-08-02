# PRD — Lexicon

> **Build date:** 2026-08-02
> **Category:** G — Game / Puzzle
> **Complexity:** Ambitious Project
> **Day of week:** Sunday

---

## Goal

A daily letter-guessing word puzzle (Wordle-style mechanic) where every word is real technical vocabulary drawn from the user's own domains — neuroscience/psychology, statistics/research methods, AI/ML, and investing — with deterministic per-day word selection, a definition-clue hint system, an optional AI-generated bonus hint via the Anthropic API, and persistent streak/mastery stats.

## User Story

As a researcher and builder who moves daily between neuroscience, statistics, AI, and markets, I want a two-minute daily vocabulary puzzle built from the exact terminology I use across those domains, so that I get a quick, genuinely fun mental warm-up that also reinforces precise recall of the language I work in — instead of a generic word game with no connection to my actual work.

## Scope

### In Scope
- Variable-length letter-guessing puzzle (5–10 letters) with green/yellow/gray feedback (correct position / present-wrong-position / absent), including correct handling of duplicate letters
- Curated word bank of 48 real terms across 4 domains (Neuroscience/Psychology, Statistics/Methods, AI/ML, Investing), each with an accurate, hand-written clue
- Deterministic daily word: a seeded shuffle of the 48-word bank fixes a cycle order once; the UTC calendar date picks today's index, guaranteeing no repeats until the full 48-day cycle completes and the same word for everyone on the same day
- One daily play per UTC calendar day, enforced via localStorage, with the result (win/loss, guess count, word) persisted
- Practice mode: pick any domain and play an unlimited random word from it, without touching daily streak/stats
- On-screen + physical keyboard input, with per-key best-state coloring aggregated across all guesses
- Guesses accepted as any A–Z string of the correct length (no external dictionary validation — documented scope decision below)
- Hint system: the word's definition clue auto-reveals after 2 incorrect guesses (always available, no key required); an optional "AI bonus hint" button calls the Anthropic API directly from the browser with a session-only, user-supplied key for a second, more creative clue — never persisted, never sent unless the user opts in, always has a deterministic fallback hint ("starts with ___, N letters, category: ___") when no key is present
- Win/loss result screen with a shareable emoji-grid summary (🟩🟨⬛), matching the result grid convention already established in this catalog
- Persistent stats dashboard (localStorage): games played, win %, current streak, max streak, per-category accuracy
- Mobile-responsive layout, dark-mode-first design with sufficient color contrast (including a colorblind-safe mode toggle using shape markers in addition to color)

### Out of Scope
- Server-side/multiplayer leaderboards — this is a single-player, local-only game
- A full English dictionary for guess validation — the word bank is small and domain-specific; validating "real word" guesses would require bundling or calling an external dictionary API, which adds a dependency for no real gameplay benefit here
- User-editable/custom word lists — a fixed, curated, high-quality bank is preferred over a feature that could introduce inaccurate or offensive content unsupervised
- Persisting the Anthropic API key across sessions — session-only by design, per STANDARDS.md's no-credential-persistence posture

## Tech Stack

- **Language:** HTML/CSS/JS (vanilla, classic `<script>` tags, no ES modules — opens directly via `file://`)
- **Framework:** None
- **Dependencies:** `@playwright/test` (dev/test only); Anthropic Messages API called directly from the browser at runtime, optional
- **Runtime requirement:** Open `index.html` directly in any modern browser — no build step, no server, no install

## Data Structure

`src/words.js` defines a flat array of word entries, loaded as a global before `src/main.js`:

```js
const WORD_BANK = [
  { word: "AMYGDALA", category: "neuro", clue: "Brain structure central to fear and threat detection." },
  // ... 47 more, 12 per category: neuro, stats, ai, finance
];
```

Each entry: `word` (A–Z uppercase only, 5–10 letters, unique across the whole bank), `category` (one of `neuro` | `stats` | `ai` | `finance`), `clue` (one accurate sentence, no external source needed — general-knowledge domain definitions).

`localStorage` keys (all under a single namespaced JSON blob `lexicon_state_v1`):
```json
{
  "lastPlayedDate": "2026-08-02",
  "history": [{ "date": "2026-08-02", "word": "AMYGDALA", "won": true, "guessCount": 4 }],
  "currentStreak": 3,
  "maxStreak": 5,
  "categoryStats": { "neuro": { "played": 4, "won": 3 }, "stats": {...}, "ai": {...}, "finance": {...} },
  "colorblindMode": false
}
```

Stateless otherwise — no server, no external persistence.

## Folder Structure

```
builds/2026-08-02-lexicon/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── package.json
├── package-lock.json
├── playwright.config.js
├── .gitignore
├── index.html
├── src/
│   ├── style.css
│   ├── words.js
│   └── main.js
└── tests/
    └── lexicon.spec.js
```

## Testing Strategy

- **Framework:** Playwright
- **Test file location:** `tests/lexicon.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - Word bank integrity: exactly 48 entries, all uppercase A–Z only, length 5–10, unique words, every entry has a non-empty clue and a valid category
  - Daily word determinism: reloading the page on the same mocked date yields the same word; two different mocked dates within the 48-day cycle yield different words
  - Guess feedback core logic: exact match → all green; wrong positions → yellow; absent letters → gray; duplicate-letter edge case (e.g. guessing a letter that appears once in the answer but twice in the guess only marks one yellow/green and the other gray)
  - Max-guess computation formula for a range of word lengths
  - On-screen keyboard state aggregation: a key that has been green in any guess stays green even if a later guess shows it gray elsewhere
  - Win detection: submitting the exact word ends the round as a win and shows the result modal
  - Loss detection: exhausting max guesses without the correct word ends the round as a loss and reveals the answer
  - Hint reveal timing: the definition clue is hidden before 2 wrong guesses and visible after
  - One-play-per-day gate: after completing today's daily round, reloading shows the result screen instead of a fresh board; a different mocked date allows a new round
  - Practice mode: playing a practice round does not change `gamesPlayed`/streak in the persisted daily stats
  - Share text generation: the emoji grid matches the actual sequence of guess results
  - Non-letter keyboard input is ignored; incomplete guesses cannot be submitted
  - AI hint fallback: with no API key present, clicking "AI bonus hint" shows the deterministic fallback hint and makes zero network requests
  - XSS/security: a `<script>` payload placed in a mocked AI hint response renders as inert text, not executed
  - Colorblind mode toggle adds shape markers to tiles in addition to color

## Success Criteria

1. All tests pass (zero failures)
2. A full daily round is playable end-to-end in a real browser: load page → daily word determined → guesses submitted with correct color feedback → win or loss reached → result/share screen shown
3. The same UTC date always produces the same word, and no word repeats within a 48-day cycle
4. Guess feedback is correct on the classic Wordle duplicate-letter edge case, verified by a dedicated test
5. The AI hint path degrades gracefully to a deterministic fallback with zero network calls when no API key is supplied, and never executes untrusted content when a key is supplied

---

## Scope Changes

None — full in-scope feature set was delivered as planned.
