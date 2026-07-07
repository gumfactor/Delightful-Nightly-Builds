# PRD — Schema Sentinel

> **Build date:** 2026-07-07
> **Category:** H — Developer Tool
> **Complexity:** Ambitious
> **Day of week:** Tuesday

---

## Goal

Detect and classify structural drift between two versions of a JSON/JSONL/CSV data file — or across a tracked file's entire git history — so a breaking change to a data contract (a renamed field, a type flip, a removed enum value) is caught before it silently breaks a downstream pipeline.

## User Story

As a researcher and solo founder who runs multiple data pipelines (Canada List ingestion exports, Qualtrics/lab data exports, API responses from tools built in prior nightly sessions) and has explicitly named "keeping multiple data systems synchronized" as a recurring friction point, I want to compare two snapshots of a data file — or walk a tracked file's full git history — and get a clear, severity-ranked list of exactly what changed structurally, so that I can catch a breaking schema change before it corrupts a downstream pipeline instead of discovering it from a crash or bad data days later.

## Scope

### In Scope
- **Schema inference** (`src/infer.py`) from a single JSON file (object or array-of-objects), JSONL file, or CSV file:
  - Per-field observed type set (`null`, `bool`, `int`, `float`, `str`, `list`, `dict`, or `mixed` when more than one non-null type is observed)
  - Presence rate (fraction of records containing the field) and a `required` flag (present in 100% of records)
  - Enum-candidate detection for string fields: flagged when the field has at most 15 distinct values across at least 2 records, with the observed value set recorded
  - Recursive nested-schema inference for `dict` fields and for `list` fields whose items are objects (dotted path naming, e.g. `address.postal_code`)
  - CSV type coercion: each string cell is heuristically parsed as `null` (empty string), `bool`, `int`, or `float` before falling back to `str`, then types are inferred the same way as JSON
- **Schema diff engine** (`src/diff.py`) comparing an old schema to a new schema, producing one entry per change:
  - `added` field, `removed` field
  - `type_changed` (old type set → new type set)
  - `presence_changed` (required → optional, or optional → required)
  - `enum_changed` (value added to / removed from an enum-candidate field)
  - Nested changes recurse and report the full dotted field path
- **Severity classification**, applied deterministically per change type:
  - `breaking`: field removed; type changed to an incompatible type (e.g. `str`→`int`, `dict`→`list`); a nested object's structure disappears
  - `risky`: required field became optional; a new enum value appears (existing switch/case-style consumer code may not handle it)
  - `safe`: field added; `int`→`float` widening; optional field became required; an enum value was removed
  - Overall result severity = the highest severity among all entries (`breaking` > `risky` > `safe` > none)
- **CLI subcommands** (`src/cli.py`, argparse-based):
  - `schema-sentinel diff <old_file> <new_file> [--ignore-fields a,b] [--json] [--html out.html] [--fail-on breaking|risky] [--ai-summary]`
  - `schema-sentinel history <path> [--repo .] [--limit N] [--ignore-fields a,b] [--json] [--html out.html] [--fail-on breaking|risky] [--ai-summary]` — walks `git log --follow` for `path` inside `--repo` (read-only `git log`/`git show` via `subprocess.run` argument lists, never a shell), reconstructs each revision's content, infers a schema per revision, and diffs every consecutive pair to build a drift timeline
- **Output formats**: colored terminal report (default), `--json` machine-readable report, `--html` self-contained dark-mode HTML report (inline CSS only, no CDN, works on a phone browser)
- **CI gating**: `--fail-on breaking` (default) or `--fail-on risky` sets the process exit code non-zero when a change at or above that severity is found — same pattern as the 2026-06-19 dep-check build's `--exit-on-outdated`
- **Optional AI migration summary** (`src/ai_summary.py`): when `ANTHROPIC_API_KEY` is set and `--ai-summary` is passed, calls the Anthropic Messages API directly via `urllib.request` (no SDK dependency) with only the computed diff entries (field names, change types, severities — never actual record data or file contents) to generate a short plain-English "what changed and what to check" paragraph. Falls back to a deterministic bullet-list template (grouped by severity) when no key is set or the call fails for any reason. Never crashes the run.
- **`--ignore-fields`**: comma-separated list of field paths to exclude from a report, for known-volatile fields (e.g. `last_synced_at`)

### Out of Scope
- XML, Avro, Protobuf, or any binary schema formats — JSON/JSONL/CSV only
- Automatic codemod/patch generation — the tool reports and classifies changes; it does not rewrite consumer code
- A persistent database or daemon/watch mode — the tool is invoked on demand, exactly like `dep-check` and `ci-pulse`
- Any operation that mutates the target git repository — `history` mode is strictly read-only (`git log`, `git show`)
- A packaged Anthropic SDK dependency — the optional AI call uses stdlib `urllib.request` only, so the tool has zero third-party runtime dependencies

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None (argparse for the CLI)
- **Dependencies:** stdlib only (`json`, `csv`, `argparse`, `subprocess`, `urllib.request`, `dataclasses`, `html`) — no `requirements.txt` entries needed at runtime; pytest only for the test environment
- **Runtime requirement:** `python3 src/main.py diff old.json new.json` or `python3 src/main.py history data/export.csv` — no install step, no network access required for core functionality

