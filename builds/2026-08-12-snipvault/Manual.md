# Manual — Snipvault

> **Version:** 1.0 (built 2026-08-12)
> **Complexity:** Ambitious Project

---

## What This Is

Snipvault is a personal code-snippet library: a local SQLite-backed store for reusable code — a regex, a SQL query shape, a shell one-liner, a Python helper — with keyword search, optional Claude Haiku-assisted tagging and natural-language search, and a browsable self-contained HTML dashboard. It ships both as a standalone CLI and as a companion Claude Code Skill, so it can be invoked mid-session ("save this as a snippet") as well as from a terminal.

---

## Quick Start

1. `cd` into this build folder: `builds/2026-08-12-snipvault/`
2. Save your first snippet:
   ```bash
   python3 main.py add --title "Dedup list preserving order" --code "def dedup(items):
       seen = set()
       return [x for x in items if not (x in seen or seen.add(x))]" --lang python
   ```
3. Find it later: `python3 main.py search "dedup order"`
4. Retrieve the full code: `python3 main.py get <id>` (the id was printed by `add`/`search`)
5. Browse everything visually: `python3 main.py render --output snippets.html` then open `snippets.html` in any browser

---

## How to Use It

### Saving snippets (`add`)

```bash
python3 main.py add --title "<title>" --code "<code>" [--lang <language>] [--tags a,b,c] [--description "..."] [--source "<file/project label>"]
python3 main.py add --title "<title>" --file path/to/snippet.py           # reads code from a file, auto-detects language
cat some_script.sh | python3 main.py add --title "<title>" --lang bash    # reads code from stdin
```

If you omit `--tags`/`--description`, a deterministic extractor fills them in (language-aware identifier frequency for tags; first comment or first code line for the description) — no network call is made. Add `--ai-enrich` to have Claude Haiku write the description and suggest tags instead; this requires `ANTHROPIC_API_KEY` to be set in your environment, and silently falls back to the deterministic result if the key is missing or the call fails.

### Searching (`search`)

```bash
python3 main.py search "dedupe list order"          # deterministic keyword search
python3 main.py search --ai "how do I retry a flaky request"   # AI-expanded natural-language search (needs ANTHROPIC_API_KEY)
```

Results are ranked title-match > tag-match > description-match > code-match, with usage count and recency as tie-breakers. `--ai` translates your natural-language question into keyword terms first, then runs the same ranked search — it never lets the AI directly decide the ranking. Without a key, `--ai` just splits your query on whitespace and searches with that.

### Retrieving, listing, and removing

```bash
python3 main.py get <id>              # prints the full snippet and increments its usage count
python3 main.py list                  # list everything
python3 main.py list --lang python    # filter by language
python3 main.py list --tag regex      # filter by tag
python3 main.py remove <id>
```

### Browsing (`render`)

```bash
python3 main.py render --output snippets.html
```

Produces a self-contained dark-mode HTML page — a search box, a language filter, click-to-expand code, and a copy button per snippet. Open the file directly (`file://`); no server needed.

### Using it as a Claude Code Skill

Copy the skill folder into your Claude Code skills directory so any session can invoke it on request:

```bash
cp -r builds/2026-08-12-snipvault/skill ~/.claude/skills/snipvault
```

(Or into a specific project's `.claude/skills/snipvault` if you only want it available there.) Once copied, edit the `<SNIPVAULT_PATH>` placeholder inside `~/.claude/skills/snipvault/SKILL.md` to point at wherever you keep this build folder (or a global install, if you set one up per FutureFeatures.md's Quick Win #1). After that, saying things like "save this as a snippet" or "do I have a snippet for X" in any Claude Code session will trigger it.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--db <path>` | `data/snippets.db` (inside this build folder) | Where the SQLite database lives; pass a different path to point at a shared/global library |
| `ANTHROPIC_API_KEY` (env var) | unset | Enables `--ai-enrich` on `add` and `--ai` on `search`. Both features work fully without it, using deterministic fallbacks — no code is ever required to leave your machine |

No other configuration required.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `error: no code provided` on `add` | Ran `add` with none of `--code`, `--file`, or piped stdin | Supply one of the three; an empty/whitespace-only stdin is treated the same as none |
| `--ai-enrich` doesn't seem to do anything different | `ANTHROPIC_API_KEY` isn't set, or the API call failed | Check the env var is exported in the shell running `main.py`; on any failure it silently uses the deterministic tags/description instead — this is intentional, not a bug |
| `render` output looks empty | No snippets saved yet, or `--db` points at a different database than the one you've been adding to | Run `python3 main.py list` against the same `--db` path to confirm what's actually stored |

---

## Known Limitations

- The database lives inside this dated build folder by default — see FutureFeatures.md's "global install location" suggestion for making it reachable from any project.
- No snippet editing yet; correcting a mistake means `remove` + re-`add`.
- AI-assisted search quality depends on Claude Haiku's keyword-expansion guess; if it misses, fall back to plain `search` with your own keywords.
