# Build Log — worklog (Cross-Agent Project Activity Workstreams)

> **Date:** 2026-09-29

### Session Start
- Step 0: latest dated folder on this checkout (2026-06-18-regex-dojo) is complete. Newest PR-branch index shows 2026-09-28 Outdoor Ops complete (BUILD_LOG contains completion line).
- Category: day 272 → index 1 → B. Lottery: pool 2, R=2, chance 29%, roll 28 → draw; weighted pick #4 (rating 9) over #7 (8).
- Read idea brief before PRD.
- OBSTACLE: initial orientation used the stale `builds/index.md` on `main`. After the build was written I fetched the newest PR branch index (PR #112) and found idea #4 already built 2026-07-10 as "Worklog". Decision: keep going as a second-generation build that fixes the brief's unmet requirements (automatic capture etc.); flagged prominently in WhyThis.md and the notification. Did not read the July build's code.

### PRD written (before code). Then modules built with tests alongside.
- `pip install` was denied in this environment; a preinstalled uv-tool pytest 9.0.2 was used via PYTHONPATH. PyYAML is therefore optional (YAML test skips if absent; it ran because system python has it).
- Decisions: SQLite ledger inside `.git/worklog/`; strong keys (sha, #N, non-default branch, objective, explicit link) merge; file+time overlap merges only at score ≥0.75 (inferred) else suggestion; GitHub calls go through an injectable fetch and degrade to Git-only.
- Fixes during build: suggestion test data threshold; split test count.

### Tests
[UTC] Tests: 107 passed, 0 failed. (`PYTHONPATH=<uv pytest site-packages> python3 -m pytest tests/ -v`)
No live network calls in tests; git repos are temporary; GitHub via fake fetch.

### Verification
1. Tests pass ✔ 2. Re-sync inserts 0 new (test_sync_is_idempotent..., test_resync_after_full_flow) ✔ 3. commit+issue+PR+CI+review+checkpoint in one workstream (test_full_flow...) ✔ 4. standup/resume/why differ and cite evidence; stale flagged ✔ 5. Git-only and GitHub-failure degradation; redaction tests ✔
Security checklist: no eval/exec/os.system/shell=True/innerHTML; git invoked with argument lists; no credentials in source (the test fixture builds a fake token string to prove redaction).
Scope note: GitHub live API was not exercised (proxy); code path is covered with a fake fetch only.

Build complete. Success criteria reviewed. All tests passing.
