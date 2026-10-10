# Voice Print: Manual

## Open it
Open `index.html` in any browser. No server, no install, no network. (Optional: `npm start` serves it on http://localhost:8080.)

## Use it
1. **Your voice.** Paste at least 40 words (150+ is better) of your own writing and press *Add to profile*. Repeat with more samples; each one is merged in. The profile is stored in this browser's localStorage. *Use demo human text* loads a sample for a trial run.
2. **Draft to check.** Paste a draft. Results update as you type.
3. **Results.**
   - *AI-tell score* (0-100): weighted density of machine-prose habits (stock vocabulary, filler phrases, "not just X but Y", stiff transitions, tacked-on participles, rhetorical openers, rule-of-three lists, hedges, em-dash overuse, even rhythm, no first person). Under about 25 reads human; over about 55 is heavy.
   - *Voice match* (0-100): how close the draft's measured style sits to your profile (sentence length and variation, commas, dashes, contractions, first person, questions, long words, common function words). Needs a profile.
   - *Highlighted draft*: hover or long-press a highlight for the reason. Colours are grouped in the list below it.
   - *Sentence rhythm*: one bar per sentence. A flat row of bars is the classic machine pattern.
   - *Compared with your voice*: per-measure draft vs. you, marked close / a bit off / far.
4. **Revision prompt.** *Build revision prompt* assembles the flagged examples and your measured targets plus the draft. *Copy* puts it on the clipboard for Claude.

## Profile backup
Open *Export / import profile*. *Show profile JSON* prints it; paste JSON back and press *Import pasted JSON*, or use *Import file*. *Clear profile* deletes it.

## Limits
This is a style linter, not an AI detector. Heuristic thresholds were tuned on small demo texts; short drafts (under about 100 words) give noisy scores. Your text never leaves the page.

## Tests
```
npm install
npx playwright test
```
Uses `/opt/pw-browsers/chromium` when present, otherwise Playwright's own browser (`npx playwright install chromium`).
