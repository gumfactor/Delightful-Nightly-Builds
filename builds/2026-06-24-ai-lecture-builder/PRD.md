# PRD — AI Lecture Builder

## Goal

A Python CLI that accepts a lecture topic, course context, and duration, calls the Anthropic API to generate a complete pedagogically-structured lecture package, and saves it as a self-contained dark-mode HTML viewer and a markdown file ready to paste into a LMS.

## User Story

As a professor teaching 3 psychology/neuroscience courses, I spend 2–3 hours per lecture creating outlines, discussion questions, quiz items, and slide structure from scratch. I want to describe a topic in one command and receive a complete, publication-ready lecture package I can review and refine, rather than writing every section manually.

## Scope

### In Scope
- CLI with `--topic`, `--course`, `--level`, `--duration` arguments
- Anthropic API call (claude-sonnet-4-6) generating structured JSON lecture package
- HTML output: dark-mode viewer with tabbed sections, copy-to-clipboard, print support
- Markdown output: flat .md file for LMS paste
- Sections: learning objectives, timed outline, opening hook, discussion questions (with teaching notes), MCQ quiz items (with answers and rationale), key concepts, homework prompt
- Graceful error handling: API key missing, API failure, JSON parse failure
- Deterministic output path: `output/YYYY-MM-DD_topic-slug.html` and `.md`

### Out of Scope
- Web server / browser-based input form (use CLI for input)
- Saving lecture history or database
- Real-time streaming of the API response
- Slide deck generation (PowerPoint / Reveal.js)
- LMS API integration (Canvas, Blackboard, Brightspace)

## Tech Stack

- **Runtime:** Python 3.8+ stdlib only — `urllib.request`, `json`, `html`, `argparse`, `pathlib`, `datetime`, `os`, `re`
- **Anthropic API:** direct `urllib.request` call with `x-api-key` header (no `anthropic` package)
- **Model:** `claude-sonnet-4-6` for high-quality structured generation
- **Tests — backend:** pytest
- **Tests — frontend:** Playwright (`@playwright/test@1.56.1`, chromium at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`)
- **Frontend:** Vanilla HTML5/CSS3/ES6, inline styles and scripts, no external CDN

## Data Structure

### Anthropic API JSON Response Schema
```json
{
  "objectives": ["Bloom's verb + measurable outcome", ...],
  "outline": [
    {"time_range": "0-5 min", "title": "Section title", "activity": "What happens here"}
  ],
  "hook": "Engaging opening activity or question (150-250 words)",
  "discussion_questions": [
    {"question": "Question text", "teaching_note": "Brief facilitation note"}
  ],
  "quiz_items": [
    {
      "question": "MCQ stem",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "answer": "A",
      "rationale": "Why this is correct and why distractors are wrong"
    }
  ],
  "key_concepts": ["term: definition", ...],
  "homework": "Reflection or application assignment (80-120 words)"
}
```

### Output Files
- `output/YYYY-MM-DD_topic-slug.html` — self-contained dark-mode HTML viewer
- `output/YYYY-MM-DD_topic-slug.md` — flat markdown

## Folder Structure

```
builds/2026-06-24-ai-lecture-builder/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── playwright.config.js
├── src/
│   ├── main.py          ← CLI entry point
│   ├── prompt.py        ← prompt building
│   ├── parser.py        ← API response parsing and validation
│   ├── renderer.py      ← HTML + markdown generation
│   └── client.py        ← Anthropic API call via urllib
├── tests/
│   ├── test_prompt.py
│   ├── test_parser.py
│   ├── test_renderer.py
│   ├── test_cli.py
│   ├── lecture.spec.js  ← Playwright UI tests
│   └── fixtures/
│       └── sample.html  ← pre-rendered fixture for Playwright
└── output/              ← generated files land here (git-ignored)
```

## Testing Strategy

### pytest (backend logic, no real API calls)
- `test_prompt.py` — prompt construction for all level/duration combinations; includes topic, course, duration in output
- `test_parser.py` — valid JSON parsing, missing-key fallbacks, malformed JSON recovery, all 7 sections extracted, rationale included in quiz items
- `test_renderer.py` — DOCTYPE present, XSS escaping in topic/course, all section tabs generated, objectives in HTML, quiz A/B/C/D options, hook content, homework section, key concepts, markdown output structure
- `test_cli.py` — missing required arguments, invalid level value, valid args pass validation, topic slug generation from topic text

### Playwright (HTML viewer UI — opens `tests/fixtures/sample.html`)
- Page loads with correct title, course header displayed
- All 7 section tabs visible and labelled
- Default tab (Objectives) shows content
- Clicking each tab shows its content
- Quiz items display all 4 options (A/B/C/D)
- "Show Answer" button reveals correct answer and rationale
- Copy button visible per section
- Export markdown button present and fires download
- Page does not break at 375px viewport (mobile-responsive)
- Section content is non-empty (validates fixture has data)

## Success Criteria

1. `python src/main.py --topic "cortisol and the stress response" --course "Stress and Coping" --level undergrad --duration 75` completes without error, produces `output/YYYY-MM-DD_cortisol-and-the-stress-response.html` and `.md`
2. The HTML output contains all 7 sections: objectives, outline, hook, discussion questions, quiz items, key concepts, homework
3. Quiz items include the correct answer and rationale (not just the question and options)
4. HTML output is XSS-safe — topic and course names with `<script>` injection are escaped before rendering
5. All 15+ tests pass with zero failures
