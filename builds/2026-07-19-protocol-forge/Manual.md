# Manual — Protocol Forge

> **Version:** 1.0 (built 2026-07-19)
> **Complexity:** Ambitious Project

---

## What This Is

Protocol Forge turns a structured description of a research study into a complete, checklist-verified IRB/ethics protocol draft. It runs a deterministic compliance check (no AI required) that catches the specific gaps reviewers most often kick a protocol back for, then drafts each standard protocol section — reusing your own previously-approved language wherever a similar past study exists, before ever asking an AI model to write anything fresh. Every protocol you approve makes the next one faster.

---

## Quick Start

1. `python3 protocol_forge.py init study.json` — creates a blank study template.
2. Edit `study.json` with your actual study details (see Study JSON Fields below).
3. `python3 protocol_forge.py check study.json` — see compliance findings before drafting.
4. `python3 protocol_forge.py draft study.json --out draft.md` — generate the full protocol document.
5. Once a protocol is genuinely approved by your IRB, run `python3 protocol_forge.py approve <id>` so its language becomes reusable boilerplate for future similar studies.

---

## How to Use It

### `init` — Scaffold a study file

```
python3 protocol_forge.py init study.json
```

Writes a template JSON with placeholder values (`REPLACE: ...`) for every field. Use `--force` to overwrite an existing file.

### `check` — Compliance checklist only

```
python3 protocol_forge.py check study.json [--json]
```

Runs 7 deterministic rules against the study and prints each finding with a severity:
- `blocking` — a required field is missing, or deception is used with no debrief plan
- `warning` — a vulnerable population lacks matching safeguard language, identifiable data has no security mention, retention period is missing, no risks are documented, or compensation is offered without a withdrawal-without-penalty mention

Exit code is `1` if any blocking finding is present, `0` otherwise — usable in a script/CI gate. `--json` prints machine-readable output.

### `draft` — Generate and save a full protocol

```
python3 protocol_forge.py draft study.json --out draft.md --db protocol_library.db
```

Runs the checklist, drafts all 6 canonical sections (Study Summary, Recruitment & Consent Process, Procedures, Risks & Benefits, Data Management & Confidentiality, and Vulnerable Populations Safeguards when applicable), writes a Markdown document to `--out` (default: a slugified version of the study title), and saves the protocol to the local library with status `draft`.

Each section is drafted using the first tier that's available:
1. **Reuse** — if an *approved* past protocol shares a similar profile (same vulnerable-group tags, same identifiable-data flag, same deception flag), its stored section text is reused verbatim and marked `(reused from protocol #N)`.
2. **AI draft** — if `ANTHROPIC_API_KEY` is set in your environment, Claude drafts the section from your structured fields.
3. **Template** — otherwise, a deterministic template fills your structured fields into standard regulatory prose. Always available — the tool is fully functional with no API key.

### `approve` — Mark a protocol as approved

```
python3 protocol_forge.py approve 1 --db protocol_library.db
```

Once your IRB has actually approved a protocol, mark it approved here. Only approved protocols' sections are eligible for reuse in future drafts — nothing is ever reused from an unreviewed draft.

### `list` / `show` — Browse the library

```
python3 protocol_forge.py list --db protocol_library.db
python3 protocol_forge.py show 1 --db protocol_library.db
```

`list` shows every protocol's id, status, completeness score, and creation date. `show` prints the full stored draft, annotating each section with where its text came from (`reused` / `ai` / `template`).

---

## Study JSON Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `title` | string | Yes | |
| `pi` | string | No | Principal investigator name |
| `study_type` | `"new"` \| `"renewal"` \| `"amendment"` | Yes | |
| `population.description` | string | Yes | |
| `population.vulnerable_groups` | list | No | Any of `minors`, `prisoners`, `cognitively_impaired`, `pregnant`, `students_as_subjects`, `none` |
| `procedures` | string | Yes | |
| `deception` | bool | No | Default `false` |
| `deception_debrief` | string | Required if `deception` is `true` | |
| `data_collected` | list of strings | Yes | At least one item |
| `data_identifiable` | bool | No | Default `false` |
| `data_storage_plan` | string | Yes | |
| `data_retention_years` | number | No | Default `0` (flagged if 0) |
| `compensation` | string | No | Empty string if none |
| `risks` | list of `{description, likelihood, mitigation}` | No | Empty list flagged as a warning |
| `recruitment_method` | string | Yes | |
| `consent_process` | string | Yes | |

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `ANTHROPIC_API_KEY` | not set | Optional environment variable. When set, the AI drafting tier is used for any section with no reusable boilerplate match. |
| `--db` | `protocol_library.db` | SQLite database path for the protocol library. |
| `--out` | slugified study title + `.md` | Output path for the drafted Markdown document. |

No configuration is required to use the tool — every command works fully offline with no API key.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Error: Study file is not valid JSON` | Trailing comma or unquoted key in the study file | Validate the JSON (e.g. `python3 -m json.tool study.json`) |
| `Error: Study definition is missing required field(s): ...` | A required top-level field is empty or absent | Fill in every field listed in the error message |
| A section that should reuse old text is drafted fresh instead | The past protocol isn't `approved` yet, or its tag profile (vulnerable groups / identifiable / deception) doesn't match closely enough | Run `approve <id>` on the past protocol, or check that both studies share the same vulnerable-group and identifiable/deception flags |
| AI tier is never used even with `ANTHROPIC_API_KEY` set | A reusable match was found first (reuse always takes priority), or the API call failed and fell back to the template tier silently | Check `show <id>`'s per-section `(source: ...)` annotation to see which tier was actually used |

---

## Known Limitations

- Similarity matching is tag-based (vulnerable groups, identifiable-data flag, deception flag), not full-text semantic similarity — two studies with very different procedures but the same tag profile can match. This is a deliberate tradeoff for determinism and offline operation; review any reused section before submitting.
- Does not track submission deadlines or renewal dates — pair with the 2026-07-17 Deadline Guardian build for scheduling.
- Does not integrate with any institution's actual IRB submission portal; the output is a Markdown document meant to be copied/pasted or attached.
- The compliance checklist covers common, general patterns — it is not a substitute for your institution's actual IRB requirements or legal review.
