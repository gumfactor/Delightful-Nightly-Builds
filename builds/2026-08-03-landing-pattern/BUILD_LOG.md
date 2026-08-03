# Build Log — Landing Pattern

> **Date:** 2026-08-03
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:13 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked local `builds/` for an incomplete build — most recent local dated folder is `2026-06-18-regex-dojo`, whose `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed." No resume needed.
- Step 1: per CLAUDE.md's instruction to read the most current `builds/index.md` from the most recent open PR branch (not the possibly-stale copy on `main`), fetched `origin/claude/cool-sagan-ubh0h8` (PR #59, 2026-08-02 "Lexicon") — the newest of many currently open PRs on this repo, none merged (exact count corrected to 50 during manual verification below — an initial paginated listing under-reported it). `main` itself is still at the 2026-06-18 build. This gap is noted for the user separately from tonight's build; it doesn't block tonight's session since my job is to develop on my own branch and push, same as every other open PR here.
- Today (2026-08-03) is day-of-year 215 → `(215-1) % 9 = 7` → Category H — Developer Tool.
- Category H backlog (from the fetched `builds/ideas.md`): 3 pending rows, none rated (R=0, lottery_chance=25%). Rolled 100/100 — missed the draw → fresh generation.
- Decided to build: **Landing Pattern** — a PR merge-order and file-conflict-risk planner. Full reasoning in `WhyThis.md`.
- Build folder created: `builds/2026-08-03-landing-pattern/`

### [08:24 UTC] PRD Written

- Goal: given a repo's open PRs, classify each one's merge readiness, detect changed-file overlaps between PRs, and produce a two-batch recommended merge order plus a sorted "blocked" list with specific reasons.
- Scope: `sync` (GitHub API → SQLite snapshot), `report` (text/json/html), `history` (per-PR trend across snapshots), optional `--ai` Claude Haiku one-line notes on blocked PRs with a deterministic fallback.
- Notable constraints: stdlib only (urllib for both GitHub and Anthropic HTTP calls — no SDK dependency); read-only against GitHub (no merge/close/comment actions); all tests mock every external HTTP call per PROFILE.md's Data Sources rules.

### [08:26 UTC] Build Phase — core package

Writing `landing_pattern/` modules: `analysis.py` (pure, no I/O — readiness classification, file-overlap graph, two-batch merge ordering), `github_client.py` (thin injectable HTTP wrapper), `storage.py` (SQLite snapshot persistence), `ai_summary.py` (optional Claude Haiku call + deterministic fallback), `report.py` (text/json/html rendering, HTML-escaped), `cli.py` (argparse: sync/report/history), `main.py` entry point.

### [08:32 UTC] Tests — Step 6

Ran `python -m pytest tests/ -v`. First run: 63 passed, 5 failed — all 5 failures were `KeyError: 'age_days'` in `report.render_html`'s Batch 2 table, because `analysis.recommend_merge_order`'s Batch 2 entries carried `number`/`title`/`conflicts_with` but not `age_days`, while every other PR row in the report expects it. Real bug, not a test-fixture issue: fixed by adding `age_days` to the Batch 2 dict in `analysis.py`, then fixed the same gap in the test fixture that had copied the same incomplete shape. Also tightened `report.render_html`'s AI-note check from "key present" to "value truthy" so an empty note string doesn't render an empty `<div class="note">`.

Tests: 68 passed, 0 failed.

### [08:35 UTC] Manual verification against this repo's real PR backlog — Step 4 continued

`GITHUB_TOKEN` REST access is blocked in this build container (403 "GitHub access is not enabled for this session" — the container routes GitHub access through the GitHub MCP connector, not raw REST). This is the documented build-container network constraint from CLAUDE.md, not a design signal — `github_client.py` is unit-tested against a mocked `_api_get` (11 tests) and is written to call the real GitHub REST API exactly as `git`/`gh` do; it will work unmodified wherever a real `GITHUB_TOKEN` has REST access, which every environment outside this specific sandboxed container has.

To still verify the actual analysis/report logic end-to-end against real data rather than only synthetic fixtures, I used the GitHub MCP connector (available in this session for a different purpose — orientation) to pull real PR metadata for a 10-PR sample spanning this repo's full age range: the 5 newest PRs (#59, #58, #57, #55, #53) and 5 of the oldest (#15, #12, #10, #5, #3). This also caught a real orientation error: my first `list_pull_requests` call used the tool's default page size and silently returned only 30 of the repo's PRs, leading me to report "31 open PRs" in `WhyThis.md`. A `perPage=100` re-listing during this verification pass found the true count is **50 open PRs**, running from #3 (2026-06-11) to #59 (2026-08-02) — corrected in `WhyThis.md`.

The real data confirmed the exact scenario this build exists to catch: `mergeable_state` was `clean` for all 5 newest PRs (all based on the current `main` tip) and `dirty` for all 5 sampled older PRs (based on stale commits, now conflicting after later merges). Fetching each PR's changed-file list confirmed every single one of the 5 "clean" PRs touches `builds/index.md` and `builds/ideas.md` — meaning if merged carelessly, the second one in would immediately conflict with the first. Fed this real 10-PR fixture directly through `analysis.build_report()` and `report.render_text()`/`render_html()` (bypassing only the blocked-in-this-container `github_client.fetch_repo_prs_full`, which is what a user's local `sync` run would call instead): the tool correctly placed the oldest clean PR (#53) alone in Batch 1, correctly demoted #55/#57/#58/#59 to Batch 2 with `conflicts_with: [53]`, and correctly sorted all 5 dirty PRs into Blocked with the `conflict` label, oldest first. Rendered HTML report opened cleanly with no missing fields after the Batch 2 fix above.

### [08:36 UTC] Headless browser verification

Rendered `report.render_html()` for a fixture PR with title `<script>alert(1)</script>` in Batch 1 and an AI note `<img src=x onerror=alert(2)>` on a Blocked PR, then opened it in headless Chromium (`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`) via `file://`. Results: zero console errors, zero `pageerror` events, zero `<script>` elements present on the rendered page, no `dialog` event fired (confirming no `alert()` ever executed), and the payload strings are present in the page's text content only as inert literal text. Satisfies PRD Success Criterion 4 directly.

