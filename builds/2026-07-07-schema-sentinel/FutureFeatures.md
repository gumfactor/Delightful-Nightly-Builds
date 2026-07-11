# Future Features — Schema Sentinel

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--config schema-sentinel.yml`** — let a project pin `ignore_fields` and a custom `fail_on` threshold in a checked-in config file instead of retyping CLI flags every run.
2. **Exit code for "no comparable revisions"** — `history` currently returns exit 0 when fewer than 2 revisions exist for a path; a `--require-history` flag could make that a hard failure for CI use, so a typo'd path doesn't silently report "all clear."
3. **Markdown output mode** (`--markdown out.md`) — the same report content as `--html` but as a GitHub-renderable Markdown table, for pasting directly into a PR description or commit message.

## Medium Effort (roughly one nightly build session)

4. **Rename-aware `history`** — the current implementation deliberately does not use `git log --follow`, so a file rename shows up as `removed` (old path) + a fresh, unrelated history start (new path) rather than a continuous timeline. Detecting renames via `git log --follow --name-status` and stitching the two paths' histories together would make the timeline continuous across a rename.
5. **Multi-file / directory mode** — `schema-sentinel diff old_dir/ new_dir/` comparing every matching filename between two directory snapshots in one run (useful for a Canada List export that ships as several related CSVs), with one consolidated report instead of running the tool once per file.
6. **`--baseline` cache mode** — save the last-seen schema for a named "contract" to a local `.schema-sentinel/` cache directory, so a single invocation (`schema-sentinel check data/export.json --contract canada-list-export`) compares against last time automatically instead of requiring the caller to keep the previous file around.

## Ambitious Extensions (multi-session effort)

7. **GitHub Actions composite action** — package the CLI as a reusable GitHub Action (`uses: ./schema-sentinel-action`) with `fail-on` wired to the workflow's pass/fail, so any of the user's repos can drop in schema-drift gating on a pull request without copying the script around.
8. **Configurable severity rules** — right now the breaking/risky/safe classification is hardcoded in `diff.py`. A `--rules custom_rules.yml` mode would let a project override individual rules (e.g. treat a new enum value as `breaking` instead of `risky` for a strict internal API), turning the tool into a general data-contract policy engine rather than one fixed opinion.
9. **OpenAPI / JSON Schema import-export** — infer a formal JSON Schema (or an OpenAPI response schema fragment) from a snapshot instead of (or alongside) the internal schema representation, so Schema Sentinel's inference step could also bootstrap documentation, not just detect drift.

---

## Possible Integration Points

- **The Canada List ingestion pipeline** (named directly in PROFILE.md as a recurring friction point) is the most direct real-world application: running `schema-sentinel diff` between the last-known-good scraped/exported dataset and each new ingestion run before it hits the pipeline would catch a source's silent field rename or type change before it propagates.
- **2026-07-05 TrialScope** and **2026-06-17 Qualtrics Survey Data Inspector** both ingest external CSV exports whose column layout is entirely outside the user's control (PsychoPy/jsPsych/Qualtrics vendor changes). Schema Sentinel could run as a pre-check ahead of either tool to flag when an export's shape has drifted from what those tools expect.
- **2026-06-19 dep-check** established the `--exit-on-outdated`-style CI gating pattern that `--fail-on` here deliberately mirrors; a future build could unify both into a single "pre-flight checks" GitHub Action that runs whichever of the two applies to a given repo.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| `history` mode does not follow file renames (`git log --follow` was deliberately not used — see BUILD_LOG) | Implement rename-aware history stitching (Future Feature #4) |
| Enum-candidate detection only considers string fields with ≤15 distinct values; a numeric or boolean-like categorical field (e.g. a small set of integer status codes) is never flagged as an enum | Extend `enum_candidate` detection to `int`/`bool` core types under the same cardinality rule |
| The AI migration summary could not be exercised against the real Anthropic API this session (`ANTHROPIC_API_KEY` was not set in the build environment) — only the mocked-HTTP path and the deterministic fallback were verified | Run one real invocation with `--ai-summary` once a key is available, to confirm the live prompt/response shape matches what the mocked tests assume |
| No support for comparing a JSON file against a CSV file (or JSONL against CSV) — both sides of a `diff` must currently share the same extension/format | Normalize both sides to the internal record-list representation before inference regardless of source format (already halfway there since `infer_schema` operates on plain records) |
