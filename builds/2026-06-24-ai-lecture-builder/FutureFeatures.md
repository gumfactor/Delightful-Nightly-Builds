# Future Features — AI Lecture Builder

## 1. Slide Deck Export (Reveal.js or PowerPoint)
Generate a self-contained Reveal.js slide deck from the lecture outline, with one slide per outline section and key concepts on their own cards. Add a `--format slides` flag. This would make the tool deliver a complete presentation artifact, not just notes.

## 2. Batch Generation from a Course Syllabus
Accept a JSON or markdown syllabus file listing all weekly topics and generate complete lecture packages for every session in one run. Output to a numbered `week-01/`, `week-02/` folder structure. Saves a full semester's prep time.

## 3. Student-Facing Handout Mode
Add a `--handout` flag that generates a second HTML file with the quiz visible but answers hidden, the discussion questions visible, and the hook set up as a pre-class activity. Students receive the handout before class; the instructor retains the full version.

## 4. Adaptive Difficulty Calibration
Accept prior quiz performance data (`--prior-score 0.65`) and adjust the Bloom's taxonomy level of new objectives and quiz items accordingly. If the cohort scored 65% last week, shift toward more application and analysis items this week.

## 5. arXiv Integration for Real Paper Recommendations
At the end of the generation pipeline, query the arXiv API (or Semantic Scholar) for 3–5 real papers on the lecture topic, include them as a "Further Reading" section in the HTML. This adds genuine academic value and saves the instructor a PubMed search.

## 6. Claude Code Skill Packaging
Package as a `/lecture` Claude Code skill: `/lecture cortisol undergrad Stress and Coping 75`. Invoking the skill mid-session generates the HTML in the background and logs the output path to the chat. This removes the terminal step entirely and integrates directly into the teaching workflow.

## 7. Lecture History and Versioning
Store a SQLite log of every generated lecture (topic, course, level, date, output path). Add a `--list` command to browse history and a `--regenerate <id>` flag to re-run an old topic with updated context. This builds a personal library of teaching materials over time.
