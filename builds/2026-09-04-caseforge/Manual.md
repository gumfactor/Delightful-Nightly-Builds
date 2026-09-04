# Manual — CaseForge

> **Version:** 1.0 (built 2026-09-04)
> **Complexity:** Ambitious Project

---

## What This Is

CaseForge turns real, live PubMed research into ready-to-teach classroom discussion cases. Give it a course name and a search topic, and it fetches real published abstracts, extracts real methodological facts from them (sample size, effect size, p-value, methodology, population), and builds a case for each one — a short narrative, a real citation, and a set of discussion questions that are only ever generated when the extracted facts actually justify them (a small-sample study gets a power question; a correlational study gets a causality question; a study with no stated control group gets a confound question). Nothing is invented — every number in a case traces back to something the tool actually found in a real abstract, and that stays true even if you turn on the optional AI-polish pass.

---

## Quick Start

1. Make sure you have Python 3 installed (no other install step is required — the CLI uses only the standard library).
2. Open a terminal in `builds/2026-09-04-caseforge/`.
3. Generate your first batch of cases:
   ```bash
   python -m src.main generate --course "Stress and Coping" --query "cortisol stress reactivity coping"
   ```
4. List and view them:
   ```bash
   python -m src.main list
   python -m src.main show <pmid>
   ```
5. Get a shareable view:
   ```bash
   python -m src.main render --out cases.html
   ```
   Then open `cases.html` in any browser.

---

## How to Use It

### `generate` — fetch real articles and build cases

```bash
python -m src.main generate --course "<name>" --query "<PubMed search terms>" [--n 3] [--ai-polish] [--register undergrad|graduate|public] [--force]
```

- `--course` (required) — any label you want to group cases under (e.g. a specific course, unit, or seminar topic). Not restricted to a fixed list.
- `--query` (required) — the actual PubMed search terms. Write it the way you'd search PubMed directly — a few keywords work better than a full sentence.
- `--n` — how many cases to generate (default 3, max 50). CaseForge searches for more than `n` results and skips any PMID already in your library, so re-running the same query later naturally finds new articles instead of repeating old ones.
- `--ai-polish` — optional. Requires `ANTHROPIC_API_KEY` set in your shell environment. Rewrites the deterministic vignette into smoother prose for the audience register you choose. **Every number the deterministic pass extracted must still appear, verbatim, in the AI's rewrite, or CaseForge silently keeps the deterministic version instead** — this is checked automatically every time, not something you need to verify by hand.
- `--register` — `undergrad` (default), `graduate`, or `public`. Only affects the AI-polish prompt.
- `--force` — re-fetch and overwrite a case even if its PMID is already in your library.

### `list` — see what's in your library

```bash
python -m src.main list [--course "<name>"]
```

### `show` — read one case in full

```bash
python -m src.main show <pmid>
```
Prints the title, citation, every extracted fact, the full vignette (and whether it's the deterministic or AI-polished version), and all discussion questions.

### `search` — find cases by keyword

```bash
python -m src.main search "<keyword>"
```
Matches against title, abstract text, and course name.

### `export markdown` — get a handout-ready file

```bash
python -m src.main export markdown [--course "<name>"] [--out cases.md]
```
Without `--out`, prints to the terminal instead of writing a file.

### `render` — the browsable dashboard

```bash
python -m src.main render [--out cases.html]
```
Produces a single self-contained HTML file — no server, no build step. Open it directly in a browser. It has a live search box, per-course tabs, and a print-friendly layout for handouts (use your browser's Print function).

### Using it inside a Claude Code session

A companion Skill lives at `skill/SKILL.md`. Copy it into your `.claude/skills/` directory and you can ask a Claude Code session to "build me 3 discussion cases on empathy and psychopathy for my seminar" and it will run the CLI on your behalf.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ANTHROPIC_API_KEY` (env var) | unset | Enables `--ai-polish`. Without it, every case is built by the deterministic assembler and `generate` makes zero calls to any AI service. |
| `--n` | 3 | Number of new cases to generate per `generate` call (1–50). |
| `--register` | `undergrad` | Audience register for AI-polished prose (`undergrad` / `graduate` / `public`). |

The local library lives in `caseforge.db` (SQLite) inside this build folder, created automatically on first run. It is not committed to git — it's yours, and it grows every time you `generate`.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `error: PubMed search failed: ...` | No internet access, or PubMed is temporarily unreachable | Check your connection and retry; this tool needs to reach `eutils.ncbi.nlm.nih.gov` directly (no API key required) |
| `No new articles found for this query` | Every matching PMID is already in your library | Try a more specific or different `--query`, or add `--force` to re-fetch and refresh existing cases |
| A case has few or no methodology/effect-size badges | The abstract genuinely didn't state that information explicitly, or phrased it in a way the extractor doesn't recognize | This is intentional — CaseForge never guesses a number it can't find; the case still ships with its 3 fallback discussion questions |
| `--ai-polish` cases still show `vignette_source: deterministic` | Either `ANTHROPIC_API_KEY` isn't set, the API call failed, or the AI's rewrite dropped a required fact and was rejected by the safety check | Check that the environment variable is set correctly; a rejected AI rewrite is expected behavior, not a bug |

---

## Known Limitations

- Facts are extracted from the abstract only — PubMed's free API does not provide full-text access, so a claim made only in the paper's results or discussion section (and not the abstract) will not be captured.
- Extraction is deterministic and pattern-based, not a language model — a study that reports its key statistic in unusual phrasing (e.g. "the correlation was moderate" with no `r =` value stated) will not have that fact extracted.
- The methodology tag reports only the single best-matching design per abstract, even for studies that genuinely combine methods.
- This build's own container blocks outbound calls to PubMed during development (confirmed live this session with a genuine `403 Forbidden`); it was validated with realistic mocked PubMed responses and is designed to run against the real API on your own machine, where PubMed is freely reachable.
