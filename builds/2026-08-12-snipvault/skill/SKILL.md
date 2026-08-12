---
name: snipvault
description: Save, search, and retrieve reusable code snippets from a personal local library. Use when the user asks to save something as a snippet, find a previously saved snippet, or reuse code they've written before in an earlier session or project.
---

# Snipvault — Personal Code Snippet Library

You have access to a local Snipvault CLI at `<SNIPVAULT_PATH>/main.py` (replace
`<SNIPVAULT_PATH>` with wherever the user installed this build folder — see
Manual.md's install instructions). It stores the user's own reusable code
snippets in a local SQLite database and lets you save, search, and retrieve
them on request.

## When to use this skill

- The user says something like "save this as a snippet", "remember this
  function", or "add this to my snippet library" → use `add`.
- The user says something like "find my snippet for X", "do I have a snippet
  that does Y", or "what was that regex I saved" → use `search`.
- The user asks to reuse or insert a previously saved snippet by id or
  description → use `get` after finding it with `search`.

## Commands

Run these via the Bash tool from `<SNIPVAULT_PATH>`:

**Save a snippet** (the code under discussion, or the most recent code block
you or the user just wrote):

```bash
python3 main.py add --title "<short descriptive title>" --code "<the code>" --lang <language> --source "<current project/file, if known>"
```

Omit `--lang` to auto-detect from a `--file` path instead of `--code`. If the
user has an `ANTHROPIC_API_KEY` set in their environment, you may add
`--ai-enrich` instead of manually filling `--description`/`--tags` — it will
generate both automatically. Otherwise, write a specific, honest one-line
`--description` yourself and pass `--tags` as a comma-separated list of 3-5
relevant keywords.

**Search for a snippet:**

```bash
python3 main.py search "<keywords describing what the user is looking for>"
```

Add `--ai` if `ANTHROPIC_API_KEY` is set and the user's request is phrased as
a natural-language question rather than keywords — it expands the query
before searching. Read the printed `#<id>` results back to the user.

**Retrieve a specific snippet:**

```bash
python3 main.py get <id>
```

This prints the full code. Show it to the user or insert it into their file
as requested — always let the user confirm before you write it into their
project; don't insert it silently.

**List or browse everything:**

```bash
python3 main.py list [--lang <language>] [--tag <tag>]
python3 main.py render --output snippets.html   # generates a browsable HTML dashboard
```

## Rules

- Never fabricate a snippet's contents — only save code that actually exists
  in the current conversation or file, verbatim.
- Always tell the user which `#id` a snippet was saved or found under, so
  they can retrieve it later.
- If `search` returns nothing, say so plainly rather than inventing a result.
