# Manual — Lexicon

> **Version:** 1.0 (built 2026-08-02)
> **Complexity:** Ambitious Project

---

## What This Is

Lexicon is a daily letter-guessing word puzzle — the classic green/yellow/gray feedback mechanic — built entirely from real technical vocabulary across four of your own domains: neuroscience/psychology, statistics/research methods, AI/machine learning, and investing. Every day (UTC) has one deterministic word, the same for every play session on that date, drawn from a 48-word curated bank that won't repeat until the full cycle completes. It's a 2–3 minute daily habit, not a research tool — the value is a quick, genuinely fun vocabulary warm-up across the domains you actually work in.

---

## Quick Start

1. Open `index.html` directly in any modern browser (double-click it, or drag it into a browser window) — no server or install needed.
2. Type letters using your physical keyboard or the on-screen keyboard, then press Enter/⏎ to submit a guess.
3. Green = correct letter, correct position. Yellow = correct letter, wrong position. Gray = not in the word.
4. After 2 wrong guesses, the word's definition clue appears automatically to help you along.
5. Solve it (or run out of guesses) to see the result screen and a shareable emoji grid.

---

## How to Use It

### Daily Mode

The default mode. One puzzle per UTC calendar day — everyone playing on the same date gets the same word. Once you finish today's puzzle (win or lose), reloading the page shows your result again instead of a fresh board; come back tomorrow (UTC) for a new word.

### Practice Mode

Click **Practice**, pick a category from the dropdown (Neuroscience/Psychology, Statistics/Methods, AI/Machine Learning, or Investing/Finance), and play an unlimited random word from that category. Practice rounds never affect your daily streak or stats — they're for warming up or drilling a specific domain.

### Hints

The deterministic definition clue always appears after your 2nd wrong guess, at no cost and no setup. If you want an extra, more creative hint before that, enter your own Anthropic API key in the "AI bonus hint" box (see Configuration below) and click **Get AI hint**. Without a key, the button still works — it shows a fallback hint (first letter, word length, category) with zero network activity.

### Stats

The stats panel below the board tracks games played, win percentage, current and max streak, and your accuracy per category — all stored locally in your browser (`localStorage`), never sent anywhere.

### Colorblind Mode

Check the "Colorblind mode" box to add a shape marker (✓ correct, ● present, ✗ absent) to every tile in addition to its color, so the feedback doesn't rely on color alone.

### Sharing

After finishing a round, copy the text under "share-text" in the result screen — it's the same emoji-grid format used elsewhere (🟩🟨⬛), with no spoilers of the actual word.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| Anthropic API key | (empty) | Optional, entered per-session in the "AI bonus hint" field. Never written to `localStorage` or sent anywhere except directly to `api.anthropic.com` when you click "Get AI hint". Cleared when you close or reload the page. |
| Colorblind mode | off | Persisted in `localStorage`; adds shape markers to tiles. |

No other configuration is required — the word bank and daily-cycle schedule are fixed in `src/words.js` and `src/main.js`.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "AI bonus hint" always shows the fallback text | No API key entered, or the key is invalid/rate-limited | Enter a valid Anthropic API key; the fallback is intentional and safe with no key — it's not a bug |
| Today's puzzle looks "stuck" on a result screen | You already completed today's daily round | Expected — one daily round per UTC date. Use Practice mode to keep playing, or come back after UTC midnight |
| Stats reset unexpectedly | Browser `localStorage` was cleared (private/incognito mode, manual clear, different browser/profile) | Stats are local to one browser profile by design — there is no server sync |

---

## Known Limitations

- Guesses are validated only as A–Z strings of the correct length, not against a real dictionary — this is a domain-vocabulary game, not general Wordle, so "nonsense" guesses are allowed and simply won't match
- No mobile app or offline install — it's a single `index.html` file you open in a browser
- The AI bonus hint requires your own Anthropic API key; it is not bundled or required for the core game
