# Build Log — AgentLint

> **Date:** 2026-07-16
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:05 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked `builds/` for an interrupted session. Local `builds/` only goes up to 2026-06-18 (regex-dojo), but that is expected — each night's PR is branched from `main` and only carries its own dated folder; the real catalog lives across many still-open PR branches. Fetched the most recently created open PR branch (`claude/cool-sagan-xkxtqj`, PR #42, 2026-07-15 "Confound Hunter") and read its `builds/index.md` and `builds/ideas.md` directly — that build's own `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing," so there is nothing to resume. Proceeding to tonight's new build.
- Day of year for 2026-07-16 is 197 → `(197-1) % 9 = 7` → category index 7 → **H — Developer Tool**. Cross-checked against history: 2026-07-07 (exactly 9 days earlier) was also H (Schema Sentinel) — confirms the rotation math.
- Checked `builds/ideas.md` (resynced copy) for pending Category H rows: none (the only H entry, #9, is already `built`). Lottery pool empty → generating fresh ideas per Step 2d.
- Topic diversity check on the last 10 builds (07-06 through 07-15): no domain repeated more than twice; no override needed.
- Generated 3 candidate ideas for Category H (see WhyThis.md for full comparison). Chose **AgentLint** — an auditor for AI agent instruction files (CLAUDE.md/AGENTS.md-style docs): deterministic checks for broken references/anchors/missing sections, plus an optional Claude-powered semantic review that can catch drift between a claim in the instructions and the real data it describes. This directly targets a real bug found while orienting tonight: this repo's own `CLAUDE.md` calibration note ("every build has scored 4/10 or below") is now false against `builds/index.md` (Qualtrics scored 9/10, and several others score above 4). That drift is the exact failure mode the AI-review path is designed to catch.
- Build folder created: `builds/2026-07-16-agentlint/`

### [08:20 UTC] PRD Written

- Goal: audit agent instruction files for broken references, missing sections, contradictions, and semantic drift vs. real project data.
- Scope: markdown parser, 4 deterministic checks, optional AI semantic review (mocked in all tests, real calls only at runtime with a user-supplied `ANTHROPIC_API_KEY`), text/JSON/HTML report rendering, CLI with `--fail-on` gating, a Claude Code Skill wrapper.
- Notable constraint: `ANTHROPIC_API_KEY` is not set in the build container, so the AI-review path is implemented against the documented Claude Messages API contract and exercised entirely through mocked `urllib.request.urlopen` calls in tests — never a live call during the build, per CLAUDE.md.
- Deployment model decision: Developer Tool invoked repeatedly across many of the user's own projects → shipped as both a standalone CLI (testable, usable outside Claude Code) and a Claude Code Skill wrapper, per CLAUDE.md's guidance that recurring developer tools are usually a better fit as a Skill than a bare script.

### [09:10 UTC] Build Phase — Parser + Deterministic Checks

- `src/parser.py`: heading extraction with GitHub-style slugification (including the `-1`, `-2`, ... suffixing GitHub applies to duplicate headings), inline-code file-path-candidate extraction (filtered to strings with a recognized file extension or trailing slash, to avoid flagging things like `git status` or `foo()` as broken "paths"), and markdown link classification into internal-anchor / relative-file / external-URL buckets.
- `src/checks.py`: broken-file-reference, broken-anchor, missing-required-section, and modal-contradiction-heuristic checks, each returning a list of `Finding` dicts.
- Decision: the contradiction check is explicitly labeled a heuristic in its own finding message ("possible contradiction — needs manual review") rather than presented as a definitive result, since keyword-overlap between "Always X" / "Never Y" statements is a signal, not proof.

### [09:45 UTC] Build Phase — AI Review + Report Rendering

- `src/ai_review.py`: builds a Claude Messages API request (model `claude-haiku-4-5-20251001`, matching the lightweight-task convention used by prior builds in this repo), asks Claude to return a strict JSON array of findings, and asks it to specifically cross-check any factual/numeric claims in the instructions against the optional ground-truth file's actual content. Falls back to an empty finding list (with an `info`-level note) when `ANTHROPIC_API_KEY` is unset, and handles malformed/non-JSON model output as a single `warning` finding rather than crashing.
- `src/report.py`: text, JSON, and HTML renderers. HTML renderer uses `html.escape()` on every piece of user-controlled text (finding excerpts, messages) before interpolating into the template — verified by a dedicated XSS-regression test, following the same pattern Regex Dojo (2026-06-18) used for its `escHtml()` helper.
- Built `tests/fixtures/mini_claude_md.md` and `tests/fixtures/mini_index_md.md` — small fixtures that mirror tonight's real discovery (a stale "every score is ≤4" claim vs. a fixture "index" showing a 9) so the AI-review ground-truth-contradiction path has a realistic, reproducible test case. The mocked Claude response in that test is hand-written to reflect what a real semantic review of those two fixtures would plausibly return.

### [10:05 UTC] Tests Run

Tests: 38 passed, 0 failed. (Exceeded the 15-test minimum comfortably — full breakdown: 6 parser tests, 10 deterministic-check tests, 7 AI-review tests (all network calls mocked), 8 report-rendering tests, 7 CLI tests.)

### [10:15 UTC] Verify — Step 7

Ran the CLI manually against `tests/fixtures/broken/instructions.md` and `tests/fixtures/clean/instructions.md` in text, json, and html formats — confirmed exit codes (1 for broken + `--fail-on error`, 0 for clean), and that every seeded issue (2 broken file references, 1 broken anchor, 1 missing section, 1 modal contradiction) is flagged on the broken fixture with zero false positives on the clean one.

Also ran it read-only against this repo's real `CLAUDE.md` with `--ground-truth builds/index.md` (no writes to either file) as an honest real-world check, not just a curated fixture. Result: the deterministic checks work correctly, but surfaced a real limitation worth recording plainly rather than glossing over — several of `CLAUDE.md`'s bare-filename code-span mentions (`PRD.md`, `BUILD_LOG.md`, `WhyThis.md`, `Manual.md`, and the literal placeholder `builds/YYYY-MM-DD-title-slug/`) are generic per-build-folder template references, not paths meant to resolve from the repo root, so they render as false-positive `broken_file_reference` findings in this specific document. This is a known, documented trade-off of the inclusive path-detection heuristic (see FutureFeatures.md and Manual.md's Known Limitations) rather than a defect in the check logic itself — the check does exactly what it says (resolve referenced paths against a root) and the fixtures prove it's accurate when paths are meant to be root-relative. No `ANTHROPIC_API_KEY` is set in this container, so the AI-review path against the real CLAUDE.md/index.md pair could only be exercised through the mocked test (`test_ai_review_flags_ground_truth_contradiction`), not live — consistent with CLAUDE.md's own runtime-credentials rule.

HTML report opened and visually confirmed dark-mode, escaped excerpts (verified via `html.parser` parsing the output without error, plus the dedicated XSS-regression test), mobile-width layout.

Security checklist:
- No `.env` files
- No hardcoded credentials, API keys, or personal data (the `ANTHROPIC_API_KEY` is read from the environment only, never logged or written to any report)
- No `eval()`/`exec()` anywhere
- No `subprocess`/`os.system` calls
- No `innerHTML`-equivalent unescaped interpolation — all dynamic HTML text goes through `html.escape()`
- No file path traversal: `--root`/target/ground-truth paths come from CLI args the user explicitly supplies, resolved with `Path.resolve()`, never constructed from content inside the audited file itself
- All code self-contained in this build folder; no imports from another build's folder

### [10:25 UTC] Documentation

- `FutureFeatures.md`: 7 concrete suggestions.
- `Manual.md`: quick start, full CLI reference, Skill install instructions, configuration table, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.
