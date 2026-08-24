# Build Log — Lecture Loom

> **Date:** 2026-08-24
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:05 UTC] Session Start

- Checked `builds/` for an interrupted prior session: the most recent local dated folder (2026-06-18-regex-dojo) ended with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- `builds/index.md` on this branch's base is weeks stale (last local entry 2026-06-18). Fetched the most recently opened PR branch (`origin/claude/cool-sagan-rik1w6`, PR #79, 2026-08-23, merged state: open/clean) and read its `builds/index.md` and `builds/ideas.md` directly via `git show` — 72 total builds, last build 2026-08-23 (Trading Book).
- Read PROFILE.md, STANDARDS.md in full.
- Day of year for 2026-08-24 (UTC) = 236 → `category_index = (236-1) % 9 = 1` → **Category B — Productivity Utility**.
- Category B backlog scan (from the synced `ideas.md`): two `pending` rows match — idea #13 (Course Material Batch Formatter, added 2026-08-15) and idea #14 (Multi-Repo Dependency Batch Auditor, added 2026-08-15). Both ratings blank → 5 tickets each, R = 0 → `lottery_chance = min(75, 25 + 0*2) = 25%`.
- Rolled 1–100 for the lottery gate: **2** → ≤25%, so the pool draws.
- Weighted draw over the 2 pending ideas (5 tickets each, 10 total): rolled 1–10 → **4** → falls in idea #13's 1–5 range. **Idea #13, "Course Material Batch Formatter," wins the draw.**
- Idea #13 has no linked Idea Brief, so Step 2e is a no-op.
- Idea #13's own Rating Notes (recorded 2026-08-15, when it was passed over for Provenance) flag a real design risk: "same failure signature as 2026-06-24's AI Lecture Builder (2/10): a power user replicates the AI-formatting step with one prompt... Would need a genuinely verifiable non-AI core... to be worth building." Per CLAUDE.md's lottery rules the drawn idea is built, not re-rolled — but that critique is a legitimate, specific design note, not a staleness/duplicate flag, so the implementation below deliberately makes the deterministic layer (timing-budget verification, objective-completeness checks, structural consistency checks) the load-bearing core, with the AI polish step as optional enrichment only. Documented in full in `WhyThis.md`.
- Marked idea #13 `built` in `builds/ideas.md` (done at Step 9, alongside the index.md sync).
- Deciding tonight's build: **Lecture Loom** — a Python CLI that batch-converts a folder of raw lecture notes into a consistent slide-outline + student handout, backed by a deterministic per-lecture timing/objective/structure-consistency engine (not just an AI rewrite pass).
- Build folder created: `builds/2026-08-24-lecture-loom/`

### [08:20 UTC] PRD Written

- Goal: turn a folder of raw, inconsistently-structured lecture notes into a consistent slide outline + student handout per lecture, with a deterministic timing-budget and completeness check flagging real problems (over-length sections, missing objectives, empty sections) before the professor ever presents.
- Scope: markdown-heading/bullet parser, objective-extraction heuristics, word-count-based timing model with configurable words-per-minute and target minutes, section-density outlier detection, per-lecture outline.md + handout.md generation, batch-wide self-contained HTML dashboard, optional Claude Haiku polish layer (bullet cleanup + discussion questions) with an unconditional deterministic fallback, companion Claude Code Skill wrapper.
- Notable constraints: no third-party packages (stdlib only, matching this container's `pip install` restriction and prior builds' precedent); `ANTHROPIC_API_KEY` never set in the build container — all AI-path tests use a mocked `urlopen`.

### [09:10 UTC] Build Phase

