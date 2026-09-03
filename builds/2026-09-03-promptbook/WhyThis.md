# Why This — Promptbook

## Selection path
Fresh generation (not a lottery draw). Category C's 4 pending backlog rows are all unrated
(R=0 → 25% lottery chance); `random.randint(1,100)` rolled **92**, missing the gate, so Step 2d
(fresh ideas) applies. Pool size checked: 4 pending Category C rows, all rated `—`.

## Topic diversity check
Scanned the last 10 builds (2026-08-22 → 2026-09-02): Renewal Radar, Trading Book, Lecture Loom,
Grant Vault, Regression Lab, EDGAR Lens, Zebra Lab, Layer Guard, Fleet Drift, CiteForge.
Investment/finance appears twice (Trading Book, EDGAR Lens) — not saturated (threshold is >2).
No other domain repeats 3+ times. Category C's own history (9 prior builds — Investment Thesis
Journal, Paper Lens, PubMed Research Radar, Connectome, CanFile, Citation Vault, Waymark,
Curriculum Atlas, Grant Vault) has already covered: academic-paper discovery/reading (3x),
note-graphs, business-ownership lookups, grant-writing language, git-commit decisions, and course
concepts. Explicitly avoided a 4th paper/citation tool and anything overlapping Waymark's
git-decision-mining shape.

## Candidates considered

**1. Promptbook — auto-mined Claude Code prompt/session knowledge base (WINNER).**
Recursively scans the user's own local `~/.claude/projects/**/*.jsonl` session transcripts
(the real file format this very session is running from — verified structure by reading this
build container's own transcript file before designing the parser), extracts every
human-authored prompt across every local project, and for each one deterministically derives
what happened next in that session (files edited, tests run and their pass/fail signal, a git
commit made, unresolved errors) into a 0–10 effectiveness score and a keyword-heuristic task-type
tag (bug-fix / feature / refactor / research / test / docs / config / review / other). Ships a
searchable SQLite library, a CLI (`ingest`/`search`/`stats`/`render`), a self-contained HTML
dashboard, and an optional Claude Haiku "why this worked" note on top-scoring prompts.
Zero manual entry — the data already exists on the user's own machine every time they use Claude
Code. Directly targets two PROFILE.md-named friction points ("Context loss between AI coding
sessions", "Re-establishing context across AI sessions") and a named learning goal ("Master AI
agent workflows and orchestration"), none of which any of the 9 prior Category C builds touch —
the closest, Waymark, mines *git* decisions, not *prompts*, and AI Session Context Bridge
(2026-06-06, 3/10) was marked down specifically for requiring manual entry, which this build
avoids entirely by construction.

**2. Highlight Vault (backlog idea #28) — rejected.** Personal database of paper
highlights/quotes, AI-clustered thematically. Real value, but its own backlog note (written
2026-08-25) already flags it as sitting close enough to Citation Vault (reading-workflow
tracker) and Connectome (note-graph) that a third "personal library of text snippets" build
risks blurring together with what exists. Also requires the user to paste highlights in —
another manual-entry-dependent design, the same pattern PROFILE ratings have penalized before.

**3. Canadian Open-Data Consumer Knowledge Base — rejected.** A searchable local index over
Statistics Canada / Health Canada open datasets relevant to Canada List editorial and consumer
research, AI-tagged by topic. Real live no-auth data source (a genuine strength), but the
Canada List ingestion/verification/editorial pipeline is already deeply covered by four prior
builds (CanFile, Ingest Gate, Provenance, Maple Press); this would be a general dataset browser
bolted onto that pipeline rather than a clearly novel personal-knowledge angle, and reads closer
to a Data Explorer (Category F) build wearing a Category C label. Logged to `builds/ideas.md` for
a future Category F night instead of forcing it into C.

## Idea Brief Traceability
N/A — no linked Idea Brief; this was freshly generated tonight, not drawn from a brief-backed
backlog row.

## Design decisions worth recording
- The database defaults to `data/promptbook.db` **inside the build folder**, resolved relative
  to the script's own location (not the caller's CWD) so it behaves the same regardless of where
  the user invokes it from — consistent with "local persistence... within the build folder" and
  avoids a CWD-dependent bug class.
- The source directory defaults to `~/.claude/projects` but respects `CLAUDE_CONFIG_DIR` if set
  (the real env var Claude Code itself uses to relocate its config directory) and accepts
  `--claude-dir` for override/testing — never hardcoded to this build container's own path.
- Only genuinely human-authored prompt turns are extracted: `type == "user"` lines whose message
  content is a plain string, or a content-block list containing a non-empty `text` block, are
  kept; lines that are pure `tool_result` echoes (how Claude Code represents tool responses,
  per Anthropic API convention) and `isSidechain: true` lines (subagent-internal turns, not the
  top-level conversation) are excluded. This was verified against this very container's own real
  transcript file before writing the extraction tests.
- The effectiveness score and task-type tag are both fully deterministic and unit-tested against
  hand-computed reference cases; the optional AI layer only ever adds a one-sentence annotation on
  top of an already-computed score — it can never change what got stored or how it was scored,
  matching this catalog's established "AI enriches, never decides" pattern.
