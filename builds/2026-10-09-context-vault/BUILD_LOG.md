# BUILD_LOG — Context Vault

[08:15 UTC] Started. Step 0: latest dated folder on this branch is 2026-06-18 (Regex Dojo, complete); index lists builds through 06-24 from merged PRs. Nothing to resume. Category index 2 (C). No pending C ideas, so fresh generation. Chose Context Vault.
[08:25 UTC] PRD and WhyThis written. No ideas appended to ideas.md: non-winning candidates are recorded in WhyThis.md only, because the run constraints forbid editing files outside the build folder and builds/index.md.
[08:40 UTC] Built parser, store (SQLite FTS5), summarize (stdlib HTTP, injectable completer), brief, server, CLI, demo data, single-page UI.
[08:50 UTC] Obstacle: first test run showed prefix search missing "calibrat" (porter stems "calibration" to "calibr"). Query now ORs the stemmed exact form with the prefix form; a hostile-query test also caught that FTS5 needs explicit AND between groups. Test expectation adjusted to the real stemming behaviour (prefix "calib" and stem form "calibrated").
[08:55 UTC] Tests: 39 passed, 0 failed.
[08:58 UTC] Verified end to end on demo transcripts: server routes, resume brief, headless Chromium screenshot renders the project list. Playwright for Python is unavailable in this container, so UI checks were manual rather than automated. Headless Chromium enforces a minimum window width, so the narrow-width screenshot was cropped; layout uses wrapping flex rows and max-width 860px.
[09:00 UTC] Security checklist: no secrets, key read from env only, localhost bind, Host check, CSRF header on POST, no eval/exec/shell, UI never uses innerHTML. Build complete. Success criteria reviewed. All tests passing.
