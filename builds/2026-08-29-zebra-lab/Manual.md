# Manual — Zebra Lab

> **Version:** 1.0 (built 2026-08-29)
> **Complexity:** Ambitious Project

---

## What This Is

Zebra Lab is a browser logic-grid deduction game — the same family of puzzle as the classic "Zebra Puzzle" ("who owns the zebra?") — but every puzzle is about fictional research studies described using real research-methods vocabulary (population, study design, confound-control method, threat to validity). Every single puzzle is procedurally generated and then verified by a from-scratch constraint-solver to have exactly one valid solution before it's ever shown to you, so if you get stuck, the answer is always fully determinable from the clues given — never a guess.

## Quick Start

1. Open `index.html` directly in any modern browser (double-click it, or drag it into a browser window). No install, no server, no build step.
2. From the home screen, click **Practice** next to "Chapter 1: Intro" (the only chapter unlocked at first).
3. Read the clue list, then use the dropdown selects in the Answer Grid to assign each attribute to the study number you believe it belongs to.
4. Click **Check Solution** — it tells you how many studies are entirely correct, but never which ones.
5. Once fully correct, you'll see the result screen with a short "Why This Matters" explanation of one methodology concept from the puzzle you just solved.

## How to Use It

### Practice Mode

Pick any unlocked chapter and get a freshly generated puzzle every time — unlimited plays. Chapter 2 unlocks after solving Chapter 1 three times; Chapter 3 unlocks after solving Chapter 2 three times.

- **Chapter 1 (Intro):** 4 studies, 3 attribute categories (Population, Study Design, Sample Size), only direct ("uses both") and negative ("does not use") clues.
- **Chapter 2 (Standard):** 5 studies, 4 attribute categories (Population, Study Design, Confound Control, Threat to Validity), adds "numbered next to" clues.
- **Chapter 3 (Expert):** same categories as Chapter 2, adds "has a lower study number than" clues, and the clue set is pruned more aggressively (fewer, harder-to-use clues).

### Daily Challenge

One Chapter-2-difficulty puzzle per UTC calendar day — everyone who plays on the same day gets the identical puzzle. You get one completion per day; the button on the home screen shows "Completed Today" once you've solved it. After solving, you can copy a small share string (date, a colored-square result, and your check/hint counts) — it never contains any puzzle content, so sharing it doesn't spoil the puzzle for anyone else.

### Hints

Each puzzle allows up to 2 hints. A hint reveals one entire study's correct row (all of its attribute values at once). Hints and checks both count toward your final score for that puzzle but never lock you out of solving it.

### Stats

The home screen shows total puzzles solved, current daily-challenge streak, and best streak ever, all stored locally in your browser (`localStorage`) — nothing is sent anywhere.

### Optional AI Explainer

After solving any puzzle that includes the Confound Control / Threat to Validity categories (Chapters 2 and 3), you'll see a short, accurate explanation of how one confound-control method relates to one threat to validity from your puzzle. This works fully offline by default (a small deterministic template, not AI). If you want Claude to polish the phrasing, paste your own Anthropic API key into the "Optional AI Explainer" field on the home screen — it's kept only in that browser tab's session storage (cleared when you close the tab) and is used only for a single direct call to `api.anthropic.com`. The underlying facts sent and returned are never anything beyond your own puzzle's category names — no personal data of any kind.

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| Anthropic API Key | (empty) | Optional. Paste your own key on the home screen to enable AI-polished explanations. Leave blank for the offline deterministic explanation. Stored only in `sessionStorage`, never `localStorage`. |

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "Check Solution" says 0 correct even though I'm sure about one study | A dropdown may still be on the blank "—" option for one of that study's categories | Make sure every select in that study's row has a real value chosen, not the blank placeholder |
| AI explanation always shows the offline version even after entering a key | The key wasn't saved because the input's `change` event didn't fire (e.g. you pasted and immediately clicked away without the field losing focus) | Click or tab out of the API key field after pasting to confirm the value is saved, then solve a new puzzle |
| Daily Challenge button is disabled and I haven't played today | Your system clock or browser might be reporting a different date than you expect, since the gate uses UTC | Check your device's date/timezone; the Daily Challenge always resets at 00:00 UTC |
| Progress/stats reset unexpectedly | Browser data (localStorage) was cleared, or you're in a private/incognito window | Progress is per-browser-profile; use the same browser profile each time to keep your stats |

## Known Limitations

- No pencil-marks / elimination-tracking grid — you'll want a notepad (physical or otherwise) for harder Chapter 3 puzzles if you don't want to hold every deduction in your head.
- Hints reveal a whole study row at once; there's no lighter "reveal just one cell" option yet.
- The AI explainer always covers Study #1's Confound-Control/Threat pairing — it doesn't yet let you pick which study to explain.
- Practice mode doesn't show a numeric difficulty rating beyond the chapter name.
