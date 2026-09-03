# PRD — Promptbook

## Goal
Turn the prompts a user has already typed into Claude Code across all their local projects into
a searchable, scored, zero-manual-entry library of what actually worked, so they can find and
reuse an effective prompt instead of re-deriving it from memory.

## User Story
As someone who runs many simultaneous AI-assisted projects and loses context between sessions, I
want to run one command and get a searchable record of my own past prompts — tagged by what kind
of task they were and scored by what happened after I sent them (did it lead to edits, passing
tests, a commit, or did it stall on errors) — so that the next time I face a similar task I can
find a prompt that worked before instead of starting from a blank page.

## Scope

### In scope
- Recursively scan Claude Code session transcript files (`~/.claude/projects/**/*.jsonl`, or
  `--claude-dir`/`CLAUDE_CONFIG_DIR` override) and extract every human-authored prompt turn.
- For each prompt, deterministically derive an "episode" of what happened next in that same
  session: tools used, files edited, bash commands run, test-runner invocations and a pass/fail
  signal, git-commit detection, and unresolved-error detection.
- Deterministic 0–10 effectiveness score from the episode signals.
- Deterministic task-type classifier (bug-fix / feature / refactor / research / test / docs /
  config / review / other) from the prompt text.
- Local SQLite library, deduplicated by prompt UUID, with incremental re-ingest (already-seen
  session files are re-scanned only for lines past their last-seen line count).
- CLI: `ingest`, `search` (filter by project/task-type/min-score/text query), `stats`, `render`
  (self-contained HTML dashboard).
- Optional `--ai` enrichment: Claude Haiku writes a one-sentence "why this worked" note for
  top-scoring prompts, built strictly from the prompt text and already-computed aggregate
  features (score, task type, tool names) — never raw tool output or file contents. Unconditional
  deterministic fallback (a templated sentence from the same features) when `ANTHROPIC_API_KEY`
  is unset, verified to make zero network calls in that path.
- Companion Claude Code Skill (`skill/SKILL.md`) so `ingest`/`search` can be invoked from inside
  a coding session.

### Out of scope
- Modifying or deleting the user's actual Claude Code session files (strictly read-only).
- Cross-machine or cross-user sync — this is a single local SQLite file.
- Any transcript content beyond human-authored prompt text and structural tool-call metadata is
  ever read into a stored field or sent anywhere (assistant prose, file contents, and tool
  outputs are inspected in memory only to derive boolean/numeric episode signals, never stored
  verbatim or transmitted).
- Prompt de-identification/redaction — this is a personal, local tool over the user's own data,
  matching the precedent of every other build that persists the user's own git/grant/lecture
  content locally.

## Tech Stack
Python 3, standard library only (`json`, `sqlite3`, `re`, `argparse`, `dataclasses`, `pathlib`,
`urllib` for the optional Anthropic call). `requirements.txt` lists only `pytest` (test-only).
Vanilla HTML/CSS/JS for the rendered dashboard (no build step, no CDN dependency needed since the
UI has no charts). `pytest` for tests.

## Data Structure

### SQLite schema (`data/promptbook.db`)
```
prompts(
  prompt_uuid TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  project TEXT NOT NULL,          -- from the record's own `cwd` field
  git_branch TEXT,
  entrypoint TEXT,                -- e.g. "cli", "remote_trigger" — how the session was started
  timestamp TEXT NOT NULL,        -- ISO 8601, from the record
  prompt_text TEXT NOT NULL,
  task_type TEXT NOT NULL,
  score INTEGER NOT NULL,         -- 0-10
  tools_used TEXT NOT NULL,       -- JSON array
  files_edited INTEGER NOT NULL,
  test_run INTEGER NOT NULL,      -- 0/1
  test_passed INTEGER,            -- 0/1/NULL (NULL = no test run detected)
  git_commit INTEGER NOT NULL,    -- 0/1
  had_error INTEGER NOT NULL,     -- 0/1
  ai_note TEXT                    -- optional, filled by --ai enrichment
)

ingested_files(
  file_path TEXT PRIMARY KEY,
  last_line_count INTEGER NOT NULL,
  last_ingested_at TEXT NOT NULL
)
```

### Episode signal → score formula (deterministic, hand-verified in tests)
Base 0. `+3` git commit detected in episode. `+2` a test-runner command detected AND a pass
signal detected in its output. `+1` a test-runner command detected with no clear pass/fail signal
either way. `+1` at least one file edited (Edit/Write/NotebookEdit) with zero unresolved errors.
`-2` an error signal (non-empty `is_error` tool result, or `Traceback`/`Error:` pattern in a tool
result) appears with no subsequent successful edit/test/commit in the same episode ("unresolved").
Clamped to `[0, 10]`.

