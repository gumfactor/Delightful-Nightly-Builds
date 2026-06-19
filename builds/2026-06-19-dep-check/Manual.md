# Manual — dep-check

**dep-check** scans Python dependency files for outdated or yanked packages by querying the PyPI JSON API. It classifies each pinned package as `up-to-date`, `patch`, `minor`, `major`, `unpinned`, or `unknown`, flags yanked releases, and outputs a coloured terminal report or a self-contained HTML dashboard.

---

## Requirements

- Python 3.8+
- No runtime dependencies (stdlib only)
- Internet access to reach `https://pypi.org`

---

## Quick Start

```bash
cd builds/2026-06-19-dep-check

# Scan current directory for requirements.txt, setup.cfg, Pipfile
python main.py .

# Scan a specific requirements file
python main.py path/to/requirements.txt

# Generate an HTML report
python main.py --format html --output report.html .

# Use as a CI gate (exit 1 if anything needs updating)
python main.py --exit-on-outdated . && echo "All good" || echo "Update needed"
```

---

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `path` | `.` | Directory to scan for known requirements files, or path to a single file |
| `--format text\|html` | `text` | Output format |
| `--output FILE` | (stdout) | Write output to FILE instead of printing |
| `--exit-on-outdated` | off | Exit 1 if any packages have status `patch`, `minor`, or `major` |

---

## Supported Files

| File | Format |
|------|--------|
| `requirements.txt` | PEP 508 subset |
| `requirements-dev.txt` | PEP 508 subset |
| `setup.cfg` | `[options] install_requires` |
| `Pipfile` | `[packages]` and `[dev-packages]` |

When scanning a directory, all matching files are collected and merged. Duplicate package names from different files are both retained (they may have different pins).

---

## Status Labels

| Status | Meaning |
|--------|---------|
| `up-to-date` | Pinned version equals or exceeds PyPI latest |
| `patch` | Latest is a patch bump ahead (e.g. 2.28.0 → 2.28.1) |
| `minor` | Latest is a minor bump ahead (e.g. 2.28.0 → 2.29.0) |
| `major` | Latest is a major bump ahead (e.g. 2.28.0 → 3.0.0) |
| `unpinned` | No version pin (`requests` with no specifier) |
| `unknown` | Package not found on PyPI or connection error |

A **YANKED** badge appears alongside any status when the pinned version has been yanked on PyPI. Yanking usually signals a security issue or critical bug — treat yanked pins as urgent regardless of their update status.

---

## Running Tests

```bash
cd builds/2026-06-19-dep-check
python -m pytest tests/ -v
```

62 tests across 3 files. No network access required — all tests use in-memory fixtures.

---

## Example Output

```
Package     Pinned         Latest         Status
-------------------------------------------------
requests    2.28.2         2.34.2         ↑↑ minor
flask       3.0.0          3.0.0          ✓ up-to-date
numpy       1.24.0         2.1.0          ↑↑↑ major
old-pkg     1.0.0          1.0.0          ✓ up-to-date [YANKED]
-------------------------------------------------
4 packages: 1 up-to-date, 2 need update, 1 yanked
```
