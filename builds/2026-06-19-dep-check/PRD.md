# PRD — dep-check: Python Dependency Auditor

## Goal

A Python CLI that scans a project's `requirements.txt` (and optionally `setup.cfg` / `Pipfile`) for pinned package versions, queries the PyPI JSON API for the current latest release and yanked status, and produces a coloured terminal report or a self-contained HTML dashboard showing which packages need updates.

---

## User Story

As a Python developer managing multiple projects, I run `dep-check` in any project directory and immediately see which of my pinned dependencies are behind — without opening a browser, without pip freeze gymnastics, and without losing context by clicking through pypi.org one package at a time. The exit-code contract (`1` when outdated packages exist) makes it usable in CI as a gate.

---

## Scope

### In scope
- Parse `requirements.txt` (PEP 508 subset: `name==version`, `name>=version`, extras, inline comments, environment markers)
- Parse `setup.cfg` `install_requires` section
- Parse `Pipfile` `[packages]` section
- Query PyPI JSON API (`https://pypi.org/pypi/{package}/json`) for latest version and per-version yanked status
- Version comparison: pinned vs latest → classified as `up-to-date`, `patch`, `minor`, `major`, or `unpinned`
- Yanked detection: is the pinned version yanked on PyPI?
- Release age: how many days since the pinned version was released
- Terminal output: coloured table (ANSI), summary line, exit code
- HTML output: self-contained report with dark-theme table, summary stats, status badges
- `--format text|html` flag
- `--output FILE` to write HTML to a file
- `--exit-on-outdated` flag (exit 1 if any non-uptodate packages exist)
- Graceful degradation: packages not on PyPI or with connection errors logged as `unknown`

### Out of scope
- `pyproject.toml` parsing (stdlib has `tomllib` only from 3.11; deferring to FutureFeatures)
- Security vulnerability scanning (separate concern; CVE APIs require registration)
- Auto-upgrading packages
- Transitive dependency resolution
- License scanning

---

## Tech Stack

- Python 3.8+ (stdlib only at runtime: `urllib.request`, `json`, `re`, `datetime`, `html`, `argparse`, `pathlib`, `configparser`)
- `pytest` for tests (dev dependency only)
- No external runtime dependencies

---

## Data Structures

```python
@dataclass
class Requirement:
    name: str                    # normalised (lowercase, hyphens)
    pinned_version: str | None   # exact version string or None
    specifier: str | None        # full specifier, e.g. ">=2.28.0"
    source_file: str             # which file this came from

@dataclass
class PackageResult:
    req: Requirement
    latest_version: str | None
    pinned_upload_date: str | None   # ISO date of pinned release
    days_since_pinned: int | None
    status: str                  # "up-to-date" | "patch" | "minor" | "major" | "unpinned" | "unknown" | "error"
    yanked: bool
    yanked_reason: str | None

@dataclass
class Summary:
    total: int
    up_to_date: int
    patch: int
    minor: int
    major: int
    unpinned: int
    yanked: int
    unknown: int
```

---

## Folder Structure

```
builds/2026-06-19-dep-check/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt          ← empty (stdlib only)
├── main.py                   ← CLI entry point
├── src/
│   ├── __init__.py
│   ├── models.py             ← Requirement, PackageResult, Summary dataclasses
│   ├── parser.py             ← parse_requirements_txt, parse_setup_cfg, parse_pipfile
│   ├── pypi.py               ← fetch_package_info (PyPI JSON API)
│   ├── analyzer.py           ← compare_versions, classify_staleness, compute_summary
│   └── report.py             ← render_terminal, render_html
└── tests/
    ├── test_parser.py        ← 14 tests
    ├── test_analyzer.py      ← 14 tests
    └── test_report.py        ← 10 tests
```

---

## Testing Strategy

All business logic lives in pure functions (no I/O side effects), so every test runs without network access or filesystem setup beyond string inputs.

- `test_parser.py` — covers `parse_requirements_txt`: simple pins, loose specifiers, extras, inline comments, blank lines, environment markers, git-URL entries (skipped), empty input, duplicates, `parse_setup_cfg`, `parse_pipfile`
- `test_analyzer.py` — covers `compare_versions` (same, patch, minor, major, unpinned, invalid), `classify_staleness` (fresh/aging/old/very-old boundaries), `compute_summary` (all-good, mixed, all-unknown, yanked counted)
- `test_report.py` — covers `render_html`: DOCTYPE present, package name in output, XSS escaping in package name, summary counts, yanked badge, up-to-date row; `render_terminal`: package name present, exit code derivation

Minimum 38 tests. All must pass with `python -m pytest tests/ -v`.

---

## Success Criteria

1. `python main.py .` scans `requirements.txt` in the current directory and prints a terminal report without crashing.
2. `python main.py --format html --output report.html .` writes a valid self-contained HTML file with no external asset references.
3. All 38+ tests pass: `python -m pytest tests/ -v` shows 0 failures.
4. Packages on PyPI are correctly classified as `up-to-date`, `patch`, `minor`, `major`, or `unpinned` based on version comparison.
5. Yanked releases are flagged visually in both terminal and HTML output.
6. The tool exits with code 1 when `--exit-on-outdated` is passed and outdated packages exist; exits 0 otherwise.
