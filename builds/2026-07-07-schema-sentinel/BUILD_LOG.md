# Build Log — Schema Sentinel

> **Date:** 2026-07-07
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:14 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked `builds/` for an interrupted session. The most recent dated folder
  (`2026-06-18-regex-dojo`) ends with `Build complete. Success criteria reviewed. All
  tests passing.` — nothing to resume.
- Synced `builds/index.md` from the most recent open PR branch (`claude/cool-sagan-qc8qor`,
  PR #31, 2026-07-06 Synapse Sort) rather than the `main` copy, which is 11 builds behind.
- Day of year for 2026-07-07 is 188. `category_index = (188-1) % 9 = 7` → **Category H —
  Developer Tool**.
- Ran the lottery: the only `pending` H-category backlog row (#9, "GitHub Actions
  Performance Analyzer") is a near-duplicate of the already-shipped 2026-06-28 ci-pulse
  build. `R` (rated pending entries) = 0, so `lottery_chance = 25%`. Rolled 81 → fresh-idea
  path.
- **Environment check before ideating:** confirmed via WebFetch that this session's egress
  proxy returns HTTP 403 for Open-Meteo and even unauthenticated `api.github.com` — direct
  `curl` calls from Bash are denied outright by the permission layer. `ANTHROPIC_API_KEY`
  is not set in this environment (only `ANTHROPIC_BASE_URL`); `GITHUB_TOKEN` is set and
  works, but only through the GitHub MCP server, not raw HTTP. This matches the pattern
  logged in every build session since 2026-07-02 (PubMed Research Radar onward). Given
  this, and given the topic-diversity check below, I prioritized an idea that needs **zero
  network access** to build and fully test tonight, with any AI/network layer strictly
  optional and gracefully degrading — a now-established pattern in this repo.
- Topic diversity check (last 10 builds, 06-26 through 07-05): GitHub API appears in 4 of
  10 (06-26, 06-28, 06-29, 06-30) — saturated. Research-methods/psychology framing appears
  in 3 of 10 (06-27, 07-04, 07-05). Both avoided for tonight.
- Decided to build: **Schema Sentinel** — a local, git-aware CLI that infers structural
  schemas from JSON/JSONL/CSV files, diffs two snapshots (or an entire git history of one
  file) field-by-field, and classifies each change as `breaking` / `risky` / `safe` using
  explicit rules, with an optional Claude-generated migration summary.
- Build folder created: `builds/2026-07-07-schema-sentinel/`

### [08:14 UTC] PRD Written

- Goal: detect and classify structural drift between two versions of a JSON/JSONL/CSV data
  file (or across a file's entire git history), so a breaking change to a data contract is
  caught before it silently breaks a downstream pipeline.
- Scope: schema inference (types, presence, enum candidates, nested objects), a diff engine
  with breaking/risky/safe severity rules, `diff` and `history` (git log-based) CLI
  subcommands, colored terminal + JSON + self-contained dark-mode HTML output, `--fail-on`
  CI gating, optional Claude-Haiku migration-summary paragraph with a deterministic
  fallback template.
- Notable constraints/decisions: stdlib-only Python (no `pip install` dependency risk); all
  git operations are read-only (`git log`, `git show` via `subprocess.run` with argument
  lists, never `shell=True`); the optional Anthropic call uses `urllib.request` directly
  (no SDK) and is fully mocked in tests since no API key is available this session.

### [08:14 UTC] Build Phase

Implemented, in order: `src/infer.py` (schema inference from JSON/JSONL/CSV, with CSV
type coercion and recursive nested/list-of-dict inference), `src/diff.py` (schema diff +
breaking/risky/safe severity classification), `src/git_history.py` (read-only
`git log`/`git show` wrapper via `subprocess.run` argument lists — no `shell=True`
anywhere), `src/report_html.py` (self-contained dark-mode HTML report, all dynamic values
`html.escape`d since field names/enum values come from untrusted input files),
`src/ai_summary.py` (optional Anthropic call via `urllib.request`, deterministic
fallback), `src/cli.py` (argparse `diff`/`history` subcommands), and `src/main.py`.

Confirmed `pytest` is unavailable via `python3 -m pytest` in this sandbox
(`ModuleNotFoundError`) and `pip install` is denied by the permission layer — but a
`uv tool`-installed `pytest` binary already exists on `PATH` at `/root/.local/bin/pytest`,
so the bare `pytest` command works. Documented `pytest` (bare command, not `python3 -m
pytest`) as the run command in `Manual.md`/PRD, matching what actually works here rather
than the table's literal suggestion — this is a sandbox-environment fact, not a project
decision, and the invocation is still exactly "pytest tests/ -v" per the standard.

Deliberately did **not** implement `git log --follow` for rename tracking (see PRD "Scope
Changes" for the reasoning) — logged as a documented, honest limitation rather than shipped
half-working.

### [08:24 UTC] Tests Run

Tests: 73 passed, 0 failed. (`pytest tests/ -v`, run from the build folder.)

### [08:26 UTC] Manual Smoke Test

Ran the built CLI directly (outside pytest) against hand-written fixtures in the scratch
directory to confirm real end-to-end behavior, not just mocked test paths:
- `diff` correctly classified a removed field (breaking), an `int`→`str` type change
  (breaking), a new field (safe), a new enum value (risky), and a removed enum value
  (safe) in one run against realistic JSON fixtures; exit code was 1 as expected.
- The `--html` report rendered as a single self-contained file (2238 bytes) with the dark
  background color present and zero `<script src=` references.
- `history` against a real two-commit local git repo correctly detected the single
  `status` field addition between commits and exited 0 (no breaking change).

Security checklist run against `src/` and `tests/` (excluding compiled `__pycache__`,
since deleted): no hardcoded credentials/secrets, no `eval`/`exec`, no `os.system` or
`shell=True`, no `innerHTML` (not applicable — no HTML is user-supplied, only escaped
data is interpolated into the report template). `__pycache__`/`.pytest_cache` directories
removed from the build folder before committing.

### [08:27 UTC] Documentation

- `FutureFeatures.md`: 9 concrete suggestions across quick/medium/ambitious tiers, plus
  integration points naming specific prior builds (TrialScope, Qualtrics Survey Data
  Inspector, dep-check) and 4 known limitations.
- `Manual.md`: quick start, full flag reference, severity-level explanation, troubleshooting
  table, known limitations.

### [08:27 UTC] Verify — Step 7 Success Criteria Check

1. ✓ All tests pass (zero failures) — 73/73, confirmed above.
2. ✓ `diff` correctly identifies and severity-classifies every change type (added, removed,
   type_changed compatible/incompatible, presence_changed both directions, enum_changed
   both directions, nested-structure removal) — covered by `tests/test_diff.py` (11 tests)
   and confirmed live in the manual smoke test.
3. ✓ `history` correctly reconstructs a multi-commit drift timeline from a real
   (test-created) git repository using only read-only git operations — covered by
   `tests/test_git_history.py` and `tests/test_cli.py::test_history_end_to_end_json_output`,
   and confirmed live against a real two-commit repo in the manual smoke test.
4. ✓ `--fail-on breaking` (default) and `--fail-on risky` exit non-zero exactly when a
   change at or above that severity is present, 0 otherwise — both outcomes verified in
   `tests/test_cli.py::test_diff_fail_on_risky_catches_risky_only_change`.
5. ✓ The `--html` report is a single self-contained file with zero external network
   references (`tests/test_report_html.py::test_render_html_has_no_external_resources`,
   confirmed live in the smoke test), and the AI summary path never crashes when no API
   key is present (`ANTHROPIC_API_KEY` was in fact absent all session — the deterministic
   fallback is the path that actually ran, not just a mocked test scenario).

Build complete. Success criteria reviewed. All tests passing.
