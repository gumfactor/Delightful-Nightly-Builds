# Manual — Counterpoint

> **Version:** 1.0 (built 2026-09-20)
> **Complexity:** Ambitious Project

---

## What This Is

Counterpoint turns a manuscript's raw peer-review comments plus your own response notes into a complete, correctly-numbered "Response to Reviewers" letter — and it will not let you submit one that silently drops a reviewer's point. You write two plain-text files (the reviewers' comments, and your response to each), Counterpoint cross-references them and refuses to build a letter with gaps unless you explicitly force it, then renders a clean Markdown/HTML/plain-text letter ready to attach to your resubmission.

---

## Quick Start

1. Copy the reviewers' comments into a text file, one `Reviewer N` heading per reviewer, numbered comments underneath (see `sample_data/reviewer_comments.md`).
2. Write your responses into a second file, one `[R{reviewer}C{comment}]` block per comment (see `sample_data/responses.txt`).
3. Run `python3 -m src.main check --comments comments.md --responses responses.txt` to confirm every comment has a response.
4. Run `python3 -m src.main build --comments comments.md --responses responses.txt --out-dir output/` to generate the letter.
5. Open `output/letter.html` (or `.md` / `.txt`) and attach it to your resubmission.

---

## How to Use It

### The Reviewer Comments File

Plain text or Markdown. Each reviewer's section starts with a line like:

```
Reviewer 1
## Reviewer #2
REVIEWER 3
```

(Any of those header styles work, case-insensitive.) Underneath, list numbered comments as `1. ...` or `1) ...`. A comment's text can continue on following lines — it ends only when the next numbered item, the next reviewer header, or the end of the file is reached. If your letter has only one reviewer and no heading at all, every numbered item is automatically attributed to "Reviewer 1."

### The Responses File

A block-marker format — no YAML, no special escaping required:

```
[R1C1]
Your response to Reviewer 1's first comment, can span
multiple lines.

[R1C2]
Your response to Reviewer 1's second comment.

[R2C1]
Your response to Reviewer 2's first comment.
```

The key `R{n}C{m}` must match the reviewer number and comment number from the comments file. Keys are case-insensitive (`[r1c1]` also works).

### `check` — Verify Completeness Before Writing Anything

```
python3 -m src.main check --comments comments.md --responses responses.txt
```

Prints how many comments are addressed, lists any comment with no response, and lists any response key that doesn't match a real comment (usually a renumbering mistake). Exits with code `0` if complete, `1` if anything is missing — safe to use as a pre-submission gate in a script.

### `build` — Generate the Letter

```
python3 -m src.main build --comments comments.md --responses responses.txt --out-dir output/
```

Writes `letter.md`, `letter.html`, and `letter.txt` to `--out-dir` (default `output/`). By default, `build` refuses to write anything if any comment is missing a response — pass `--force` to build anyway, in which case missing comments are rendered with a visible `⚠ MISSING` flag rather than being silently dropped.

### `--ai` — Optional Prose Polishing

```
ANTHROPIC_API_KEY=sk-... python3 -m src.main build --comments comments.md --responses responses.txt --ai
```

When `--ai` is passed and `ANTHROPIC_API_KEY` is set in your environment, each response is rewritten into courteous, publication-register prose by the model named in `--model` (default `claude-haiku-4-5-20251001`). The model is explicitly instructed to rephrase only — it is never allowed to add a claim, number, or citation that isn't already in your own response text. Without `--ai`, or without a key present, Counterpoint uses a deterministic formatter (capitalization, punctuation, whitespace cleanup) instead and makes **zero** network calls.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--out-dir` | `output/` | Where the three letter files are written |
| `--ai` | off | Enable Anthropic-polished prose (requires `ANTHROPIC_API_KEY`) |
| `--model` | `claude-haiku-4-5-20251001` | Model used when `--ai` is passed |
| `--force` | off | Build even if some comments are missing responses |
| `ANTHROPIC_API_KEY` (env var) | unset | Your own Anthropic API key, only read when `--ai` is passed |

To use `--ai`, install the optional dependency first: `pip install -r requirements.txt`. Without `--ai`, no third-party package is required at all — only the Python standard library.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `error: No numbered reviewer comments found...` | The comments file has no lines matching `1. ...` / `1) ...` | Check that comments are numbered, not bulleted with `-` or `*` |
| `check` reports a comment as missing that you did respond to | The `[R{n}C{m}]` key doesn't match the comment's actual reviewer/comment number | Re-check the numbering in both files line up exactly |
| `build` exits 1 immediately | Some comments have no matching response | Run `check` first to see exactly which ones, or pass `--force` to build anyway with them flagged |
| `--ai` output looks identical to your raw notes | No `ANTHROPIC_API_KEY` set, or the API call failed and fell back silently | Confirm the key is exported in your shell; failures are intentionally silent (graceful degradation), not a crash |
| `ModuleNotFoundError: No module named 'anthropic'` | You passed `--ai` without installing the optional dependency | `pip install -r requirements.txt`, or drop `--ai` |

---

## Known Limitations

- Does not cross-reference your response text against the actual manuscript (e.g. verifying "see line 45" really points to the right place) — you are trusted to describe your own changes accurately.
- No built-in journal-specific formatting templates; output is a generic, universally accepted point-by-point format.
- The completeness check only proves every comment has *a* response — it cannot judge whether a response substantively addresses the reviewer's concern.
