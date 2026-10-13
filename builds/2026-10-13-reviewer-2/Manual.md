# Manual — Reviewer 2

## Run
Open `index.html` in any browser (works from `file://`, no build step, no server). Phone-friendly.

## Play
- **Daily Review**: 8 cases, same set for everyone on a given UTC date. Your score counts toward your total once per day.
- **Practice**: 8 cases weighted toward the flaw types you miss most.
- **Fresh cases from Claude**: open the section, paste an Anthropic API key, save, then "Play 3 fresh cases". The key lives in this tab's sessionStorage only and is sent only to api.anthropic.com. Cases are fictional and validated before use.
- Each case: read the study summary, pick the main flaw from four options. Correct = 10 points, +2 per streak step (max +10). Hint costs 4 points.
- Ranks: Desk Rejection, Reviewer 3 (40), Reviewer 2 (90), Reviewer 1 (150), Associate Editor (210+ total points).
- Home screen shows accuracy per flaw type. "Reset stats" clears everything (localStorage).

## Tests
```
npm install
npx playwright test
```
Uses the Chromium at `/opt/pw-browsers/chromium-1194` (edit `playwright.config.js` if yours differs). Anthropic calls are mocked.

## Notes
`node_modules/` and `test-results/` are git-ignored.
