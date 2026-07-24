# Manual — Heuristic Hunt

> **Version:** 1.0 (built 2026-07-24)
> **Complexity:** Ambitious

---

## What This Is

Heuristic Hunt is a browser game that trains you to recognize 12 common cognitive biases and decision-making heuristics — anchoring, confirmation bias, sunk cost fallacy, loss aversion, overconfidence, and more — by reading short, realistic scenarios and identifying which bias is at play. Scenarios are drawn from research/lab life, investing decisions, and everyday situations. Every answer comes with an explanation of why it's correct and why the tempting alternatives are close-but-wrong, so wrong answers teach as much as right ones.

---

## Quick Start

1. Open `index.html` directly in any modern browser (double-click it, or drag it into a browser window — no server or install needed).
2. From the main menu, click **Play Campaign** to start Chapter 1.
3. Read the scenario, pick the bias you think applies from the four options.
4. Read the feedback and explanation, then click **Next Question**.
5. Score 70% or higher on a chapter to unlock the next one.

---

## How to Use It

### Play Campaign

Three chapters of 10 questions each, increasing in subtlety. Chapter 1 is unlocked from the start; each subsequent chapter unlocks once you score 70% or higher on the one before it. You can retry any unlocked chapter as many times as you like — your lifetime accuracy per chapter is shown on the chapter-select screen, but only your most recent attempt's score decides whether the next chapter unlocks.

### Daily Challenge

A 5-question set, the same for every player on a given UTC calendar day, chosen deterministically by the date. You can play it once per UTC day. After finishing, you get a shareable emoji result grid (🟩/🟥) and a **Copy Result** button that copies your score and grid to the clipboard — paste it anywhere you'd share a Wordle-style result.

### Practice by Bias

Drill any single bias on demand, independent of campaign progress — useful for shoring up a specific weak spot the Mastery Dashboard flags. **All Biases (mixed)** pulls a shuffled mix of all 30 vignettes.

### Mastery Dashboard

Shows your lifetime attempts, correct answers, and accuracy for each of the 12 biases, with a color-coded bar: green (≥80% accuracy), yellow (50-79%), red (<50%), gray (not yet attempted). This updates from every mode — Campaign, Daily Challenge, and Practice all count toward it.

### Reset Progress

Clears all chapter unlocks, mastery stats, streaks, and daily challenge history back to a fresh install. There's a confirmation screen before anything is cleared — this cannot be undone afterward.

---

## Configuration

No configuration required. All progress is stored in your browser's `localStorage` under the key `heuristicHunt_v1` and never leaves your machine.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Progress resets every time I reopen the page | Browser is in a private/incognito window, or third-party cookies/storage are blocked for `file://` pages | Open the file in a normal (non-private) browser window; some browsers restrict `localStorage` for local files in strict privacy modes |
| Daily Challenge says "already played" but I don't remember playing today | Your system clock or timezone made "today" roll over in UTC, not your local time | The Daily Challenge always uses UTC, not local time — check what date it currently is in UTC |
| Copy Result button doesn't seem to do anything | Some browsers require a user gesture and a secure/local context for clipboard access, and a few restrict clipboard writes from `file://` pages entirely | The button still updates to "Copied!" as visual confirmation; if the paste doesn't work, manually note the emoji grid and score shown on screen |

---

## Known Limitations

- The 30 vignettes are fixed at build time — there's no in-app way to add new scenarios (see FutureFeatures.md for a proposed community-vignette overlay).
- Practice mode's question order is randomized each time using the browser's own randomness (not date-seeded like the Daily Challenge), so it's not reproducible across sessions.
- All 12 biases are drawn from Western behavioral-economics/psychology literature; the taxonomy doesn't cover culturally-specific decision heuristics.

---

## Running the Tests

```bash
cd builds/2026-07-24-heuristic-hunt
npm install
npx playwright test
```

22 Playwright tests cover data integrity, chapter gating/unlocking and persistence, answer feedback, Daily Challenge determinism and once-per-day gating, practice mode, the Mastery Dashboard, Reset Progress, console-error-free playthroughs, and mobile layout.
