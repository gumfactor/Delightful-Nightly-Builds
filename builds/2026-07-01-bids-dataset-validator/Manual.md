# Manual — BIDS Dataset Organizer & Validator

## What it does

Points at a directory of neuroimaging scan data and checks it against the
core BIDS (Brain Imaging Data Structure) naming rules: consistent entity
ordering, required `.json` sidecars, required `events.tsv` files for task
runs, a valid `dataset_description.json`, consistent subject/session/run
zero-padding, no duplicate files, and consistent session structure across
subjects. It never reads scan content — only filenames and the existence
(not the content) of a few required companion files.

## Setup

```bash
cd builds/2026-07-01-bids-dataset-validator
pip install -r requirements.txt   # only needed for --ai-summary
```

`pytest` is required to run the test suite; if it isn't on your machine,
`pip install pytest`.

## Running it

```bash
python -m src.main /path/to/your/dataset
```

Add flags as needed:

```bash
# Write a JSON and an HTML report alongside the terminal output
python -m src.main /path/to/dataset --json-report report.json --html-report report.html

# Actually apply the safe zero-padding fixes (default is dry-run/report-only)
python -m src.main /path/to/dataset --apply

# Get a Claude-generated, prioritized, plain-English fix list
# (requires ANTHROPIC_API_KEY in your environment)
python -m src.main /path/to/dataset --ai-summary
```

Exit code is `0` if there are no error-level findings, `1` if there are
(useful for CI/pipeline gating — run this before handing a dataset to
fMRIPrep or MRIQC).

## What gets checked

| Rule | Severity | What it catches |
|---|---|---|
| `MALFORMED_ENTITY` | error | An entity segment with no `key-value` dash |
| `INVALID_ENTITY_VALUE` | error | An entity value that isn't plain alphanumeric |
| `MISSING_SUB_ENTITY` | error | Filename has no `sub-` entity at all |
| `BAD_ENTITY_ORDER` | error | Entities out of canonical order (sub, ses, task, acq, run, echo) |
| `UNRECOGNIZED_ENTITY` | warning | An entity key outside the core set this tool understands |
| `UNRECOGNIZED_SUFFIX` | warning | A suffix outside T1w/T2w/bold/sbref/dwi/physio/events/fieldmap suffixes |
| `MISSING_DATASET_DESCRIPTION` | error | No `dataset_description.json` at the dataset root |
| `MISSING_DATASET_DESCRIPTION_FIELD` | error | Missing `Name` or `BIDSVersion` |
| `MISSING_SIDECAR` | warning | A data file (T1w/T2w/bold/dwi/etc.) has no matching `.json` |
| `MISSING_EVENTS` | warning | A non-resting-state `bold` run has no matching `events.tsv` |
| `DUPLICATE_FILE` | error | Two files resolve to the same entities + suffix + extension |
| `INCONSISTENT_PADDING` | warning | Subject/session/run numbers aren't zero-padded consistently |
| `INCONSISTENT_SESSION_STRUCTURE` | warning | Some subjects use `ses-` and others don't |

## What `--apply` does (and doesn't do)

`--apply` only renames files to fix zero-padding — e.g. `sub-1` → `sub-01`
to match the dataset's dominant width. It:
- Never touches directory names, only filenames
- Never overwrites an existing file at the target path (skips instead)
- Verifies the target path resolves inside the dataset root before every
  rename
- Is a no-op by default — you must pass `--apply` explicitly; otherwise
  the report just lists what it *would* do

## Scope

This tool covers the entities and suffixes a typical anatomical/task-fMRI
dataset uses. It is **not** a full BIDS-validator replacement — MEG/EEG/
iEEG-specific entities, derivatives datasets, BEP extensions, fieldmap
`IntendedFor` linking, and `.tsv` column-schema validation are out of
scope (see `PRD.md` and `FutureFeatures.md`).

## Running the tests

```bash
python -m pytest tests/ -v
```

50 tests, all using synthetic placeholder files in `tmp_path` — no real
scan data is read or required.
