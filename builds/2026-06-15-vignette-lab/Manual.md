# Manual — Vignette Lab

A command-line tool that generates psychological scenario vignettes for research
stimuli and classroom exercises. Output is print-ready markdown.

---

## Quick Start

```bash
# Run from the build folder
cd builds/2026-06-15-vignette-lab

# List available themes
python3 main.py list

# Generate 5 stress vignettes, print to terminal
python3 main.py generate --theme stress --count 5

# Generate 10 empathy vignettes, save to files
python3 main.py generate --theme empathy --count 10 --output my_study

# Reproducible batch (same seed = same output)
python3 main.py generate --theme moral --count 8 --seed 42 --output pilot_vignettes

# Print researcher version (with manipulation checks) to terminal
python3 main.py generate --theme stress --count 3 --researcher
```

---

## Available Themes

| Theme    | Label                | Designed to measure |
|----------|----------------------|---------------------|
| `stress` | Acute Stress Induction | Perceived stress, threat appraisal, coping self-efficacy |
| `empathy` | Empathy Elicitation  | Affective and cognitive empathy, pro-social motivation |
| `moral`  | Moral Dilemma        | Moral judgment, bystander intervention, ethical reasoning |

Each theme has 10 characters × 6 settings × 8 events ≈ 480 unique combinations.

---

## Command Reference

### `list`
```
python3 main.py list
```
Displays all available themes with their labels, descriptions, and element counts.

---

### `generate`
```
python3 main.py generate --theme THEME [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--theme` | *(required)* | `stress`, `empathy`, or `moral` |
| `--count N` | 5 | Number of vignettes to generate |
| `--seed N` | *(random)* | Integer seed for reproducible output |
| `--output PREFIX` | *(stdout)* | Save to `PREFIX_participant.md` and `PREFIX_researcher.md` |
| `--researcher` | off | When printing to stdout, include manipulation checks and notes |

---

## Output Files

When `--output PREFIX` is specified, two files are written:

### `PREFIX_participant.md`
- Numbered vignette narratives
- Response prompt per vignette
- **No** manipulation checks or researcher notes
- Ready to paste into Qualtrics, Google Forms, or course materials

### `PREFIX_researcher.md`
- Everything in the participant version, plus:
- Character metadata (name, age, role)
- Two manipulation check questions per vignette
- One-time theme note with design rationale at the top

---

## Using in Research

**Qualtrics import:**
Copy vignette text blocks from `_participant.md` into Qualtrics Display Logic text
elements. Paste manipulation check questions as separate MC items immediately following.

**Seeding for reproducibility:**
Use `--seed N` to lock the random selection. Record the seed in your pre-registration
or methods section so the exact vignette set can be reproduced.

**Character de-duplication:**
Within a batch, each character is not reused until all 10 characters have appeared once.
For batches larger than 10, characters cycle in a newly shuffled order.

**Pilot review:**
Generated vignettes are starting-point drafts. Review each for:
- Internal consistency (setting + event should co-occur naturally)
- Population fit (character age/role should match your target sample)
- Manipulation strength (event should achieve the intended psychological effect)

---

## Running Tests

```bash
# From the build folder
python -m pytest tests/ -v
```

Expected output: **29 passed**, 0 failed.

Tests cover: generation logic, reproducibility, character cycling, error handling,
markdown formatting (participant and researcher versions), and edge cases.
