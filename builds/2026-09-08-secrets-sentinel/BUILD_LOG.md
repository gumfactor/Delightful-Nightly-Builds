# BUILD_LOG — Secrets Sentinel

[Step 0] No incomplete build found — last dated folder (2026-06-18-regex-dojo, local) and the most recent open PR branch (2026-09-07, True Course) both ended with "Build complete. Success criteria reviewed." Starting fresh tonight.

[Step 1] Orient — read PROFILE.md, STANDARDS.md, and resynced `builds/index.md`/`builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-703xh7`, PR #92) since local `main`/this branch's checkout was ~85 builds behind (last local dated folder was 2026-06-18; 30 open unmerged PRs exist from 2026-06-26 through 2026-09-07). Local copies of index.md/ideas.md updated from that branch's content before proceeding.

[Step 2] Category H — Developer Tool (day of year 251, index 7). Backlog lottery pool = 3 pending H ideas, all unrated → 25% draw chance. Roll: 94 → miss → fresh ideas. Generated 3 candidates, picked "Secrets Sentinel" (git-history secret scanner). Full reasoning in WhyThis.md. Non-winners (License Compliance Auditor, Config Drift Detector) appended to builds/ideas.md as rows #49/#50.

[Step 4] PRD.md written before any code — see PRD.md.

[Step 5] Build start. Building in order: entropy.py → patterns.py → scanner.py → classifier.py → report.py → main.py, with tests alongside each module.

[Step 5] Bug found and fixed during first test run: `git diff-tree -p -r <sha>` returns empty output for a repo's very first commit (no parent to diff against), which meant secrets committed in an initial commit were silently missed. Fixed by adding `--root` to `get_commit_diff` (src/scanner.py) — verified against real git output before and after the fix, not just by re-running pytest.

[Step 6] Tests: 63 passed, 0 failed. `python -m pytest tests/ -v` from the build folder. Covers: entropy scoring (12 tests), vendor pattern matching for all 6 named vendors + JWT (13 tests), git-history scanning against real temporary git repos including the initial-commit edge case and a secret added-then-removed case (12 tests), tier assignment/redaction/dedup/AI-triage-redaction-safety (12 tests), terminal/JSON/HTML report rendering including XSS-escaping (9 tests), and CLI argument handling / exit codes / file output (7 tests). No test makes a live network or Anthropic API call — all mocked or purely local git.

[Step 7] Manual end-to-end verification (not just pytest): built a real temporary demo repo with a secret added in one commit and removed in the next, a medium-tier finding (suspicious variable name + high entropy), and a low-tier finding (a checksum — high entropy, no suspicious name, correctly not flagged as urgent). Ran `python -m src.main <demo-repo> --no-ai --html-out report.html` directly against it. Confirmed: (a) the history-only secret was correctly flagged "history only" with the right remediation text, (b) the still-live secret was flagged "STILL IN HEAD", (c) the checksum was correctly tiered "low" rather than "medium" since no secret-sounding variable name was nearby, (d) the HTML report rendered with proper `&quot;`/`&lt;` escaping and the redacted placeholder — never the real secret value — appeared in the "Redacted context" column.

Success criteria review:
1. ✓ Secret added-then-removed reported with still_in_head=False and correct commit/file/line — verified by test_scan_repo_finds_secret_removed_from_head_but_present_in_history and the manual demo run
2. ✓ All 6 vendor patterns + JWT each match their canonical example and tier 'high' — test_patterns.py::test_each_vendor_pattern_matches_its_canonical_example (9 parametrized cases)
3. ✓ Redacted-context guarantee — test_classify_with_ai_never_sends_real_secret_value_to_client asserts the real secret string never appears in the mocked client's call args, and Finding has no matched_text field at all (structural guarantee, test_build_findings_never_stores_raw_matched_text_on_finding)
4. ✓ HTML report escapes injected markup — test_render_html_escapes_script_injection_in_file_path and test_render_html_escapes_injection_in_redacted_snippet
5. ✓ 63 tests, all passing (minimum was 15)

Security checklist (STANDARDS.md):
- No .env files committed
- No real credentials/keys — test/demo secrets are either AWS's own published example key (AKIAIOSFODNN7EXAMPLE) or synthetic strings, never real
- No eval()/exec() anywhere
- No innerHTML equivalent — HTML report is server-rendered Python with html.escape() on every user-controlled field, verified by test
- No subprocess call ever uses shell=True or string-interpolated shell commands — every git invocation is a fixed argv list
- No file path traversal beyond the tool's own stated purpose (scanning repos the user explicitly points it at)
- All build output confined to this build folder

Build complete. Success criteria reviewed. All tests passing.