### [08:40 UTC] Verify — Step 7

Success criteria review against `PRD.md`:
1. ✅ All tests pass — 68 passed, 0 failed
2. ✅ Overlapping-file fixture correctly splits Batch 1/Batch 2 — confirmed by `test_merge_order_demotes_overlapping_pr_to_batch2` and `test_merge_order_three_way_overlap_does_not_crash`, plus the real 10-PR manual run above (#53 in Batch 1, #55/#57/#58/#59 correctly demoted to Batch 2)
3. ✅ Every Blocked PR shows a specific, correct label — confirmed by `test_blocked_sort_prioritizes_actionable_reasons` and the manual run (all 5 real `dirty` PRs correctly labeled `conflict`)
4. ✅ HTML report opens via `file://` with zero console errors and escapes a `<script>` payload — confirmed by the headless-browser check above and `test_html_output_escapes_script_payload_in_title`
5. ✅ Two `sync` runs produce two distinct history rows, `history --pr N` shows both — confirmed by `test_two_syncs_create_two_distinct_rows_not_an_overwrite` and `test_history_for_pr_returns_chronological_trend`

STANDARDS.md security checklist:
- All output confined to `builds/2026-08-03-landing-pattern/` — confirmed, no writes outside the build folder during development (temp verification files were written to the session scratchpad, not this repo)
- No hardcoded credentials — `GITHUB_TOKEN`/`ANTHROPIC_API_KEY` read from environment only, never written to source
- No personal data hardcoded — all fixtures use synthetic or already-public repo data (this repo's own public PR titles/numbers)
- No calls to paid/auth-required APIs outside PROFILE.md's Data Sources — GitHub API (`GITHUB_TOKEN`, listed) and Anthropic API (`ANTHROPIC_API_KEY`, listed as runtime-only) only
- No user-entered or personal data sent to a third party — `ai_summary.py` sends only PR title, blocking label, file count, and age to Claude; never diff content, never GitHub usernames/emails
- No `eval()`/`exec()`/user-controlled shell strings anywhere in the codebase
- Read-only against GitHub — no merge, close, comment, or write endpoint is ever called

### [08:42 UTC] Documentation — Step 8

- `FutureFeatures.md` — 8 concrete suggestions (3 quick wins, 3 medium-effort, 2 ambitious)
- `Manual.md` — quick start, full command reference, configuration table, troubleshooting table, known limitations

Build complete. Success criteria reviewed. All tests passing.
