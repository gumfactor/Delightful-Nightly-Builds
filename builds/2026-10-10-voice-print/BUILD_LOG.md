# Build Log — Voice Print

- [Orient] 2026-10-10, day 283, category index 3 = D. Step 0: latest dated folder on this branch (2026-06-18) is complete. Lottery skipped: no pending D ideas. Only main is visible locally; no gh CLI, so index resync uses the local copy.
- [Decide] Voice Print chosen over live-weather landscape and lecture vignette generator. See WhyThis.md.
- [PRD] Written before code.
- [Build] analyzer.js (tokenizer, metrics, 9 detectors, profile build/merge, comparison, revision prompt), samples.js, app.js, style.css, index.html.
- [Tuning] Contrast-frame regex initially missed "X is not just a skill — it's Y"; widened. Em-dash test fixture was too short to be "rare"; fixed the test data, not the threshold.
- [Tests] 17 logic + 12 UI Playwright tests. Tests: 29 passed, 0 failed. (`npx playwright test`; uses /opt/pw-browsers/chromium if present.)
- [Verify] Criteria 1-5 checked by tests: machine demo ai>60 vs human <20; held-out own-style text voice match beats machine by >25; spans highlighted with tooltips; profile persists and round-trips; drafts rendered via textContent (XSS test). Security grep: no eval/exec/innerHTML/network calls/keys.
- [Scope] No API call from the page by design (privacy); revision prompt is copy-paste. Thresholds are heuristics tuned on two demo texts: documented in Manual.
- [Docs] FutureFeatures.md, Manual.md written.

Build complete. Success criteria reviewed. All tests passing.
