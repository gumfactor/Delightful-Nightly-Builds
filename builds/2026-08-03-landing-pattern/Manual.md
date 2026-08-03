# Manual — Landing Pattern

> **Version:** 1.0 (built 2026-08-03)
> **Complexity:** Ambitious Project

---

## What This Is

A read-only Python CLI that looks at every open pull request on a GitHub repo and answers the question the PR list view can't: which of these are actually safe to merge right now, in what order, and which ones will silently conflict with each other if you merge them carelessly? It classifies each PR's readiness (ready, conflicted, CI-failing, awaiting review, etc.), builds a changed-file overlap graph across the whole backlog, and produces a two-batch recommended merge order — a "merge these now, in this order" batch and a "these are ready but will need a rebase after Batch 1" batch — plus a sorted list of everything still blocked, with the specific reason. Useful for anyone who lets PRs accumulate across several parallel projects and wants to clear a backlog in one focused pass instead of opening each PR individually.

---

## Quick Start

1. Set `GITHUB_TOKEN` in your environment (a personal access token with repo read access is enough — `Contents: Read`, `Pull requests: Read`).
2. `python3 main.py sync --repo owner/name` — fetches every open PR and stores a snapshot.
3. `python3 main.py report --repo owner/name` — prints the merge-order report to your terminal.
4. For a browsable dashboard: `python3 main.py report --repo owner/name --format html --output report.html`, then open `report.html` in any browser.

---

## How to Use It

### `sync` — pull the current PR state

```
python3 main.py sync --repo owner/name [--token TOKEN]
```

Fetches every open PR (readiness fields, changed files, CI state, review state) and stores it as a new timestamped snapshot in a local SQLite database (`landing_pattern.db` by default, next to wherever you run the command). Each `sync` is additive — run it as often as you like and every run becomes a new row in the PR's history, not an overwrite.

### `report` — see the merge order

```
python3 main.py report --repo owner/name [--format text|json|html] [--output PATH] [--ai] [--run-id N]
```

Renders the most recent `sync` snapshot (or a specific one with `--run-id`). Three formats:

- `text` (default) — printed to the terminal, good for a quick check
- `json` — the full computed report, useful for scripting
- `html` — a self-contained dark-mode dashboard; opens directly via `file://`, no server needed

The report has four sections:

- **Batch 1** — ready PRs with no changed-file overlap with an earlier PR in the batch. Safe to merge back-to-back, in the listed order.
- **Batch 2** — also ready, but will conflict with a Batch 1 PR's files. Merge these after Batch 1 lands and you've rebased.
- **Blocked** — not ready. Each entry names the specific reason (merge conflict, CI failing, changes requested, CI pending, awaiting review, behind the base branch, or unknown), sorted with the most actionable reasons first.
- **Drafts** — listed separately, lowest priority.

Add `--ai` to get a one-sentence, Claude-generated note on each Blocked PR explaining what to do about it. Requires `ANTHROPIC_API_KEY` in your environment; without it, every note falls back to a fixed template for that PR's blocking reason (no network call is made).

### `history` — track a PR's readiness over time

```
python3 main.py history --repo owner/name --pr NUMBER
```

Shows every stored snapshot's view of one PR — its label and age at each `sync`. Useful for spotting a PR that's been stuck in the same blocked state across several syncs.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--db` | `landing_pattern.db` | Path to the SQLite snapshot database. Set once per repo if you track more than one. |
| `GITHUB_TOKEN` | (required) | GitHub personal access token, read-only scope is enough. Override per-call with `--token`. |
| `ANTHROPIC_API_KEY` | (optional) | Only needed for `report --ai`. Without it, blocked-PR notes use a deterministic template. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Error: no GitHub token` | `GITHUB_TOKEN` isn't set and `--token` wasn't passed | Export `GITHUB_TOKEN` or pass `--token` |
| `Error fetching PRs: GitHub API error 403 ...` | Token lacks repo read access, or you're behind a restricted egress proxy | Use a token with `repo` scope; if running in a sandboxed CI/build container, run `sync` from an environment with normal internet access instead |
| `Error: no snapshot found ... Run 'sync --repo ...' first` | `report` or `history` was run before any `sync` | Run `sync --repo owner/name` first |
| A PR you know is mergeable shows up in Blocked as `unknown` | GitHub hadn't finished computing `mergeable_state` yet (common right after a push) | Re-run `sync` a minute later |

---

## Known Limitations

- Read-only by design — it never merges, closes, comments on, or rebases anything. It tells you what to do; you still do it (or wire it into your own automation).
- One repo per invocation. To track several repos, run `sync`/`report` once per repo (optionally with a separate `--db` per repo).
- The two-batch merge order is a heuristic based on changed-file overlap, not a guarantee — it flags PRs that touch the *same files*, not every possible semantic conflict (e.g. two PRs that both add a route named the same thing in different files won't be caught).
- CI state comes from GitHub's combined-status and check-runs APIs; a repo with no CI configured at all will show `ci_state: none` for every PR, which is treated as passing for readiness purposes.
