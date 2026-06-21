# BUILD LOG — GitHub Repository Health Scorecard

## Session: 2026-06-21

---

### [Step 0] No incomplete builds
Most recent build (2026-06-18-regex-dojo on branch main + 2026-06-20-run-planner on PR #14) — both complete. Skipped.

### [Step 1] Orient
- PROFILE.md read: researcher/developer, 20+ GitHub repos, friction with managing simultaneous projects
- builds/index.md synced from PR #14 branch (claude/cool-sagan-2sn61t) — 11 builds total
- STANDARDS.md read: 15+ tests required, all must pass, Category A requires visual interface
- Today: 2026-06-21 UTC, day 172, category index 0 → A (Dashboard / Visualizer)
- Working branch: claude/cool-sagan-uvraa2

### [Step 2] Decision
- Category A pending ideas: IDs 3, 5, 6 (14 total tickets, R=1)
- lottery_chance = min(75, 25 + 1×2) = 27%
- Roll: 9 ≤ 27 → draw triggered
- Winner: ID 5 — GitHub Repository Health Scorecard (5/14 tickets)
- No idea brief linked; building from backlog row description
- Marking ID 5 as built in builds/ideas.md

### [Step 3] Build folder created
`builds/2026-06-21-github-health-scorecard/` with src/ and tests/ subdirectories

### [Step 4] PRD written
All sections filled: Goal, User Story, Scope (in/out), Tech Stack, Data Structure, Folder Structure, Testing Strategy, Success Criteria (5 verifiable criteria)

### [Step 5] Building

**src/scorer.py** — health scoring functions:
- score_recency (0–30): 5 breakpoints — today/7d/30d/90d/older
- score_ci (0–40): passing/running/no-ci/failing mapping
- score_issues (0–30): 0/1-5/6-20/>20 bands
- compute_score: composite 0–100
- health_label and health_css: 5-tier thresholds
- enrich_repo: converts raw GitHub API dict + CI run → full scored dict

**src/github_client.py** — authenticated GitHub API client:
- list_repos: paginated fetch (100 per page, loops until <100 returned)
- get_latest_ci_run: fetches latest Actions run per repo with error handling
- Both functions accept _fetch/_post injection for testability

**src/ai_summary.py** — Anthropic API integration:
- Direct urllib.request HTTP call to api.anthropic.com/v1/messages (no anthropic package needed)
- Model: claude-haiku-4-5-20251001 (fast, cost-efficient)
- Graceful fallback: returns empty string on missing key, empty repos, or any exception

**src/report.py** — self-contained HTML generator:
- Inlines ~250 lines of CSS with full dark-mode custom properties
- Embeds repo data as HTML-safe JSON (angle brackets unicode-escaped as </>)
- Chart.js 4.4.4 CDN doughnut chart for health distribution
- Interactive table: sortable columns, label filters, search box — all vanilla JS
- All repo text set via textContent (not innerHTML) — XSS-safe
- AI insights panel (html.escape() applied to all AI text)

**src/main.py** — CLI orchestrator:
- argparse: --output, --no-ai, --max-repos (for testing)
- Requires GITHUB_TOKEN; exits with error if missing
- Handles ANTHROPIC_API_KEY optionally

### [Tests] Step 6 — Tests written and run

54 tests across 4 files:
- tests/test_scorer.py: 31 tests — recency (8), CI (5), issues (7), composite (2), labels (5), CSS (1), enrich_repo (3)
- tests/test_github_client.py: 6 tests — list_repos (3), get_latest_ci_run (3)
- tests/test_report.py: 13 tests — structure, CDN, repo name, health score, dark mode, count, JSON embed, XSS, AI panel (present/absent/escaped), stats, sort controls
- tests/test_ai_summary.py: 4 tests — mock response, no key, API error, empty repos

Initial run: 53 passed, 1 failed.
Failure: test_html_xss_safe_description — json.dumps doesn't escape angle brackets by default.
Fix: Added .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026") after json.dumps in report.py.
Updated test to assert "\\u003cscript" is present (confirming the escape happened).

[UTC] Tests: 54 passed, 0 failed.

### [Verify] Step 7 — Success criteria check

1. ✓ All 54 tests pass with zero failures (confirmed above)
2. ~ python3 src/main.py --no-ai exits with "GITHUB_TOKEN not set" in this remote environment (no token available). HTML generation verified with mock data — produces valid 16KB HTML with all required elements.
3. ✓ Generated HTML verified: DOCTYPE, Chart.js CDN, sortable table, dark mode, repo data embedded, AI panel (when insights provided)
4. ✓ Stale+failing score computed correctly: pushed 2025-01-01 + failing CI + >20 issues = 10/100 (Stale label) — confirmed by test_compute_score_stale and test_enrich_repo_failing_stale
5. ✓ AI insights: renders when api_key provided (test_html_ai_panel_present_when_insights_given), absent when empty (test_html_ai_panel_absent_when_no_insights)

Note: GITHUB_TOKEN and ANTHROPIC_API_KEY are not set in this remote execution container. The tool requires GITHUB_TOKEN to run against live data. All logic is verified through mocked tests. The user can run the tool locally with their credentials.

Security checklist:
- No .env files ✓
- No hardcoded credentials ✓ (all via env vars)
- No eval() or exec() ✓
- No innerHTML from user data ✓ (tbody.innerHTML = '' is safe clear; all repo data via textContent)
- No os.system() or subprocess ✓
- No file path traversal ✓
- All code within build folder ✓

### [Docs] Step 8 — Documentation complete
- FutureFeatures.md: 7 concrete enhancements (commit trends, contributor count, nightly routine, CI drill-down, language filters, watchlist mode, open PR count)
- Manual.md: full usage guide, health score table, CI status reference, test command

Build complete. Success criteria reviewed. All tests passing.
