# Manual — CiteForge

## What it is

A Python CLI that converts a bibliography into a correctly-formatted, submission-ready reference list in **APA 7**, **AMA 11**, **Vancouver/ICMJE**, or **Chicago Author-Date 17** style — and can print all four side by side, or produce a self-contained HTML comparison report with per-entry copy buttons.

## Requirements

- Python 3.11+, no third-party packages needed to run (stdlib only)
- `pip install -r requirements.txt` only if you want to run the test suite (installs `pytest`)

## Quick start

```bash
cd builds/2026-09-02-citeforge

# 1. Import references — pick any/all of these:
python main.py add-bibtex my-refs.bib                # from a BibTeX file
python main.py add-doi 10.1037/ppm0000185             # from a single DOI (Crossref lookup)
python main.py add-doi dois.txt                       # from a file of DOIs, one per line
python main.py add-text pasted-refs.txt                # from free-text reference lines
python main.py add-text pasted-refs.txt --ai           # ...with Claude Haiku for lines regex can't structure

# 2. See what's in the library
python main.py list

# 3. Format it
python main.py format --style apa
python main.py format --style ama
python main.py format --style vancouver
python main.py format --style chicago

# 4. Compare all 4 styles side by side (terminal)
python main.py compare

# 5. Produce a browsable, copyable HTML report
python main.py render -o report.html
```

Every command accepts `--db <path>` (default `citeforge.db` in the current directory) to point at a specific library file — use a fresh path per project/manuscript, or one persistent path for an ongoing personal bibliography.

Use `--ids 1,3,5` on `format`/`compare`/`render` to work with a subset of the library instead of everything.

## The `--ai` flag on `add-text`

`add-text` first tries a deterministic regex pass on each line (looks for a `(Year)`, a `"Quoted Title"`, and a leading author list). If that pass can't confidently fill in both a year and a title, and `--ai` is passed with `ANTHROPIC_API_KEY` set in the environment, the raw line is sent to Claude Haiku with a strict extraction prompt and only the reference text itself (no other context) leaves your machine. A line neither pass can structure is stored flagged `NEEDS_REVIEW` rather than guessed — check `list`/`render` output for that flag and fix those entries by hand (`add-text` again with a cleaner line, or edit the source `.bib`).

## Known limitations (documented, not bugs)

- **Journal abbreviations**: AMA and Vancouver technically use NLM-style abbreviated journal names (e.g. "N Engl J Med"). CiteForge prints whatever journal name your source data provides — abbreviate it yourself first if your target journal requires it.
- **Sentence-case proper nouns**: The sentence-case converter (used by APA/AMA/Vancouver titles) can't detect ordinary capitalized words as proper nouns without a name dictionary — it preserves acronyms (`HIV`, `DNA`) and internally-capitalized words (`McDonald`, `mRNA`), but a plain proper noun like "United States" gets lowercased along with the rest of the sentence. Fix by hand if it matters for your submission.
- **Chicago place-of-publication and month**: not tracked in the reference model, so both are omitted rather than fabricated.
- **AMA/Vancouver numbered in-text citations**: numbered by library (import) order, not by where they'd actually appear in your manuscript — CiteForge doesn't scan a manuscript file.
- **Reference types**: only `journal-article`, `book`, and `webpage` have dedicated templates. Other BibTeX types (`@inproceedings`, etc.) fall back to a generic template.

## Running the tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Using it from a Claude Code session

A companion Skill lives at `skill/SKILL.md` — copy it into `.claude/skills/cite-format/` in a project where you want to say "format these references in AMA" mid-session.
