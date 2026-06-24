# Manual — AI Lecture Builder

## Overview

AI Lecture Builder generates a complete lecture package from a topic description using the Anthropic API (Claude). Given a topic, course context, audience level, and duration, it produces:

- A self-contained dark-mode HTML viewer with 7 tabbed sections
- A markdown file ready to paste into a LMS or notes system

## Requirements

- Python 3.8+ (stdlib only — no pip install required at runtime)
- `ANTHROPIC_API_KEY` environment variable set

## Usage

```bash
python src/main.py \
  --topic "cortisol and the stress response" \
  --course "Stress and Coping" \
  --level undergrad \
  --duration 75
```

Output files:
- `output/YYYY-MM-DD_cortisol-and-the-stress-response.html`
- `output/YYYY-MM-DD_cortisol-and-the-stress-response.md`

Open the HTML file in any browser — no server required.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--topic` | Yes | — | Lecture topic (free text) |
| `--course` | Yes | — | Course name |
| `--level` | Yes | — | `undergrad`, `graduate`, or `mixed` |
| `--duration` | No | `75` | Duration in minutes (1–300) |
| `--output` | No | `output` | Output directory |
| `--demo` | No | off | Skip API call; render a demo lecture for testing |

## Generated Sections

| Tab | Contents |
|-----|---------|
| Objectives | 3–5 learning objectives using Bloom's taxonomy verbs |
| Outline | Timed lecture outline summing to the specified duration |
| Hook | 150–250 word opening activity or scenario |
| Discussion | 8–10 discussion questions with teaching notes |
| Quiz | 5 MCQ items with A–D options, correct answer, and rationale |
| Concepts | 5–8 key terms with definitions |
| Homework | One reflection or application assignment |

## HTML Viewer Features

- **Tab navigation:** Click any tab to switch sections
- **Copy button:** Each section has a one-click Copy button
- **Show Answer:** Reveals the correct option and rationale for each quiz item
- **Export Markdown:** Downloads a flat `.md` file from the browser
- **Print:** Use the Print button or Ctrl+P — tabs are expanded, UI chrome hidden
- **Mobile-responsive:** Works on narrow screens

## Example Workflows

### Quick lecture prep
```bash
python src/main.py \
  --topic "empathy and the mirror neuron system" \
  --course "Social Affective Neuroscience" \
  --level graduate \
  --duration 90
```

### Course material batch
```bash
for TOPIC in "amygdala and fear" "hippocampus and memory" "prefrontal cortex and decision making"; do
  python src/main.py --topic "$TOPIC" --course "Introduction to Neuroscience" --level undergrad --duration 50
done
```

### Demo / dry run (no API key needed)
```bash
python src/main.py --topic "stress and the brain" --course "Stress and Coping" --level undergrad --demo
```

## Running Tests

```bash
# Python backend tests (84 tests)
python -m pytest tests/ -v

# UI tests (23 Playwright tests)
npx playwright test
```

## API and Cost Notes

- Model: `claude-sonnet-4-6` (generates structured JSON in one call)
- Typical token usage: ~200 input tokens + ~1500 output tokens per lecture
- Generation time: 15–30 seconds depending on network and load
- The `ANTHROPIC_API_KEY` is read from the environment — never hardcoded

## Output File Naming

Files are named `YYYY-MM-DD_topic-slug.html` and `.md`, where the slug is the topic text lowercased and punctuation-stripped. Running the same topic twice on the same day overwrites the previous output.
