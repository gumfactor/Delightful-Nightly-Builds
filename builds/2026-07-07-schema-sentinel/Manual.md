# Manual — Schema Sentinel

> **Version:** 1.0 (built 2026-07-07)
> **Complexity:** Ambitious

---

## What This Is

Schema Sentinel is a command-line tool that catches breaking data-contract changes before
they silently break a pipeline. Point it at two versions of a JSON/JSONL/CSV file — or at
one file's entire git history — and it infers the structure of each version, diffs them
field by field, and classifies every change as **breaking** (removed field, incompatible
type change), **risky** (a required field became optional, a new category value appeared),
or **safe** (a new field, a widened type, a fewer-values enum). It is meant to run before
trusting a new export from any pipeline you don't fully control — a scraped dataset, a
Qualtrics export, a partner API response — against the last known-good version.

---

## Quick Start

1. `cd` into the build folder (or copy `src/` wherever you like — it has no dependencies).
2. Compare two files directly:
   ```
   python3 src/main.py diff old_export.json new_export.json
   ```
3. Or walk one tracked file's entire git history inside a repo:
   ```
   python3 src/main.py history data/export.csv --repo /path/to/repo
   ```
4. Add `--html report.html` any time you want a shareable, phone-readable report instead of
   (or alongside) the terminal output.
5. Add `--fail-on breaking` (the default) in a CI step so a pipeline stops before ingesting
   a breaking change.

---

## How to Use It

### `diff` — compare two snapshots directly

```
python3 src/main.py diff <old_file> <new_file> [options]
```

Both files can be `.json` (a single object or an array of objects), `.jsonl` (one JSON
object per line), or `.csv`. The two files don't need to be the same size — Schema Sentinel
compares their *inferred structure*, not their row-by-row content.

### `history` — walk one file's git log

```
python3 src/main.py history <path> [--repo .] [--limit N] [options]
```

`<path>` is the path to the tracked file **relative to the repository root** (the same
string you'd pass to `git log -- <path>`). `--repo` defaults to the current directory.
`--limit N` restricts the walk to the N most recent revisions (still shown oldest-first).
Every step between consecutive revisions is diffed and reported as one entry in the
timeline. This only ever runs read-only `git log`/`git show` commands — it never modifies
the repository, checks out a branch, or touches your working tree.

### Shared options (both subcommands)

| Flag | Effect |
|------|--------|
| `--ignore-fields a,b,c` | Comma-separated field paths (dotted for nested fields, e.g. `address.postal_code`) to exclude from the report — use for fields you know change often and don't care about. |
| `--json` | Print a machine-readable JSON report instead of the colored terminal report. |
| `--html PATH` | Also write a self-contained dark-mode HTML report to PATH — no network calls, opens correctly on a phone browser or straight from disk. |
| `--fail-on breaking\|risky` | Sets the process exit code: non-zero if any change at or above this severity is found. Default `breaking`. Use this in a CI step to gate a pipeline. |
| `--ai-summary` | Adds a short plain-English "what changed and what to check" paragraph. Uses the Anthropic API if `ANTHROPIC_API_KEY` is set; otherwise (or if the call fails for any reason) falls back to a deterministic summary built from the same diff data. Never crashes the run either way. |

### Reading the severity levels

- **breaking** — a field was removed, or its type changed incompatibly (e.g. `str` → `int`). Code reading this field will likely error or silently misbehave.
- **risky** — a required field became optional (code assuming it's always there may `KeyError`/`NoneType` error), or a categorical field gained a new value your code may not handle (e.g. a `switch`/`if-elif` chain with no `default`).
- **safe** — a field was added, an `int` field widened to `float`, an optional field became required, or a categorical field lost a value it no longer produces.

---

## Configuration

No configuration file is required — everything is a CLI flag.

| Setting | Default | Description |
|---------|---------|--------------|
| `--repo` | `.` (current directory) | Path to the git repository for `history` mode |
| `--limit` | unlimited | Restrict `history` to the N most recent revisions |
| `--fail-on` | `breaking` | Minimum severity that triggers a non-zero exit code |
| `ANTHROPIC_API_KEY` (env var) | unset | Enables the real AI summary when `--ai-summary` is passed; otherwise a deterministic template is used |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Error: 'X' is not a git repository` | `--repo` doesn't point at a git working tree | Pass the correct repo path, or `cd` into it and use `--repo .` |
| `Error: No git history found for '<path>'...` | The path is wrong, or the file was renamed at some point (see Known Limitations) | Confirm the exact path with `git log -- <path>` yourself; use the path as it exists at `HEAD` |
| `Error: Malformed JSON: ...` | The file isn't valid JSON, or is empty | Open the file and check it parses with `python3 -m json.tool <file>` |
| A field you don't care about clutters every report | It changes often but isn't meaningful | Add it to `--ignore-fields` |
| `--ai-summary` always returns the same templated-looking paragraph | `ANTHROPIC_API_KEY` isn't set (or the call failed) | This is the intended graceful fallback — it never blocks the run; set the env var for the live version |

---

## Known Limitations

- `history` mode does not follow file renames — a rename shows up as the old path's history simply stopping. See `FutureFeatures.md`.
- Enum-candidate detection only applies to string fields (≤15 distinct values across ≥2 records); a small set of numeric status codes is not currently flagged as an enum.
- The AI summary path was verified with a mocked HTTP layer only — this build session had no `ANTHROPIC_API_KEY` available to exercise a real call.
- `diff` requires both files to share the same extension/format (both `.json`, both `.csv`, etc.) — comparing a JSON export against a CSV export of the same data isn't supported yet.
