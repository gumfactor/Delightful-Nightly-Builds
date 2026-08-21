# Build Log — Secret Sweep

> **Date:** 2026-08-21
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [00:05 UTC] Session Start

- Checked Step 0: most recent dated build folder is `builds/2026-06-18-regex-dojo`, whose BUILD_LOG.md ends with "Build complete. Success criteria reviewed. All tests passing." — no resume needed. (The local `main` checkout is weeks behind the actual catalog; the true most-recent build per the open-PR resync is 2026-08-20-fairway-physics, also complete — nothing interrupted.)
- Read PROFILE.md, STANDARDS.md, and resynced `builds/index.md` from the head of the most recently created open PR branch (`claude/cool-sagan-w0k5dx`, PR #77, 2026-08-20) rather than the stale local copy — 106 prior build rows, last build date 2026-08-20.
- Today is 2026-08-21 (Friday), day-of-year 233. `category_index = (233 - 1) % 9 = 7` → **Category H — Developer Tool**.
- Read `builds/ideas.md`. Only one pending Category H row (#9, "GitHub Actions Performance Analyzer") — its description is a verbatim duplicate of the already-built `ci-pulse` (2026-06-28). Corrected its status to `skipped` with a note before running the lottery, which left the Category H pool empty → routed straight to fresh generation (Step 2d), consistent with the precedent set by Landing Pattern (2026-08-03) and Voiceprint (2026-07-28) for stale/duplicate backlog rows.
- Generated 3 fresh Category H candidates (full reasoning in `WhyThis.md`): a git-history secret/credential scanner across the user's own local repos, a Python dead-code/unreachable-symbol finder, and a type-hint coverage/drift auditor. Selected the secret scanner — none of the 8 prior Category H builds (dep-check, ci-pulse, Schema Sentinel, AgentLint, BugTrace, Landing Pattern, Snipvault) touch security/credential hygiene, and it is the build most likely to catch something the user would genuinely want to know about before it becomes a real incident, especially given how much of this user's code is written with AI assistance across many simultaneous repos.
- Appended the two non-winning ideas to `builds/ideas.md` as new pending rows (IDs 13-14).
- Build folder created: `builds/2026-08-21-secret-sweep/`

### [00:20 UTC] PRD Written

- Goal: a Python CLI that scans one or more local git repositories — both the current working tree and full commit history — for accidentally committed secrets and credentials, using pattern + entropy detection, then renders a redacted, actionable report.
- Scope: pattern library (12+ known credential formats) + generic high-entropy detector, working-tree scan, full-history scan via `git log -p`, SQLite-backed finding baseline with `ack` to suppress confirmed false positives across re-scans, severity ranking (still-live-in-HEAD vs. history-only), remediation guidance per finding, optional Claude Haiku second-opinion classifier that is only ever shown a redacted/masked context (never the raw secret), terminal/JSON/self-contained dark-mode HTML report output, companion Claude Code Skill for a fast on-demand working-tree-only scan mid-session.
- Notable constraints/decisions: no third-party dependency for git access — shell out to the user's own `git` binary via `subprocess.run` with argument lists only (never `shell=True`, never string-interpolated user input); every finding value is redacted (first 4 / last 4 chars only) both in the SQLite store and in every report format, and only a SHA-256 hash of the raw match is stored for re-scan dedup, so the tool never persists or transmits a usable copy of the secret it just found.

### [01:10 UTC] Build Phase

Implemented in dependency order: `src/patterns.py` (pattern library + entropy scorer + allowlist), `src/redact.py` (masking + hashing, written and unit-tested first since every other module depends on it never leaking a raw value), `src/git_ops.py` (subprocess wrappers for tree listing, `git log -p`, per-commit file content — all argument-list `subprocess.run`, `-C <repo>` scoping, no shell), `src/scanner.py` (core detection over working-tree files and history diffs, dedup/merge logic), `src/db.py` (SQLite schema + CRUD + ack workflow), `src/ai_review.py` (optional Claude Haiku call via `urllib.request` — request payload built and asserted to contain no raw secret substring in tests — with an unconditional deterministic fallback), `src/report.py` (terminal/JSON/HTML renderers, HTML built with a JSON-in-`<script>`-tag payload plus `textContent`/`createElement` rendering, no `innerHTML` from scanned repo content), `secretsweep.py` (CLI entry point: `scan`, `history`, `report`, `ack`, `list`), and `skill/SKILL.md` (companion Claude Code Skill wrapping the fast working-tree-only path).

Obstacles: `git log -p` output needed careful parsing to attribute an added line to the correct file path and commit (tracking the current `commit <sha>`, `+++ b/...`, and `@@ -a,b +c,d @@` headers per hunk) without pulling in a diff-parsing dependency — implemented a small stateful line-scanner instead of a full patch parser, since only added (`+`-prefixed) lines within a hunk are ever relevant to secret detection. Also had to escape `<` to `<` in the HTML report's embedded JSON payload before writing it into the `<script>` tag — `<script>` content is HTML raw text and is never entity-decoded, so a scanned file path or masked context containing a literal `</script>` substring would otherwise terminate the tag early (the same class of bug the 2026-08-06 Manuscript Pipeline build hit and fixed); added a dedicated regression test (`test_render_html_escapes_script_injection_in_file_path`) before relying on it.

A first full test run caught one real detection bug: a single AWS-shaped key assigned to a variable literally named `AWS_KEY` was being reported *twice* — once by the named "AWS Access Key ID" pattern and again by the generic high-entropy detector, since the variable name matches `key` and the value is genuinely high-entropy. Fixed in `src/scanner.py::_matches_for_line` by collecting the set of values already caught by a named pattern first and excluding those from the generic pass, with a regression test (`test_working_tree_scan_finds_secret_in_tracked_file` asserting exactly one finding, not two).

### [01:45 UTC] Tests Run

Tests: 47 passed, 0 failed.

### [01:55 UTC] Verify — Step 7

Checked all 5 PRD success criteria against the actual behavior and manually verified end-to-end against a real (non-mocked) fixture git repo, not just the pytest suite: committed an AWS-shaped key and a Stripe live publishable key, then a second commit that removed the AWS key from `config.py` but left the Stripe key in place. `scan` correctly reported only the still-present Stripe key as `critical`; `history` correctly reported the Stripe key as `critical` (still at HEAD) and the AWS key as `high` (history-only, correct commit SHA and line number), and the rendered HTML report contained zero occurrences of the raw AWS key string (`grep -c` returned 0). Ran the STANDARDS.md security checklist against every file in this build folder: no `.env` files, no hardcoded credential values (the pattern library contains detection *regexes*, never real key material — verified by grep), no `eval()`/`exec()`, no `innerHTML` from scanned content, no `subprocess`/`os.system` call built from a concatenated/interpolated string or `shell=True`, no file-path traversal on user-supplied repo paths beyond what `git -C` itself scopes, no reads from paths outside the build's own folder except the user-supplied repo paths that are the explicit point of the tool (same precedent as Waymark/BugTrace/Landing Pattern). All criteria met.

### [02:00 UTC] Docs

- FutureFeatures.md: 7 concrete suggestions.
- Manual.md: quick start, all 5 CLI commands documented, Skill usage, configuration table, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.
