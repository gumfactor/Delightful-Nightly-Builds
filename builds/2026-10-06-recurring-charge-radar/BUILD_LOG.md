# BUILD_LOG — Recurring Charge Radar

[08:10 UTC] Step 0: latest prior build (2026-06-24 AI Lecture Builder) is in the catalog and complete; nothing to resume. Category index (279-1)%9=8 → I. No pending Category I backlog rows → fresh ideas (no lottery). Chose Recurring Charge Radar; other candidates documented in WhyThis.md. Non-winning ideas NOT appended to ideas.md: the task constraints for this scheduled run restrict edits to the build folder and builds/index.md.
[08:12 UTC] PRD and WhyThis written before code.
[08:15 UTC] Obstacle: `pip install pytest` was denied by the environment, so pytest is unavailable. Decision: write tests with stdlib `unittest` (pytest collects them too), so the suite runs with zero installs. Deviation from the CLAUDE.md pytest default, recorded here.
[08:25 UTC] Built parsers (RBC/TD/CIBC/Scotia/BMO/generic), normalize, detect, forecast/ICS, rules, report, CLI, demo generator.
[08:35 UTC] Bug found by tests: a one-off price spike polluted the running price level, producing a false price change on the next charge. Fixed in detect.segment_levels (spikes no longer enter the baseline).
[08:40 UTC] Tests: 59 passed, 0 failed.
[08:42 UTC] Visual check: rendered demo report in headless Chromium; layout fits at 500px (the browser's minimum window width) with no horizontal scroll; mobile viewport meta present.
Security checklist: no network code, no eval/exec/subprocess, no innerHTML (DOM built with textContent), embedded JSON escapes `<`, `>`, `&`; file paths come only from CLI args the user supplies.
Build complete. Success criteria reviewed. All tests passing.
