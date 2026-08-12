# PRD — Snipvault

> **Build date:** 2026-08-12
> **Category:** H — Developer Tool
> **Complexity:** Ambitious Project
> **Day of week:** Wednesday

---

## Goal

A personal code-snippet library — save, tag, and search reusable code snippets from any language or project, with optional AI-assisted description/tag generation and natural-language search, usable both as a standalone CLI and as a Claude Code Skill invoked mid-session.

## User Story

As an intermediate-to-advanced developer who codes daily with AI assistance across many simultaneous projects (The Canada List, Kwyeter, lab tooling, this nightly-build repo itself), I want to save a snippet the moment I write something reusable — a regex, a SQL query shape, a shell one-liner, a Python utility function — and find it again by meaning rather than remembering the exact file I wrote it in, so that I stop re-deriving or re-prompting for code I've already written.

## Scope

### In Scope
- Local SQLite snippet store: id, title, language, code, description, tags (comma-joined), source (optional file path/label), created_at, updated_at, usage_count
- `add` — save a snippet from `--code`, a file path, or stdin; auto-detects language from a file extension when not given explicitly; auto-generates 3–5 tags via deterministic identifier/keyword extraction when tags aren't supplied
- `--ai-enrich` flag on `add` — calls Claude Haiku to write a one-line description and suggest tags when the user didn't supply them; always falls back to the deterministic extractor on missing key, network error, or malformed response (zero network calls without `ANTHROPIC_API_KEY`)
- `search <query>` — deterministic ranked keyword search across title/description/tags/code (weighted: title > tags > description > code; recency and usage_count as tie-breakers)
- `search --ai <query>` — natural-language search: Claude Haiku expands the query into keyword terms before running the same deterministic ranker (so ranking logic never depends on an unverifiable LLM judgment call); falls back to running the raw query as keywords when no key is set or the call fails
- `get <id>` — print full snippet, increments usage_count
- `list` — list all snippets, filterable by `--lang` / `--tag`
- `remove <id>`
- `render` — self-contained dark-mode HTML browsing dashboard: search box, language/tag filters, click-to-expand code view, copy-to-clipboard button, sorted by usage/recency
- All snippet text (code, titles, descriptions) inserted into the rendered HTML via an escaped JSON payload read with `textContent`/`createElement` — never raw string concatenation into HTML
- Companion Claude Code Skill (`skill/SKILL.md`) — a copyable skill definition that teaches a Claude Code session how to invoke `main.py` to save/search/insert snippets on the user's request (e.g. "save this as a snippet", "find my snippet for X")
- `requirements.txt` (stdlib only; the optional Anthropic call uses `urllib`, matching this catalog's established convention)

### Out of Scope
- Cross-machine sync / cloud storage (local SQLite only, inside this build folder, per Abort Protocol — no persistent cloud infra)
- Semantic vector embeddings / true similarity search (the AI-assisted search expands a query into keywords rather than embedding-based retrieval, to stay deterministic and auditable — see Scope Changes if this needs revisiting)
- Editor/IDE plugin (VS Code extension) — the Skill wrapper is the integration surface for tonight
- Snippet versioning / edit history (a snippet is add-then-optionally-remove; editing means remove + re-add tonight)

## Tech Stack

- **Language:** Python 3
- **Framework:** None (stdlib only)
- **Dependencies:** stdlib only (`sqlite3`, `argparse`, `urllib`, `json`, `re`, `html`) — see `requirements.txt`
- **Runtime requirement:** `python3 main.py <command>` from the build folder; `render` output opens directly in any browser (`file://`, no server)

## Data Structure

SQLite database at `data/snippets.db` (created on first `add`; not committed — matches this catalog's convention of runtime-created local databases).

```sql
CREATE TABLE snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    language TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '',       -- comma-joined, normalized lowercase
    source TEXT,                          -- optional origin label/path
    created_at TEXT NOT NULL,             -- ISO 8601 UTC
    updated_at TEXT NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0
);
```

`render` reads the full table and serializes it into an escaped JSON blob embedded in the generated HTML.

## Folder Structure

```
builds/2026-08-12-snipvault/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── main.py
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── db.py           (SQLite schema + CRUD + search ranking)
│   ├── enrich.py        (language detection, deterministic tag/description extraction, Claude Haiku enrichment + fallback)
│   ├── render.py        (self-contained HTML dashboard generator)
│   └── cli.py           (argparse commands, wires db/enrich/render together)
├── skill/
│   └── SKILL.md          (copyable Claude Code Skill definition)
└── tests/
    ├── __init__.py
    ├── test_db.py
    ├── test_enrich.py
    ├── test_render.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - DB: add/get/list/remove, filtering by language/tag, usage_count increment on get, search ranking order (title match outranks code-only match), empty-db search returns empty list, duplicate titles allowed with distinct ids
  - Enrich: language detection from filename extension (known + unknown extension), deterministic tag extraction from code identifiers, deterministic description fallback, AI enrichment success path (mocked HTTP), AI enrichment falls back on network error / malformed JSON / no API key (zero real network calls)
  - AI-assisted search: query expansion success path (mocked), falls back to raw-query keyword search on failure/no key
  - Render: HTML output is valid/self-contained, snippet data appears only inside the escaped JSON payload (never unescaped in raw HTML), a `</script><script>alert(1)</script>` payload in a snippet title is verified inert as text data, empty-vault render doesn't crash
  - CLI: `add` from `--code`, from a file, from stdin; `get` on missing id exits with a clear error (not a stack trace); `remove` on missing id; argument parsing for `--lang`/`--tag` filters

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests
2. `add` → `list` → `get` → `search` round-trips correctly against a real local SQLite file with no crashes across language/tag filters
3. With no `ANTHROPIC_API_KEY` set, `--ai-enrich` and `search --ai` make zero network calls and produce a fully usable deterministic result (verified via a `urlopen` call-count assertion in tests, not just log inspection)
4. `render` produces a self-contained HTML file that opens correctly and where an injected `<script>` payload in a snippet field is confirmed inert (rendered as text, never executed)
5. `skill/SKILL.md` is a self-contained, install-ready Claude Code Skill definition documented in Manual.md with the exact copy command

---

## Scope Changes

None — full scope as planned above was completed as specified.
