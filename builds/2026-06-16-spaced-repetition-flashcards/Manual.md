# Manual — Spaced Repetition Flashcards

## What It Is

A browser-based flashcard app that uses the SM-2 spaced repetition algorithm to schedule card reviews. It shows you cards you know well less often, and cards you're weak on more often — the same algorithm used by Anki.

Ships with three pre-built decks:
- **Bayesian Stats** — 20 cards on priors, posteriors, MCMC, credible intervals, model diagnostics
- **Python Research** — 15 cards on pandas, scipy, argparse, pathlib, logging, pytest
- **Git & GitHub** — 15 cards on undo/redo, stash, rebase, bisect, blame, branch management

## How to Use

### Opening the App

1. Open `index.html` in any modern browser (Chrome, Firefox, Safari)
2. No server required — double-click the file or drag it to a browser window
3. On phone: transfer the file to your device, open in browser, or add to home screen

### Daily Study Flow

1. The app opens on the **Bayesian Stats** deck with your due cards ready (or all cards on the first session)
2. Click a deck tab at the top to switch decks
3. **Read the question**, then click **Show Answer**
4. Rate your recall honestly:
   - **Again** — you didn't know it or had to guess
   - **Hard** — you knew it but it took effort or was partially wrong
   - **Good** — you remembered correctly with minor hesitation
   - **Easy** — immediate, confident recall
5. The app shows the next card automatically
6. When the queue is empty, the done screen appears

### How the Algorithm Works

Each rating adjusts the card's **ease factor** (EF) and schedules the next review:

| Rating | Next interval |
|--------|--------------|
| Again  | 1 day (resets) |
| Hard   | Same as last time |
| Good   | 1 day → 6 days → (prev × EF) |
| Easy   | 1 day → 6 days → (prev × EF) + bonus |

New cards progress: 1 day → 6 days → ~15 days → ~35 days → longer. Cards you rate Again reset to 1 day. Up to 20 new cards are introduced per deck per day.

### Persistence

All progress is stored in your browser's `localStorage` under the key `srf_state_v1`. This means:
- State persists between browser sessions on the same device
- State is not shared between devices
- Clearing browser data (site data / cache) will reset all progress

## Running Tests

From the build folder:

```bash
npm install
npx playwright test
```

Expected output: `23 passed (0 failed)`

**Note:** Requires `@playwright/test@1.56.1` and Chromium to be available. The `npm install` step handles this.

## Files

| File | Purpose |
|------|---------|
| `index.html` | The entire app — HTML, CSS, and JavaScript in one file |
| `playwright.config.js` | Playwright test configuration |
| `tests/flashcards.spec.js` | 23 automated tests |
| `package.json` | Node.js manifest for test dependencies |
