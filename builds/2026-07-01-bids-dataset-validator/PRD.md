# PRD — BIDS Dataset Organizer & Validator

## Goal

Give a neuroimaging lab a fast, local, zero-dependency-on-the-cloud way to catch BIDS
(Brain Imaging Data Structure) naming and structure violations in a scan dataset before
they break a downstream pipeline (fMRIPrep, MRIQC, etc.), and to safely auto-fix the
subset of violations that can be corrected unambiguously.

## User Story

As a neuroscience lab director who manages raw fMRI/anatomical data acquired by
research assistants with inconsistent naming habits, I want to point a tool at a
dataset folder and get a clear report of every BIDS violation (missing sidecars,
missing `dataset_description.json`, inconsistent zero-padding, duplicate files,
unrecognized entities) so I can fix the dataset before running it through analysis
software, instead of discovering the problem when the pipeline crashes hours in.

## Scope

### In Scope
- Recursive scan of a target dataset directory (any path the user provides)
- Parsing of core BIDS filename entities: `sub`, `ses`, `task`, `acq`, `run`, `echo`
- Supported suffixes: `T1w`, `T2w`, `bold`, `sbref`, `dwi`, `physio`, `events` (`.tsv`),
  and fieldmap suffixes `magnitude1`, `magnitude2`, `phasediff`, `epi`
- Validation rules:
  1. Filename matches the `key-value` entity grammar in the correct order
  2. `dataset_description.json` exists at the dataset root with `Name` and `BIDSVersion`
  3. Every `bold`/`T1w`/`T2w`/`dwi`/fieldmap data file has a matching `.json` sidecar
  4. Every non-resting-state `bold` run has a matching `events.tsv`
  5. Subject/session/run index zero-padding is consistent across the dataset
  6. No two files resolve to the same entity set + suffix (duplicate detection)
  7. Session labels present for some subjects but not others are flagged (inconsistent
     session structure)
- Reports: terminal text summary, self-contained HTML report (dark mode, mobile
  responsive), and machine-readable JSON report
- `--apply` mode: safely renames files to fix zero-padding inconsistencies only
  (never overwrites an existing target, never touches ambiguous cases, dry-run is the
  default)
- `--ai-summary` (optional, requires `ANTHROPIC_API_KEY`, already available in the
  build environment): sends the *structural* findings (issue types, counts, anonymized
  BIDS entity labels — never scan content) to Claude Haiku to produce a prioritized,
  plain-English action list

### Out of Scope
- Full BIDS-validator spec parity (MEG/EEG/iEEG entities, derivatives, BEP extensions,
  fieldmap `IntendedFor` linking, `.tsv` column-level schema validation)
- Reading or interpreting actual scan/voxel data — the tool only ever looks at file
  *names* and the *keys* of sidecar JSON files it needs to check existence of, never
  scan content
- Any network calls except the optional, explicit `--ai-summary` call to Anthropic

## Tech Stack

- Python 3.11, stdlib only for the core validator (`pathlib`, `json`, `re`, `argparse`)
- `anthropic` Python package for the optional AI summary layer
- `pytest` for tests

## Data Structure

Internal representation per scanned file: `ParsedFile` dataclass —
`path` (relative to dataset root), `entities` (ordered dict of BIDS key/value pairs),
`suffix`, `extension`, `is_recognized` (bool).

Findings are a list of `Finding` dataclasses — `severity` (`error`/`warning`),
`code` (short machine key, e.g. `MISSING_SIDECAR`), `message`, `path` (optional).

Reports (JSON) are a dict: `{dataset_path, scanned_at_files: int, subjects: int,
findings: [...], summary: {errors, warnings}}`.

## Folder Structure

```
builds/2026-07-01-bids-dataset-validator/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── bids_rules.py      # filename parsing + rule checks
│   ├── scanner.py         # directory walk -> ParsedFile list
│   ├── report.py          # text / HTML / JSON report rendering
│   ├── fixer.py           # --apply safe rename logic
│   ├── ai_summary.py      # optional Claude Haiku summary
│   └── main.py            # CLI entry point
└── tests/
    ├── test_bids_rules.py
    ├── test_scanner.py
    ├── test_report.py
    ├── test_fixer.py
    ├── test_ai_summary.py
    └── test_cli.py
```

## Testing Strategy

All tests use synthetic, empty placeholder files created in `tmp_path` pytest
fixtures — no real scan data exists or is needed, since every rule operates on
filenames and JSON sidecar existence, never file content.

- **Parsing**: valid BIDS filenames parse to the correct entity dict; invalid ones
  (missing `sub-` prefix, out-of-order entities, unrecognized suffix) are flagged
- **Rule checks**: missing sidecar, missing `dataset_description.json`, missing
  `events.tsv` for non-rest task runs (and correctly *not* required for rest runs),
  inconsistent zero-padding, duplicate entity sets, inconsistent session structure
- **Happy path**: a fully valid minimal dataset produces zero error-level findings
- **Fixer**: `--apply` renames a padding mismatch correctly; refuses to overwrite an
  existing target; dry-run (no `--apply`) never touches the filesystem
- **Security**: entity values containing path-traversal sequences (`../`) are
  rejected before any path is constructed; HTML report escapes filenames so a
  filename containing `<script>` cannot inject markup
- **AI summary**: the Anthropic client is injected/mocked — no real network call
  happens in the test suite; the function is a graceful no-op when the flag is
  omitted or the API key is absent
- **CLI**: argument parsing defaults, missing/nonexistent dataset path handled with
  a clear error instead of a stack trace, JSON/HTML report files are written with
  expected structure

Run: `python -m pytest tests/ -v` (target: 15+ tests, all passing)

## Success Criteria

1. A synthetic dataset with known, deliberately-planted violations (missing sidecar,
   missing `dataset_description.json`, inconsistent padding, duplicate file, missing
   `events.tsv`) is scanned and every planted violation appears in the findings list
   with the correct `code`
2. A fully valid minimal synthetic dataset produces zero `error`-severity findings
3. `--apply` corrects a zero-padding mismatch on disk and a re-scan of the fixed
   dataset no longer reports that finding, while never overwriting or deleting an
   existing file
4. Text, HTML, and JSON reports are all generated successfully and the HTML report
   is safe against a maliciously-named file (no unescaped HTML injection)
5. All tests in `tests/` pass (`python -m pytest tests/ -v`) with zero failures
