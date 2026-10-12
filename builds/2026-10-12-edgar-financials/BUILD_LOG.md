# BUILD_LOG — EDGAR Financials

- [08:17 UTC] Session started. Step 0: previous build (2026-10-11 Bayes Lab) logged complete. Nothing to resume.
- [08:20 UTC] Orient: category F (day 285). Lottery: pool 2 (ids 1, 10), R=1, chance 27%, roll 21 -> draw; weighted pick (7 vs 5 tickets) gave #10 SEC EDGAR Financial History Extractor. Marked `built` in ideas.md.
- [08:22 UTC] Environment notes: `gh` unavailable and `git checkout -B` onto the latest build branch was denied by the permission layer, so the work stayed on the assigned branch and `builds/index.md` / `builds/ideas.md` were synced from `origin/claude/cool-sagan-l2amdy` via `git show` (Step 1/9 intent). `pip install pytest` was also denied.
- [08:25 UTC] PRD written (before code).
- [08:40 UTC] Built: concepts, sec client (cache, throttle, retry), extract, metrics, exports, report, ai, demo, cli.
- [08:50 UTC] Deviation (soft standard): tests use stdlib `unittest` instead of pytest because pytest could not be installed. Files are named `tests/test_*.py` and are pytest-collectable. Documented in PRD Scope Changes.
- [08:52 UTC] Tests: 56 passed, 0 failed. (`PYTHONPATH=src python -m unittest discover -s tests`, also clean with `-W error`.)
- [08:55 UTC] Demo run produced all CSVs and report.html; embedded JS passes `node --check`. Chart rendering with the CDN script could not be exercised in the build container (no browser run), so chart behaviour is verified only by syntax and data checks.
- [08:57 UTC] Security checklist: no eval/exec/subprocess; no credentials in source (keys read from env); report uses html.escape for all text and `<`-escaped JSON in the script block; CSV filenames sanitised; cache and outputs only under `--out`. Live SEC calls were not made in the build (egress policy); the client was exercised only against a fake transport, so SEC response-shape assumptions follow the public companyfacts schema and are untested against the live API.
- Build complete. Success criteria reviewed. All tests passing.
