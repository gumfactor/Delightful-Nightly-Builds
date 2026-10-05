# BUILD_LOG — Burnrate

[08:16 UTC] Session start. Step 0: latest dated build (2026-09-28 on PR #112) is complete. Index synced from PR #112 branch.
[08:17 UTC] Category H (day 278). Lottery: pool 1 (#9), R=0, chance 25%, roll 11 → drew #9, but it duplicates ci-pulse (2026-06-28). Fell through to fresh ideas. Chose Burnrate.
[08:18 UTC] PRD written before code.
[08:19 UTC] Obstacle: the harness denied reading `~/.claude/projects` (real transcripts, personal data). Parser was therefore written against the documented JSONL schema and made defensive (bad lines counted, unknown fields ignored). `doctor` reports parse health so the user can confirm it against their real data; `scan.no_usage` and `bad_lines` reveal schema drift. All tests use synthetic fixtures.
[08:20 UTC] Obstacle: `pip install` denied; pytest 9.0.2 available at /root/.local/bin/pytest and used.
[08:21 UTC] Built parse/pricing/analyze/report/demo/cli. Demo renders 6 findings in headless Chromium (CDN charts not reachable in build container; tables and findings render without Chart.js).
[08:22 UTC] Test fix: the XSS test used a cwd containing '/', which the project-name parser splits; rewrote the payload to avoid slashes (test bug, not code bug).
[08:23 UTC] Tests: 36 passed, 0 failed.
[08:24 UTC] Security checklist: no network calls, no eval/exec/subprocess, no innerHTML (DOM built with textContent), JSON embedded with `<`,`>`,`&` escaped, only reads under --root.
Known limits: pricing.json values are estimates and Sonnet/Opus 5.x ids are unpriced until added; Chart.js loads from CDN so charts need internet when opening the file.

Build complete. Success criteria reviewed. All tests passing.
