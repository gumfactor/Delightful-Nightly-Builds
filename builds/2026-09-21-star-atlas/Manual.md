# Manual — Star Atlas

> **Version:** 1.0 (built 2026-09-21)
> **Complexity:** Ambitious Project

---

## What This Is

Star Atlas turns your GitHub starred repos into a searchable, tagged personal knowledge base instead of a scroll-forever list you never revisit. It syncs your real stars (via a GitHub token you already have), tags each one deterministically by language/topic keywords, optionally refines those tags and adds a one-sentence "why this might be useful" note using Claude, and gives you `search`/`list`/`stats` commands plus a self-contained dark-mode HTML dashboard you can open on your phone.

---

## Quick Start

1. `cd builds/2026-09-21-star-atlas`
2. Get a GitHub personal access token with `read:user` scope (Settings → Developer settings → Personal access tokens) if you don't already export `GITHUB_TOKEN`.
3. `python3 -m src.main sync --token YOUR_TOKEN` (or `export GITHUB_TOKEN=...` first and drop `--token`)
4. `python3 -m src.main render --open`
5. Browse, search, and filter your stars in the dashboard that opens.

---

## How to Use It

### Syncing

```
python3 -m src.main sync                 # incremental: only fetches stars newer than the last sync
python3 -m src.main sync --full          # re-fetch everything (safe to run any time, dedups by repo id)
python3 -m src.main sync --ai            # also send public repo metadata to Claude for a refined tag/note
```

`--ai` requires `ANTHROPIC_API_KEY` (env var or `--api-key`). Only already-public GitHub metadata (repo name, description, language, topics) is ever sent — never anything else. If the key is missing or the API call fails for any reason, every repo still gets a tag and note from the deterministic rule engine; nothing is ever left blank.

### Searching and browsing

```
python3 -m src.main search "llm"                    # text search across name/description/topics
python3 -m src.main list --tag "AI/ML"               # browse one tag
python3 -m src.main list --language Python            # browse one language
python3 -m src.main stats                              # counts by tag, by language, last sync time
```

### Dashboard

```
python3 -m src.main render                 # writes dashboard.html in this folder
python3 -m src.main render --out my.html --open   # custom path, opens in your default browser
```

The dashboard is a single self-contained HTML file — no server, no build step. It has a live search box and clickable tag filter chips, works on a phone screen, and every repo card links straight to GitHub.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--db` | `star_atlas.db` in this build folder | SQLite database path |
| `GITHUB_TOKEN` / `--token` | none (required for `sync`) | GitHub personal access token, `read:user` scope is enough |
| `ANTHROPIC_API_KEY` / `--api-key` | none (only used with `--ai`) | Claude API key for AI-refined tags/notes |
| `--out` (on `render`) | `dashboard.html` in this build folder | Output path for the HTML dashboard |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Error: No GitHub token provided.` | `GITHUB_TOKEN` not set and `--token` not passed | Export `GITHUB_TOKEN` or pass `--token` directly |
| `Error: GitHub API error 401: ...` | Token is invalid, expired, or lacks the right scope | Generate a new token with at least `read:user` scope |
| `Error: GitHub API error 403: ...` | Rate-limited, or token lacks access | Wait for the rate limit to reset, or check token permissions |
| `sync --ai` runs but tags look rule-based, not AI-refined | `ANTHROPIC_API_KEY` missing or the Claude call failed | This is by design — the fallback is silent and safe. Check the key is set and valid if you expect AI notes. |
| `render` output looks empty | Nothing synced yet | Run `sync` first — `render` only shows what's already in the local database |

---

## Known Limitations

- Read-only: this tool never un-stars or modifies anything on GitHub.
- Only your own account's stars — organization-wide star lists aren't included.
- `search` does substring matching, not fuzzy or ranked full-text search.
- If a repo is un-starred on GitHub, it stays in your local library until you manually delete the database — there's no automatic prune yet (see `FutureFeatures.md`).
