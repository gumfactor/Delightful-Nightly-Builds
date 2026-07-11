# Manual — Synapse Sort

> **Version:** 1.0 (built 2026-07-06)
> **Complexity:** Ambitious Project

---

## What This Is

Synapse Sort is a daily "find the connection" puzzle game, in the style of NYT Connections, with a puzzle bank written entirely around your own interests: neuroscience and psychology, AI and agentic workflows, investing and markets, Canadian business, and running/golf/boating. Sixteen tiles, four hidden groups of four — the trick is that categories deliberately share words to mislead you (a term that fits two different groups). It's a two-minute daily mental warm-up, not a public trivia clone.

---

## Quick Start

1. Open `index.html` directly in any browser (double-click it, or drag it into a browser window) — no install, no server, no internet connection needed.
2. You'll see today's puzzle: a 4x4 grid of 16 tiles.
3. Tap or click four tiles you think share a hidden category, then hit **Submit**.
4. Keep going until you've found all four groups, or you run out of your 4 allowed mistakes.
5. When you finish, hit **Copy Result** to copy a shareable emoji grid of how you did.

---

## How to Use It

### Playing the Daily Puzzle

Every UTC calendar day has one puzzle, cycling through a 30-puzzle bank (so it repeats after 30 days). You get one attempt per day — once you finish (win or lose), reopening the page shows your result instead of letting you replay, exactly like the genre's real daily games.

- Click tiles to select them (up to 4 at a time); click a selected tile again to deselect it.
- **Shuffle** re-arranges the remaining tiles on screen without changing the puzzle.
- **Deselect All** clears your current selection.
- **Submit** is only enabled once exactly 4 tiles are selected.
- A correct group of 4 locks into a colored row above the grid, showing its name and difficulty (Easy/Medium/Hard/Tricky — labeled in text as well as color, so it's colorblind-friendly).
- An incorrect guess costs a mistake. If exactly 3 of your 4 selected tiles share a true category, you'll see "One away..." as a hint.
- Four mistakes ends the puzzle and reveals every remaining category.

### Archive (Practice Mode)

Click **Archive** to browse and replay any of the 30 puzzles by title. Practice games never touch your daily stats or streak — they're purely for fun or if you want to revisit a favorite.

### Stats

Click **Stats** to see games played, wins, win rate, current streak, best streak, and average mistakes per game — calculated only from daily-mode plays.

### Sharing a Result

After finishing (win or lose), the result panel shows an emoji grid — one row per guess you made, with squares colored by each tile's true category (so a wrong guess still shows how close you were). Hit **Copy Result** to copy it to your clipboard for pasting anywhere.

### Dark / Light Mode

The moon icon in the top-right toggles between dark and light themes. It defaults to your system preference and remembers your choice for next time.

---

## Configuration

No configuration required. Everything — puzzle content, stats, and theme preference — lives in the browser's `localStorage`; nothing is sent anywhere.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Page opens but always shows "you already played today" | You already completed today's puzzle in this browser | This is by design — one attempt per UTC day. Use Archive to play any puzzle again in practice mode. |
| Stats show 0 games after playing | You played in Archive/practice mode | Practice mode intentionally does not affect stats — only the daily puzzle does. |
| Theme doesn't match system dark mode | You previously toggled it manually | Your manual choice is remembered over the system default; toggle the moon icon again to change it. |

---

## Known Limitations

- The puzzle bank has 30 entries; after day 30 the daily puzzle repeats from the top. See `FutureFeatures.md` for how to grow the bank.
- Puzzle "today" is anchored to UTC midnight, not your local timezone, so the daily puzzle changes at UTC midnight rather than at midnight in Eastern Time.
- All progress is per-browser `localStorage` — there's no account or sync, so switching browsers or devices starts a fresh stats history.
