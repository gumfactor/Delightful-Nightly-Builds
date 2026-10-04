# BUILD_LOG — Neuro Arcade

- [Orient] Step 0: latest dated folder on main (2026-06-18) is complete. Index resynced from newest open PR branch (#112, 105 builds). Category G; lottery roll 73 > 25, fresh path.
- [Decide] Chose Neuro Arcade (4 cognitive paradigms). Stack: vanilla classic scripts so index.html opens from file://. No external APIs, no Anthropic calls: research/personal data stays in the browser.
- [PRD] Written before code.
- [Build] stats.js, tasks.js, store.js, app.js, styles.css. Scorers are pure and shared by the live game and CSV import.
- [Obstacle] Stimulus stored as number for Ultimatum broke CSV round trip equality (import returns strings). Fixed in app by storing strings.
- [Obstacle] 2-back/Go-No-Go UI tests missed brief stimuli in fast mode. Added `data-trial` attribute, keep stimulus in the DOM in `?test=1` mode, and use longer response windows in fast mode. No sleeps in tests.
- [Obstacle] Test label hit input maxlength=24; shortened the test payload.
- Tests: 29 passed, 0 failed.
- [Verify] Criteria: all four tasks playable and saved (UI tests); CSV round trip identical (test); reference bar and percentile per metric; 390px no horizontal scroll (test). Security checklist: no eval/exec, all user text via textContent/DOM APIs, no network calls, no credentials.
- Known limit: RT is measured from the frame after DOM update, keydown timestamp to performance.now(); browser input latency (~10-30 ms) is not corrected. Documented in Manual.md.

Build complete. Success criteria reviewed. All tests passing.
