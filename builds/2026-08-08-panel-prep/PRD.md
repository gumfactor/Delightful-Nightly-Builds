# PRD — Panel Prep

> **Build date:** 2026-08-08
> **Category:** D — Creative / Generative
> **Complexity:** Ambitious
> **Day of week:** Saturday

---

## Goal

Turn a pasted or file-loaded grant-proposal draft (Specific Aims / Significance / Innovation / Approach) into a mock NIH-style study-section critique — a deterministic completeness/rigor checklist plus three reviewer-persona scores and rationales — so weaknesses surface before real submission, with score history tracked across revisions of the same project.

## User Story

As an Associate Professor who writes grants regularly and has explicitly named "Grant writing" and "Ethics application generation" as friction points, I want to paste a proposal draft and get a structured, critical, NIH-scoring-rubric-shaped review from multiple simulated reviewer perspectives, so that I can find and fix weak spots — missing power analysis, an under-argued significance case, absent rigor/reproducibility language — before a real study section ever sees the draft, and so I can see whether my revisions are actually improving the draft over time.

## Scope

### In Scope
- A section parser that splits a pasted/loaded proposal draft into named sections (Specific Aims, Significance, Innovation, Approach, Rigor & Reproducibility) from Markdown headers, ALL-CAPS headers, or `Header:`-style lines, with a whole-document-as-Aims fallback when no headers are found.
- A deterministic, regex-based completeness/rigor checklist (no AI, no ML) covering per-section checks that mirror what real NIH reviewers are trained to look for (numbered aims with hypothesis language, an explicit significance gap, an explicit innovation claim, a sample-size/power justification, a timeline, pitfalls/alternatives, preliminary data, a statistical analysis plan, and rigor/reproducibility language: sex as a biological variable, blinding/randomization, reagent/resource authentication).
- Three fixed reviewer personas (Rigor Hawk, Vision Advocate, Generalist), each weighting the checklist differently, each producing a deterministic NIH-style score (1 = exceptional, 9 = poor) for Significance / Innovation / Approach / overall Impact, with rationale bullets drawn from the actually-failed checks in that persona's focus area. This deterministic path is always available and is independently useful with no API key.
- An optional Claude Haiku call per persona (only when `ANTHROPIC_API_KEY` is set) that replaces the deterministic score/rationale with a richer narrative critique in that persona's voice, grounded in the same checklist results and the proposal text; any missing key, network failure, timeout, or malformed response falls back to the deterministic result with zero retries and zero silent data loss.
- A deterministic "resume of discussion" synthesis paragraph (reviewer agreement/disagreement framing from score variance, plus the top shared checklist failures) — always generated, no additional AI call required.
- Local SQLite persistence: every `submit` for a named project becomes a new, permanent version row (never overwritten); `history` and the HTML report show checklist pass-rate and overall Impact score trend across versions.
- CLI commands: `submit <file> --project NAME`, `list`, `history <project>`, `render <project> [--out path.html]`.
- Terminal summary output and a self-contained dark-mode HTML report (checklist matrix, persona score cards, resume paragraph, Chart.js 4.4.4 trend line with a DOM-table fallback when the CDN is unreachable) — all dynamic text delivered as an escaped JSON blob and inserted via `textContent`/`createElement`, never `innerHTML`.
- `requirements.txt` (stdlib only).

### Out of Scope
- Investigator and Environment NIH scoring criteria — these require CV/facilities information this tool is never given; fabricating a score for them would be actively misleading, so they are omitted entirely rather than guessed.
- A live database of real NIH funding outcomes or comparison against real study-section score distributions (no such free/public dataset exists for this).
- Multi-user/collaborative review (this is a personal single-user tool, matching every other build in this catalog).
- PDF/Word ingestion — plain text/Markdown input only; the user's proposal drafting tools already export or copy-paste as text easily.
- Editing/rewriting the proposal text itself (Voiceprint, 2026-07-28, already covers AI-writing-tell detection for prose; this tool's job is content-critique, not prose polish).

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None
- **Dependencies:** stdlib only (`argparse`, `sqlite3`, `re`, `json`, `urllib.request` for the optional Anthropic call)
- **Runtime requirement:** `python3 src/main.py <command> ...` — no install step, no virtualenv required beyond a standard Python 3 interpreter

## Data Structure

SQLite database (default `panel_prep.db`, override with `--db`):

```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    version_num INTEGER NOT NULL,
    submitted_at TEXT NOT NULL,
    source_path TEXT,
    sections_json TEXT NOT NULL,      -- {"aims": "...", "significance": "...", ...}
    checklist_json TEXT NOT NULL,     -- full checklist.run() result
    review_json TEXT NOT NULL,        -- full reviewer.build_review() result
    checklist_pass_rate REAL NOT NULL,
    overall_impact REAL NOT NULL,
    ai_used INTEGER NOT NULL,         -- 0/1, true if >=1 persona used the AI path
    UNIQUE(project_id, version_num)
);
```

No personal data is stored beyond what the user explicitly pastes into their own local proposal draft file, and that text never leaves the machine except as the section text sent to the Anthropic API when a key is supplied (matching the pattern of every prior optional-AI build in this catalog).

## Folder Structure

```
builds/2026-08-08-panel-prep/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── sample_proposal.txt
├── src/
│   ├── __init__.py
│   ├── parsing.py
│   ├── checklist.py
│   ├── reviewer.py
│   ├── db.py
│   ├── render.py
│   └── main.py
└── tests/
    ├── test_parsing.py
    ├── test_checklist.py
    ├── test_reviewer.py
    ├── test_db.py
    ├── test_render.py
    └── test_main.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v` (run from `builds/2026-08-08-panel-prep/`)
- **What will be tested:**
  - Section parsing across Markdown/ALL-CAPS/`Header:`-style headers, the no-headers-found fallback, empty input, and mixed casing/whitespace
  - Checklist pass/fail correctness for representative pass and fail text per check, and the all-sections-missing case
  - Deterministic persona scoring (monotonic: a fuller checklist never scores worse than an emptier one) and rationale content
  - The AI path: a mocked well-formed response is used; a mocked malformed/missing-field response falls back to deterministic; a mocked network error falls back to deterministic; no API key present makes zero calls to `urllib.request.urlopen` (asserted via mock)
  - SQLite persistence: project auto-creation, version auto-increment per project, history ordering, re-submitting an existing project
  - HTML report: contains the project name and current scores, a script-injection payload (`</script><script>alert(1)</script>`) placed in proposal text renders only inside the JSON payload and never as a literal unescaped `<script>` tag in the surrounding HTML, valid JSON round-trips through `json.loads`
  - CLI end-to-end: `submit` on a real sample file writes a version row and prints a non-empty summary; `list`/`history`/`render` run without error against a freshly seeded temp database

## Success Criteria

1. All tests pass (zero failures)
2. `submit` on a representative complete proposal draft and a representative sparse draft produce checklists whose pass-rates and persona scores correctly reflect the input (complete draft scores strictly better than the sparse one)
3. With no `ANTHROPIC_API_KEY` set, `submit`/`render` still produce a fully populated, genuinely useful critique (not a placeholder) and make zero network calls
4. `history` and the HTML report correctly show version-over-time score trend after 2+ submissions to the same project
5. The HTML report is self-contained (opens via `file://`, no server) and is verified safe against a script-injection payload placed directly in proposal text

---

## Scope Changes

None — full scope as specified above was implemented as planned.
