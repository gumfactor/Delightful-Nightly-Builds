# Future Features — Worklog: Cross-Agent Project Activity Workstreams

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **GitHub review + CI check-run ingestion** — `github_collector.py` already fetches issues
   and PRs; adding `/pulls/{n}/reviews` and `/commits/{sha}/check-runs` calls would let
   `standup`'s "blocked" bucket include failing CI, not just failing checkpoint validation.
2. **`worklog resume --json`** — machine-readable output so an agent can consume the resume
   package programmatically instead of parsing terminal text (the `ResumePackage` dataclass in
   `views.py` already has everything needed; this is a formatting-layer addition only).
3. **`worklog workstreams --merge A B`** — a manual override to merge two workstreams the
   deterministic correlation didn't connect, updating every event's `workstream_id` in one
   transaction.

## Medium Effort (roughly one nightly build session)

4. **A small checkpoint-writer hook for this very repo** — a Claude Code `Stop` or
   `SessionEnd` hook that writes a checkpoint JSON automatically from the session's tool-call
   history (files touched, tests run) would give worklog its first fully-automatic capture
   path for a real AI agent, not just the manual `checkpoint --from-file` contract.
5. **Cross-project "where was I?" view** — `worklog resume` currently operates on one repo's
   ledger; a thin wrapper that scans a configured list of repos and surfaces the single most
   stale-and-important workstream across all of them would directly serve the "managing many
   simultaneous projects" friction point named in PROFILE.md.
6. **Fuzzy `why` search** — the current substring match is honest but literal; a local
   TF-IDF/keyword-overlap layer (still no external API call, still evidence-cited) would catch
   paraphrased queries without giving up the "deterministic first" principle from the Idea
   Brief.

## Ambitious Extensions (multi-session effort)

7. **MCP server wrapper** — expose `sync`/`resume`/`standup`/`why` as MCP tools so any
   MCP-aware agent (not just one invoking this CLI directly) can query project state
   mid-conversation, exactly as the Idea Brief's "Future Expansion" section describes.
8. **Optional Anthropic-API-assisted workstream titling/summarization** — once the
   deterministic correlation core has been used long enough to trust, an opt-in layer that
   asks Claude Haiku to write a one-line human-readable title for `general_bucket` and
   `branch`-signal workstreams (never to invent correlations, only to phrase ones already
   established) would make `worklog workstreams` output more readable without compromising the
   evidence-before-prose principle.

---

## Possible Integration Points

- **Git Standup Reporter** (2026-06-07) and **AI Session Context Bridge** (2026-06-06) are the
  two builds this one was explicitly built to absorb and surpass per the Idea Brief; once this
  proves useful in daily use, those two could reasonably be marked superseded in
  `builds/index.md` rather than kept as separate tools to remember to run.
- **Pipeline Pulse** (2026-07-09) reconciles this nightly-build repo's own `builds/index.md`
  against git history — a shared pattern (read-only git plumbing, graceful GitHub degradation)
  that a future MCP-server version of Worklog could expose as a tool Pipeline Pulse itself
  calls, rather than duplicating git-inspection logic across builds.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| No AI-provider-specific session parsers | Add a small adapter per provider (Codex/Claude/Copilot) that converts each provider's native session log into a Worklog checkpoint JSON, per the Idea Brief's "Future Expansion" |
| GitHub reviews/CI not ingested | Add `/pulls/{n}/reviews` and `/commits/{sha}/check-runs` calls to `github_collector.py`, feeding `standup`'s blocked/in-progress logic |
| Correlation has no semantic layer | Any future addition here must stay evidence-cited and optional per the Idea Brief — a plain keyword/TF-IDF pass is the natural first step before reaching for an LLM call |
| Ledger is single-machine | If multi-machine use becomes real, sync `.worklog/ledger.db` via the same mechanism as the rest of the user's dotfiles/config rather than building bespoke cloud sync (explicitly out of scope per the Idea Brief) |