- Implemented `src/parser.py` (deterministic Markdown structural parser: title/objectives/sections/bullets, heading-level-skip detection, two independent objective-extraction paths — an explicit "Objectives" heading block and a "By the end of this lecture... students will..." sentence pattern), `src/timing.py` (word-count-based timing engine, ±10% budget classification, section-density outlier detection, objective-completeness classification — this is the load-bearing deterministic core the idea's Rating Notes asked for), `src/ai_polish.py` (optional Claude Haiku bullet polish + discussion questions, unconditional deterministic fallback), `src/formatter.py` (outline.md/handout.md generation), `src/render.py` (self-contained dark-mode HTML batch dashboard, JSON-in-`<script>` delivery with `</` escaped to prevent premature script-tag termination, DOM built via `createElement`/`textContent` only), and `src/main.py` (CLI: `check`/`format`/`render`).
- Wrote 4 hand-authored fixture lecture files (`fixtures/`) covering: a well-formed lecture with explicit objectives, a lecture with none, one using the "By the end..." sentence pattern with no explicit heading, and one with a skipped heading level (H1 → H3).
- Wrote a companion Claude Code Skill (`skill/SKILL.md`) so the tool can be invoked as `/lecture-loom <folder>` inside a coding session, per CLAUDE.md's guidance that on-demand productivity tools are usually a better fit as a Skill than a bare script.

### [09:35 UTC] Tests Run

Tests: 56 passed, 0 failed. (`/root/.local/bin/pytest tests/ -v`; the user's own machine runs `python -m pytest tests/ -v` per `Manual.md` once `pytest` is installed — stdlib-only source, `pytest` is a dev-only dependency)

Two test-authoring bugs (not source bugs) were caught and fixed during the first run: `test_dashboard_renders_valid_html_shell` asserted a lecture title never appears anywhere in the HTML, which is wrong — it correctly appears inside the escaped JSON `<script type="application/json">` payload, never as raw markup; and `test_xss_payload_in_title_never_breaks_out_of_script_tag` asserted exactly 2 occurrences of the substring `<script` in the page, not realizing a malicious title's un-slashed `<script>` fragment (as opposed to `</script>`) is inert text while a browser is already inside a `<script>` element's raw-text parsing mode — the real security invariant is that the *closing* sequence `</script` appears exactly twice (the two tags this build authors), which the fixed assertion now checks.

### [09:50 UTC] Manual Verification — Live in Headless Chromium

Generated a real `dashboard.html` via `python3 src/main.py render` over the 4 committed fixtures plus a deliberately malicious 5th file (`</script><script>window.__xss=true;</script>` as the lecture title, `<img src=x onerror="window.__xss2=true">` as a bullet) using the global npm Playwright 1.56.1 install driving this container's pre-installed Chromium (`/opt/pw-browsers/chromium`). Confirmed live: zero page errors and zero console errors, zero dialogs fired, `window.__xss`/`window.__xss2` both stayed `undefined` (neither payload executed), all 5 lecture rows rendered, the search box correctly filtered to 1 row on "Stress", clicking a row correctly toggled its detail panel visible, and at a 375px mobile viewport `document.documentElement.scrollWidth` equalled `clientWidth` (no horizontal overflow). Also ran `check` over the same batch from the terminal and confirmed the heading-skip warning and missing-objectives flag both surfaced correctly for the `heading_skip_lecture.md` fixture, matching the automated test's expectation.

### [10:00 UTC] Documentation

- `FutureFeatures.md`: 7 concrete suggestions across quick-wins/medium/ambitious tiers.
- `Manual.md`: quick start, all 3 commands, configuration table, troubleshooting, known limitations.

### [10:05 UTC] Verify — Step 7 Success Criteria Check

1. ✓ All 56 tests pass (zero failures) — confirmed above.
2. ✓ A deliberately-inserted timing overrun (`test_over_budget_flag_matches_hand_computed_value`) reports `over_budget` with the correct named section, matching a hand-computed 10-words-at-10-wpm = 1.0 minute reference value.
3. ✓ A no-objectives fixture is flagged `missing` (`test_no_objectives_fixture_flags_missing`, and reconfirmed live via `check`).
4. ✓ `render` produces a working, mobile-readable dashboard — verified live in headless Chromium above (zero errors, injected XSS payload confirmed inert, no horizontal overflow at 375px).
5. ✓ With no `ANTHROPIC_API_KEY` set, every command (including `--ai-polish`) makes zero network calls, verified both by a monkeypatched-`urlopen`-raises-if-called test and by the deterministic-fallback unit tests.

Security checklist (STANDARDS.md):
- No `.env` files committed.
- No hardcoded credentials/API keys/passwords.
- No `eval()`/`exec()` on user-controlled input.
- No `innerHTML` assignment anywhere — `render.py`'s JS builds the DOM exclusively via `createElement`/`textContent`.
- No `os.system()`/`subprocess` calls at all.
- No file paths built from user-controlled strings beyond the CLI's own `path`/`--output` arguments, which are the tool's documented purpose (no traversal beyond what argparse already receives).
- All code lives under this build's own folder; no reads/writes outside it.

Build complete. Success criteria reviewed. All tests passing.