## Data Structure

**Schema representation** (the output of `infer.py`), a plain dict:
```python
{
  "field.path": {
    "types": {"str", "int"},       # observed type names; {"str"} if consistent
    "required": True,               # present in 100% of records
    "presence_rate": 1.0,
    "enum_candidate": True,         # only set for low-cardinality string fields
    "enum_values": {"active", "cancelled"},   # only present if enum_candidate
    "children": { ... }              # nested schema dict, only for dict/list-of-dict fields
  },
  ...
}
```

**Diff entry** (the output of `diff.py`), one per detected change:
```python
{
  "field": "address.postal_code",
  "change": "type_changed",          # added | removed | type_changed | presence_changed | enum_changed
  "severity": "breaking",            # breaking | risky | safe
  "old": "str",
  "new": "int",
  "detail": "type changed from str to int"
}
```

**History timeline entry** (the output of `git_history.py` + `diff.py` combined): one entry per consecutive pair of revisions, each carrying the commit SHA (short), commit date, and the list of diff entries between that revision and the previous one.

The tool reads files the user points it at (any path given as a CLI argument) — this is the same operating model as the existing `dep-check` and `TrialScope` builds, which read arbitrary `requirements.txt` / CSV paths supplied by the user. It writes nothing except the optional `--html`/report file the user explicitly names. `history` mode never writes to the target git repository.

## Folder Structure

```
builds/2026-07-07-schema-sentinel/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt        (empty — stdlib only, documented as such)
├── src/
│   ├── __init__.py
│   ├── infer.py            (schema inference: JSON/JSONL/CSV → schema dict)
│   ├── diff.py             (schema diff engine + severity classification)
│   ├── git_history.py      (read-only git log/show wrapper)
│   ├── report_html.py      (self-contained dark-mode HTML report renderer)
│   ├── ai_summary.py       (optional Anthropic call + deterministic fallback)
│   ├── cli.py              (argparse entrypoint: diff, history subcommands)
│   └── main.py             (if __name__ == "__main__" entry point)
└── tests/
    ├── test_infer_json.py
    ├── test_infer_csv.py
    ├── test_infer_nested.py
    ├── test_diff.py
    ├── test_severity.py
    ├── test_git_history.py
    ├── test_report_html.py
    ├── test_ai_summary.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Type inference for every scalar type, `null`, `mixed`, and nested `dict`/`list` fields, from both JSON and CSV sources
  - Presence-rate and `required` calculation across records with inconsistent keys
  - Enum-candidate detection (cardinality threshold, both sides of the boundary)
  - Diff engine: `added`, `removed`, `type_changed` (both compatible and incompatible directions), `presence_changed` (both directions), `enum_changed` (both directions), nested-field diffs, and the no-change case
  - Severity classification matrix for every change type, plus `--ignore-fields` suppression
  - `git_history`: builds a real temporary git repo (via `tmp_path` + `subprocess`) with multiple commits touching a tracked file, and verifies the revision list, ordering, and per-revision content extraction — fully local, no network
  - HTML report: valid self-contained output (no external `<script src=` / `<link href=` to a CDN), correct severity counts rendered
  - AI summary: the Anthropic HTTP call is fully mocked (`unittest.mock.patch` on `urllib.request.urlopen`); a separate test asserts the deterministic fallback path when no API key is set and when the mocked call raises
  - CLI: `diff` and `history` subcommands end-to-end via `subprocess`, including `--json`, `--fail-on` exit-code gating, and `--ignore-fields`
  - Error handling: malformed JSON, empty file, and a git path that was never tracked all fail with a clear message rather than a traceback

## Success Criteria

1. All tests pass (zero failures)
2. `schema-sentinel diff` correctly identifies and severity-classifies every change type listed above between two hand-crafted JSON fixtures
3. `schema-sentinel history` correctly reconstructs a multi-commit drift timeline from a real (test-created) git repository, using only read-only git operations
4. `--fail-on breaking` exits non-zero exactly when a `breaking`-severity change is present, and 0 otherwise (verified for both outcomes)
5. The `--html` report renders as a single self-contained file with zero external network dependencies, and the optional AI summary path never crashes the run when no API key is available (falls back to the deterministic template)

---

## Scope Changes

- `history` mode uses plain `git log -- <path>` rather than `git log --follow`. `--follow`
  detects renames for the *log listing*, but `git show <sha>:<path>` still requires the
  path exactly as it existed at that revision — using `--follow` without also resolving the
  path-per-revision would produce a listing that silently fails on `git show` for any commit
  before a rename. Rather than ship that half-correct behavior, tracking a renamed file
  across its full history is deferred to `FutureFeatures.md` and documented as a known
  limitation in `Manual.md`. Everything else shipped as planned; no `--repo` remote-clone
  support was ever in scope — `history` mode only operates on a local git working tree
  already present on disk.
