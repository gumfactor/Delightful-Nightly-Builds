# PRD — Protocol Forge

> **Build date:** 2026-07-19
> **Category:** B — Productivity Utility
> **Complexity:** Ambitious Project

---

## Goal

A local CLI that turns structured research-study parameters into a complete, regulatory-checklist-verified IRB/ethics protocol draft, while building a reusable local library of approved boilerplate language that makes every subsequent protocol faster and more consistent than the last.

## User Story

As a lab director who runs human-subjects research and repeatedly writes and renews IRB/ethics protocols by hand, I want a tool that (1) catches missing or risky elements in a study design before I submit it, and (2) reuses my own previously-approved language for recurring sections (data security, vulnerable-population safeguards, consent boilerplate) instead of me copy-pasting from old Word documents, so that ethics application writing stops being a from-scratch task every time.

## Scope

### In Scope
- A structured JSON study-description format (`init` command scaffolds a blank template with inline comments-as-keys for guidance)
- A deterministic, rule-based **compliance checklist engine** (no AI required) that checks a study description for:
  - Missing required fields
  - Deception without a debrief plan
  - Vulnerable populations without a matching safeguard keyword in procedures/consent text
  - Identifiable data without a security/encryption mention in the storage plan
  - Missing or zero data retention period
  - No risks documented
  - Compensation offered without a withdrawal-without-penalty mention in the consent process
  - Each finding has a severity (`blocking` / `warning`) and a human-readable message
- A local SQLite **protocol library** that persists every drafted study (JSON + generated section text + status: `draft` / `approved`) and supports:
  - Listing all stored protocols
  - Showing a stored protocol's full draft
  - Marking a protocol `approved`, which makes its section text eligible for reuse
- A deterministic **tag-based similarity matcher**: for a new study, finds the best-matching *approved* past protocol per canonical section (based on shared vulnerable-group tags, identifiable-data flag, and deception flag) and reuses its stored section text verbatim (marked as reused) instead of regenerating it
- A **drafting engine** for 6 canonical IRB sections (Study Summary, Recruitment & Consent Process, Procedures, Risks & Benefits, Data Management & Confidentiality, Vulnerable Populations Safeguards — the last only when applicable) with a three-tier fallback per section:
  1. Reuse matched approved boilerplate (if similarity match found)
  2. Otherwise, call the Anthropic API to draft the section from the structured fields (only if `ANTHROPIC_API_KEY` is set at runtime)
  3. Otherwise, fill a deterministic prose template from the structured fields (always available, no key required)
- A full Markdown protocol document assembled from the sections plus a Compliance Check Summary appendix
- CLI commands: `init`, `check`, `draft`, `approve`, `list`, `show`
- Full test suite covering the checklist engine, similarity matcher, drafting fallback tiers, and CLI commands end-to-end

### Out of Scope
- Deadline/renewal-date tracking (already covered by the 2026-07-17 Deadline Guardian build — this build is scoped strictly to protocol content, not scheduling)
- Direct submission/integration with any institution's actual IRB portal (no public API exists for this)
- Free-text fuzzy/semantic similarity matching (would require an embeddings model or a live API call at match time; the deterministic tag-based matcher is used instead so the library works fully offline)
- A browser UI (Category B does not require one per STANDARDS.md; a CLI + generated Markdown/HTML report is the right shape for this workflow)
- Multi-user / multi-institution templates (built for one user's single-institution workflow)

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`sqlite3`, `json`, `argparse`, `dataclasses`, `urllib.request` for the optional Anthropic call, `html` for report escaping)
- **Runtime requirement:** `python3 protocol_forge.py <command> ...` — no install step

## Data Structure

**Study JSON** (user-authored input file):
```json
{
  "title": "string",
  "pi": "string (optional)",
  "study_type": "new | renewal | amendment",
  "population": {
    "description": "string",
    "vulnerable_groups": ["minors" | "prisoners" | "cognitively_impaired" | "pregnant" | "students_as_subjects" | "none", ...]
  },
  "procedures": "string",
  "deception": false,
  "deception_debrief": "string (required if deception true)",
  "data_collected": ["survey_responses", "audio_recording", ...],
  "data_identifiable": false,
  "data_storage_plan": "string",
  "data_retention_years": 3,
  "compensation": "string (optional, empty if none)",
  "risks": [{"description": "string", "likelihood": "string", "mitigation": "string"}],
  "recruitment_method": "string",
  "consent_process": "string"
}
```

**SQLite library** (`protocol_library.db`, created in the build's own folder or a user-chosen path via `--db`):
- `protocols` table: `id INTEGER PRIMARY KEY`, `title TEXT`, `status TEXT` (`draft`/`approved`), `study_json TEXT`, `created_at TEXT`
- `sections` table: `id INTEGER PRIMARY KEY`, `protocol_id INTEGER`, `section_key TEXT`, `text TEXT`, `source TEXT` (`reused`/`ai`/`template`), `tags TEXT` (JSON list used for future matching)

## Folder Structure

```
builds/2026-07-19-protocol-forge/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── protocol_forge.py
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── models.py        (Study dataclass, JSON load/validate)
│   ├── checklist.py      (compliance rule engine)
│   ├── library.py         (SQLite persistence + similarity matcher)
│   ├── drafting.py        (template + AI drafting, 3-tier fallback)
│   └── cli.py             (argparse commands)
└── tests/
    ├── test_models.py
    ├── test_checklist.py
    ├── test_library.py
    ├── test_drafting.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v` (from the build folder)
- **What will be tested:**
  - Study JSON loading: valid file, missing file, malformed JSON, missing required keys
  - Every checklist rule individually (each fires correctly and does not fire on a clean study)
  - Severity classification (blocking vs. warning) and overall completeness scoring
  - Library: saving a protocol, listing, showing, approving, and that only `approved` protocols are eligible for section reuse
  - Similarity matcher: correct best-match selection by tag overlap, no-match case, and that a draft-status protocol is never matched
  - Drafting fallback tiers: reused-boilerplate path, template-fallback path (no API key), and the Anthropic-call path (mocked — never a live call)
  - CLI end-to-end: `init` scaffolds a valid template, `check` reports findings correctly, `draft` produces a complete Markdown document and persists it, `approve`/`list`/`show` round-trip correctly
  - Error handling: malformed study file, unknown protocol id passed to `show`/`approve`

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests
2. Running `check` on a deliberately incomplete study surfaces every seeded compliance issue (deception-without-debrief, vulnerable-population-without-safeguard, identifiable-data-without-security-mention, missing-retention, no-risks, compensation-without-withdrawal) with correct severities
3. Running `draft` with no `ANTHROPIC_API_KEY` set produces a complete, non-empty Markdown protocol document using the deterministic template fallback for every section
4. Approving a protocol and then drafting a second, tag-similar study reuses the approved protocol's matching section text verbatim (verified by a test asserting the reused text appears unchanged, with a "(reused from protocol #N)" marker)
5. The Anthropic API path is exercised only through mocks in tests; no live network call is made during the build or test run

---

## Scope Changes

None — full scope as planned was delivered.