## Folder Structure
```
builds/2026-09-03-promptbook/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── data/                      -- created at runtime, holds promptbook.db
├── skill/
│   └── SKILL.md
├── src/
│   ├── __init__.py
│   ├── extract.py             -- JSONL parsing, prompt-turn extraction
│   ├── episode.py             -- post-prompt episode signal extraction
│   ├── classify.py            -- deterministic task-type classifier
│   ├── score.py               -- deterministic effectiveness scorer
│   ├── storage.py             -- SQLite persistence, incremental ingest
│   ├── ai_enrich.py           -- optional Claude Haiku note + deterministic fallback
│   ├── render.py              -- self-contained HTML dashboard renderer
│   └── cli.py                 -- ingest/search/stats/render command wiring
└── tests/
    ├── fixtures/               -- realistic synthetic .jsonl session files
    ├── test_extract.py
    ├── test_episode.py
    ├── test_classify.py
    ├── test_score.py
    ├── test_storage.py
    ├── test_ai_enrich.py
    ├── test_render.py
    └── test_cli.py
```

## Testing Strategy
- **Framework:** `pytest`, run via `python -m pytest tests/ -v`.
- **Fixtures:** hand-authored synthetic `.jsonl` files under `tests/fixtures/` that mirror the
  real Claude Code transcript shape verified by reading this build container's own session file
  (`type: user/assistant`, `message.content` blocks, `tool_use`/`tool_result`, `isSidechain`,
  `cwd`, `entrypoint`) — never a live/real transcript in the committed test fixtures.
- **extract.py:** genuine text prompts are kept; pure `tool_result`-echo user turns are excluded;
  `isSidechain: true` turns are excluded; non-`user`/`assistant` line types (`queue-operation`,
  `attachment`, `atis-latch`) are skipped without error; malformed JSON lines are skipped, not
  fatal to the whole file.
- **episode.py:** git-commit detection, test-runner + pass detection, test-runner + fail
  detection, unresolved-error detection, edit-with-no-error detection — each as an isolated case
  with a hand-built fixture episode.
- **classify.py:** at least one boundary-case test per task-type category, plus a default-to-
  "other" case for text matching no keyword rule.
- **score.py:** hand-computed reference cases covering each formula branch and the 0/10 clamps.
- **storage.py:** dedup by `prompt_uuid` on re-ingest of the same file; incremental ingest only
  processes lines past the previously recorded line count; a second `ingest` run with no new
  lines inserts zero new rows.
- **ai_enrich.py:** the Anthropic API call is fully mocked (an injectable transport); a test
  asserts zero network calls occur when `ANTHROPIC_API_KEY` is unset.
- **render.py:** a `</script><script>` + `<img onerror>` payload injected into a fixture prompt's
  text renders as inert text with no injected DOM node, verified with a real HTML parser
  (`html.parser`), not a string `in` check.
- **cli.py:** end-to-end `ingest` → `search` → `stats` → `render` over a fixture directory,
  argument-parsing error cases (bad `--min-score`, missing `--claude-dir`).
- **Manual, non-mocked verification:** run `ingest` against this build container's own real
  `~/.claude/projects/**/*.jsonl` (this very session's transcript) after tests pass, then `render`
  and open the output in the container's pre-installed headless Chromium to confirm it handles
  genuine data end to end, not just synthetic fixtures.
- Minimum 15 tests; target substantially more given the number of independent code paths.

## Success Criteria
1. `ingest` run against a real Claude Code session directory (this build container's own,
   verified manually) extracts only genuine human-authored prompts — zero tool-result echoes or
   sidechain turns leak into the `prompts` table.
2. Every stored prompt has a deterministic `task_type` and `score` in `[0, 10]` computed with no
   AI call, verified by hand-computed reference cases in `test_score.py`/`test_classify.py`.
3. Re-running `ingest` on the same source directory with no new session activity inserts zero
   duplicate rows (verified by `prompt_uuid` primary key + incremental line-count tracking).
4. `render` produces a self-contained HTML file that opens standalone, is searchable/filterable
   client-side, and safely renders a live XSS payload as inert text (verified in headless
   Chromium, not just a unit test).
5. All tests pass (`python -m pytest tests/ -v`), zero failures, at or above the 15-test minimum.
