# Manual — Regex Dojo

## What It Is

Regex Dojo is a 20-level browser puzzle game that teaches regular expressions from scratch. Each level presents a set of strings you must MATCH and strings you must REJECT, and your job is to write a regex pattern that satisfies both constraints simultaneously. Instant feedback shows whether each string passes or fails as you type.

---

## Opening the Game

Open `index.html` in any modern browser (Chrome, Firefox, Safari, Edge). No server or build step required. Progress is saved automatically in `localStorage`.

```
open builds/2026-06-18-regex-dojo/index.html
```

---

## How to Play

1. **Level Select** — The game opens on the level select screen showing all 20 levels. Only Level 1 is unlocked initially; each level unlocks the next when complete.

2. **Click a level** — The game view opens with:
   - A concept badge (the regex feature being taught)
   - A description of the puzzle
   - **MUST MATCH** strings (green label) — your regex must match these
   - **MUST NOT MATCH** strings (red label) — your regex must not match these

3. **Type your regex** — Enter a pattern in the `/` `/` input field. Feedback updates instantly:
   - `·` — neutral (no pattern typed yet)
   - `✓` — this string satisfies its constraint
   - `✗` — this string fails its constraint

4. **Submit** — The Submit button activates only when all constraints are satisfied. Click it to mark the level complete and unlock the next.

5. **Hint** — Click "Hint" to reveal a conceptual clue (it won't give away the answer, just explain the relevant regex syntax).

6. **Level Select** — Click "← Levels" at any point to return to the menu. Progress is never lost.

---

## Level Overview

| # | Title | Concept |
|---|-------|---------|
| 1 | Find the Greeting | Literal Match |
| 2 | Vowel Starter | Character Class `[ ]` |
| 3 | Three-Letter Code | Dot Wildcard `.` |
| 4 | British or American | Optional `?` |
| 5 | Numbers Only | One or More `+` |
| 6 | Optional Repeats | Zero or More `*` |
| 7 | Error Lines | Start Anchor `^` |
| 8 | Log Files | End Anchor `$` |
| 9 | PIN Validator | Exact Count `{n}` |
| 10 | Image Files | Alternation `\|` |
| 11 | Phone Numbers | Escaping & Combining |
| 12 | Whole Words Only | Word Boundary `\b` |
| 13 | No Whitespace | Non-Whitespace `\S` |
| 14 | IP Addresses | Range Quantifier `{n,m}` |
| 15 | Password Validator | Lookahead `(?=...)` |
| 16 | Hex Colors | Character Ranges `[0-9a-fA-F]` |
| 17 | Valid Identifiers | Word Character `\w` |
| 18 | Email Addresses | Composing Patterns |
| 19 | Comment Lines | Real-World Pattern |
| 20 | Log Entry Validator | Final Challenge |

---

## Running Tests

```bash
cd builds/2026-06-18-regex-dojo
npm install          # installs @playwright/test (only needed once)
npx playwright test  # runs all 33 tests
```

All 33 tests must pass with zero failures.

---

## Notes

- Progress persists in `localStorage` under the key `regex-dojo-v1`. Clear site data to reset.
- The game is entirely self-contained — no internet connection required after initial load.
- Regex patterns are tested using JavaScript's built-in `RegExp` engine. Flags (`i`, `g`, etc.) are not currently supported.
