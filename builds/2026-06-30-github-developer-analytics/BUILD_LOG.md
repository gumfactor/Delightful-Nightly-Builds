# BUILD LOG — GitHub Developer Analytics Dashboard

## Session: 2026-06-30

---

### [Orient] Step 0 — No incomplete builds
Most recent local build (2026-06-18-regex-dojo) ends with "Build complete. Success criteria reviewed. All tests passing." Skipped.

### [Orient] Step 1 — Orientation complete
- PROFILE.md read: developer/neuroscience researcher, manages many projects, values tools that save real time, prefers functional over flashy
- index.md read: 19 builds total through 2026-06-24; last build was AI Lecture Builder (D) rated 2/10; pattern of low scores for builds that duplicate existing tools or lack visual interfaces
- STANDARDS.md read: 15+ tests required, all must pass, visual interface mandatory for Category A

### [Decide] Step 2 — Decision
- Day 181 → category_index = 0 → A (Dashboard / Visualizer)
- Lottery roll 81 > 27% threshold → fresh ideas
- 3 candidates generated; winner: GitHub Developer Analytics Dashboard
- Runners-up added to ideas.md: Kwyeter Noise Profile Visualizer, Canada List Category Intelligence Dashboard
- Note: ANTHROPIC_API_KEY not available in this routine environment; OpenAlex and other external APIs blocked by proxy; GitHub API accessible via GITHUB_TOKEN ✓

### [Create] Step 3 — Build folder created
`builds/2026-06-30-github-developer-analytics/` with `src/` and `tests/` subdirectories

### [PRD] Step 4 — PRD written
All sections filled. Goal: personal coding pattern dashboard from live GitHub data. 4 tabs: Overview, Timeline, Rhythm, Languages. Tech: Python 3 + requests + pytest; HTML/Chart.js 4.4.4. 20+ tests planned.

### [Build] Step 5 — Building
Writing src/github_client.py, src/analytics.py, src/renderer.py, src/main.py, tests/

Key decisions:
- ANTHROPIC_API_KEY not available in this routine environment → AI layer omitted; documented in WhyThis.md
- External APIs (OpenAlex, arXiv) blocked by network proxy → GitHub API (accessible) drives all data
- Token has limited scope (no private repo commits access): github_client._get() returns None on permission 403s; get_commits() gracefully returns [] for inaccessible repos
- GitHub returns 409 for empty repos on commits endpoint → treated same as 404 (return None)
- innerHTML with data-derived values: added esc() helper in JS to safely HTML-escape before insertion

### [Tests] Step 6 — Tests
Initial test run: 58 passed, 2 failed (test bounds wrong for build_since_iso — function correctly returns first of month N months ago, not exactly N*30 days). Fixed test bounds.
After adding 409 and permission-403 test cases: 61 passed, 0 failed.

[08:25 UTC] Tests: 61 passed, 0 failed.

### [Live run] Step 5b — End-to-end verification
Ran `python3 src/main.py --output dashboard.html` against live GitHub API.
Result: 524 commits, 16 active repos, 23 repos scanned.
Most active: TheCanadaList. Top language: Python.
Languages found: Python, HTML, Dart, TypeScript, JavaScript, Jupyter Notebook, CSS, PLpgSQL.
Dashboard file: 520 lines, self-contained HTML with Chart.js 4.4.4 CDN.

### [Verify] Step 7 — Success criteria check
1. ✓ Live data: 524 real commits fetched from GitHub API
2. ✓ Timeline heatmap: present and populated with real commit data
3. ✓ All four tabs: Overview, Timeline, Rhythm, Languages all present with correct chart elements
4. ✓ Edge-case safety: empty repos (409) and permission-denied (403) handled gracefully, 7 inaccessible repos skipped without crash
5. ✓ Tests pass: 61 passed, 0 failed

Security checklist:
- No .env files committed ✓
- No hardcoded credentials ✓
- No eval()/exec() ✓
- innerHTML guarded with esc() helper ✓
- No os.system()/subprocess with user data ✓
- No file path traversal ✓
- All code self-contained in build folder ✓

### [Docs] Step 8 — Documentation complete
- FutureFeatures.md: 7 concrete enhancements
- Manual.md: usage guide, CLI options, notes on timezone and token scope

**Late discovery (Step 9 sync):** Syncing index.md from the most recent open PR branch revealed a 2026-06-26 "GitHub Developer Activity Explorer" (F category) that already includes hourly heatmap and day-of-week distribution — two of my four tabs overlap. This was not visible at Step 1 (I read local index.md which only went to 2026-06-24; I did not fetch the PR branch at Step 1 as required). The unique contributions of tonight's build are: (1) the project-vs-month CSS grid heatmap (different from a weekly volume chart), and (2) the language evolution stacked bar chart. The rhythm section (hour + weekday) is a genuine overlap with 2026-06-26.

Build complete. Success criteria reviewed. All tests passing.

