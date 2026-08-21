---
name: secret-scan
description: Scan the current repo's working tree for accidentally committed secrets and credentials before a commit or push. Use when the user asks to check for leaked API keys/secrets, wants a pre-commit sanity check, or says something like "scan this repo for secrets" or "did I leak a key?".
---

# Secret Scan

Fast, working-tree-only secret check for the repo you're currently working in — the quick
mid-session counterpart to Secret Sweep's full `history` audit, which is slower and meant to
be run periodically from the CLI directly rather than every session.

## When to use this

- Before committing or pushing, when the user wants a sanity check.
- After pasting in a config block, `.env`-style file, or code from elsewhere.
- Whenever the user directly asks to check for leaked secrets/API keys.

## How to run it

From the repo you want to check, run the companion CLI's `scan` command (working tree only —
does **not** walk git history, which is a separate, slower operation):

```bash
python3 /path/to/secret-sweep/secretsweep.py scan .
```

Findings are stored in `~/.secretsweep/findings.db` and also printed to the terminal,
grouped by severity. Every value is masked (first/last 4 characters only) — never paste
the raw secret back into the conversation even if you can see more of it locally.

If anything is flagged as `critical`:

1. Tell the user exactly what was found (masked preview + file + line), not the raw value.
2. Recommend removing it from the tracked file and adding the path to `.gitignore`.
3. Recommend rotating the credential with its provider — a value that was ever committed to
   a working tree the user intends to push should be treated as compromised regardless of
   whether it's removed before the push.

If the user wants the full historical audit (has this secret ever been committed, even if
it's since been removed from the current tree?), point them to the CLI directly:

```bash
python3 /path/to/secret-sweep/secretsweep.py history .
python3 /path/to/secret-sweep/secretsweep.py report --format html --output secrets-report.html
```

Do not run `history` automatically from this skill — it walks the full commit log and can be
slow on a large repo; it's an explicit, occasional audit action, not a per-commit check.

## Acknowledging false positives

If the user confirms a flagged value is a placeholder/test fixture, not a real secret:

```bash
python3 /path/to/secret-sweep/secretsweep.py ack <finding_id>
```

This suppresses it from future "new finding" counts without deleting the audit trail.
