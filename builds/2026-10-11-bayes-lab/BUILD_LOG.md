# BUILD_LOG — Bayes Lab

- [start] Step 0: latest prior build (2026-06-18-regex-dojo) complete. Today 2026-10-11, day 284 → category E.
- Orient: PROFILE, index (19 builds, ratings ≤ 4 except Qualtrics 9), STANDARDS read. Lottery skipped: no pending E ideas. Fresh ideas generated; Bayes Lab chosen.
- PRD written before code.
- Build: numeric core (`src/bayes.js`) verified in Node against known values first (Γ(5)=24, BF10 7/10 = 0.7758, PPV 1/12, Lindley p=.0466 with BF01≈10.8).
- Build: SVG charts, six lessons, router, CSS (light/dark, 375px layout).
- Decision: classic scripts + global namespace instead of ES modules, because `file://` blocks module loading and the user must be able to double-click index.html.
- Decision: no Anthropic API layer; page is fully offline and sends nothing anywhere.
- Visual check via screenshot at 420px width: no console errors.
- Tests: 34 passed, 0 failed. (`npx playwright test`; 18 core-math tests via page.evaluate, 16 UI tests.)
- Security checklist: no eval/exec, no network, no credentials. innerHTML only receives static templates and numbers; quiz history numbers are coerced with Number() before rendering.
- Build complete. Success criteria reviewed. All tests passing.
