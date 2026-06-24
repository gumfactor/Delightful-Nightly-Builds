"""Render lecture data to HTML (dark-mode viewer) and markdown."""

import html
import json


def _esc(text: str) -> str:
    """HTML-escape a string to prevent XSS."""
    return html.escape(str(text), quote=True)


def _safe_json(obj) -> str:
    """JSON-encode and escape angle brackets to prevent script injection via </script> in JS blocks."""
    return json.dumps(obj).replace("<", "\\u003c").replace(">", "\\u003e")


def render_html(topic: str, course: str, level: str, duration: int, data: dict) -> str:
    """Return a self-contained dark-mode HTML string for the lecture package."""
    t_topic = _esc(topic)
    t_course = _esc(course)
    t_level = _esc(level.capitalize())
    t_duration = _esc(str(duration))

    objectives_html = _render_objectives(data.get("objectives", []))
    outline_html = _render_outline(data.get("outline", []))
    hook_html = _render_hook(data.get("hook", ""))
    discussion_html = _render_discussion(data.get("discussion_questions", []))
    quiz_html = _render_quiz(data.get("quiz_items", []))
    concepts_html = _render_concepts(data.get("key_concepts", []))
    homework_html = _render_homework(data.get("homework", ""))

    tabs = [
        ("tab-objectives", "Objectives", objectives_html),
        ("tab-outline", "Outline", outline_html),
        ("tab-hook", "Hook", hook_html),
        ("tab-discussion", "Discussion", discussion_html),
        ("tab-quiz", "Quiz", quiz_html),
        ("tab-concepts", "Concepts", concepts_html),
        ("tab-homework", "Homework", homework_html),
    ]

    tab_buttons = "\n".join(
        f'<button class="tab-btn{" active" if i == 0 else ""}" '
        f'data-tab="{tab_id}" onclick="showTab(\'{tab_id}\')">{label}</button>'
        for i, (tab_id, label, _) in enumerate(tabs)
    )

    tab_panels = "\n".join(
        f'<div id="{tab_id}" class="tab-panel{" active" if i == 0 else ""}">'
        f'<div class="copy-row"><button class="copy-btn" onclick="copySection(\'{tab_id}\')">Copy</button></div>'
        f'{content}'
        f'</div>'
        for i, (tab_id, _, content) in enumerate(tabs)
    )

    safe_data = _safe_json(data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lecture: {t_topic}</title>
<style>
:root {{
  --bg: #0f1117;
  --surface: #1a1d27;
  --surface2: #242837;
  --border: #2e3347;
  --accent: #7c6ef7;
  --accent-dim: #4b47a0;
  --text: #e2e4ed;
  --text-muted: #8b91aa;
  --green: #4ade80;
  --amber: #fbbf24;
  --red: #f87171;
  --radius: 8px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  --mono: "SFMono-Regular", "Consolas", "Monaco", monospace;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 15px;
  line-height: 1.65;
  min-height: 100vh;
}}
header {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 20px 24px;
}}
.header-meta {{ color: var(--text-muted); font-size: 13px; margin-bottom: 4px; }}
.header-title {{ font-size: 22px; font-weight: 700; letter-spacing: -0.02em; }}
.header-sub {{ color: var(--text-muted); font-size: 13px; margin-top: 4px; }}
.header-actions {{ margin-top: 14px; display: flex; gap: 10px; flex-wrap: wrap; }}
.btn {{
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 14px; border-radius: var(--radius);
  border: 1px solid var(--border); background: var(--surface2);
  color: var(--text); font-size: 13px; cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}}
.btn:hover {{ background: var(--border); }}
.btn-primary {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
.btn-primary:hover {{ background: var(--accent-dim); border-color: var(--accent-dim); }}
main {{ max-width: 900px; margin: 0 auto; padding: 24px 16px; }}
.tab-bar {{
  display: flex; gap: 4px; overflow-x: auto; padding-bottom: 0;
  border-bottom: 1px solid var(--border); margin-bottom: 20px;
  scrollbar-width: none;
}}
.tab-bar::-webkit-scrollbar {{ display: none; }}
.tab-btn {{
  padding: 8px 16px; border: none; background: transparent;
  color: var(--text-muted); font-size: 14px; cursor: pointer;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
  white-space: nowrap; transition: color 0.15s, border-color 0.15s;
}}
.tab-btn:hover {{ color: var(--text); }}
.tab-btn.active {{ color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}
.copy-row {{ display: flex; justify-content: flex-end; margin-bottom: 12px; }}
.copy-btn {{
  padding: 5px 12px; border-radius: var(--radius);
  border: 1px solid var(--border); background: var(--surface2);
  color: var(--text-muted); font-size: 12px; cursor: pointer;
  transition: color 0.15s;
}}
.copy-btn:hover {{ color: var(--text); }}
.section-title {{
  font-size: 17px; font-weight: 700; margin-bottom: 16px;
  color: var(--text);
}}
ol.objectives {{ padding-left: 20px; }}
ol.objectives li {{ margin-bottom: 10px; }}
.outline-item {{
  display: grid; grid-template-columns: 100px 1fr;
  gap: 0 16px; margin-bottom: 12px;
  background: var(--surface); border-radius: var(--radius);
  padding: 12px 14px; border: 1px solid var(--border);
}}
.outline-time {{ color: var(--accent); font-size: 12px; font-family: var(--mono); font-weight: 600; padding-top: 2px; }}
.outline-title {{ font-weight: 600; margin-bottom: 4px; }}
.outline-activity {{ color: var(--text-muted); font-size: 14px; }}
.hook-box {{
  background: var(--surface); border-radius: var(--radius);
  border-left: 3px solid var(--accent); padding: 16px 18px;
  white-space: pre-wrap; line-height: 1.7;
}}
.dq-item {{
  margin-bottom: 16px; background: var(--surface);
  border-radius: var(--radius); border: 1px solid var(--border); padding: 14px 16px;
}}
.dq-num {{ color: var(--accent); font-weight: 700; font-size: 13px; margin-bottom: 6px; }}
.dq-question {{ font-weight: 500; margin-bottom: 8px; }}
.dq-note {{ color: var(--text-muted); font-size: 13px; }}
.dq-note-label {{ font-weight: 600; color: var(--amber); }}
.quiz-item {{
  margin-bottom: 20px; background: var(--surface);
  border-radius: var(--radius); border: 1px solid var(--border); padding: 16px 18px;
}}
.quiz-num {{ color: var(--accent); font-weight: 700; font-size: 13px; margin-bottom: 8px; }}
.quiz-question {{ font-weight: 500; margin-bottom: 12px; }}
.quiz-options {{ list-style: none; margin-bottom: 12px; }}
.quiz-options li {{
  padding: 8px 12px; margin-bottom: 6px;
  background: var(--surface2); border-radius: 6px;
  border: 1px solid var(--border); font-size: 14px;
}}
.quiz-options li.correct {{ border-color: var(--green); background: rgba(74,222,128,0.1); }}
.quiz-answer-btn {{
  padding: 6px 12px; border-radius: 6px;
  border: 1px solid var(--border); background: var(--surface2);
  color: var(--text-muted); font-size: 13px; cursor: pointer;
  transition: color 0.15s;
}}
.quiz-answer-btn:hover {{ color: var(--text); }}
.quiz-rationale {{
  margin-top: 12px; padding: 10px 14px;
  background: rgba(124,110,247,0.1); border-radius: 6px;
  border: 1px solid var(--accent-dim); font-size: 14px;
  display: none;
}}
.quiz-rationale.visible {{ display: block; }}
.quiz-rationale-label {{ color: var(--accent); font-weight: 700; font-size: 12px; margin-bottom: 4px; }}
.concepts-list {{ list-style: none; }}
.concepts-list li {{
  padding: 10px 14px; margin-bottom: 8px;
  background: var(--surface); border-radius: var(--radius);
  border: 1px solid var(--border); font-size: 14px;
}}
.concept-term {{ font-weight: 700; color: var(--accent); }}
.homework-box {{
  background: var(--surface); border-radius: var(--radius);
  border-left: 3px solid var(--amber); padding: 16px 18px;
  white-space: pre-wrap; line-height: 1.7;
}}
@media print {{
  .tab-bar, .copy-row, .header-actions, .quiz-answer-btn {{ display: none !important; }}
  .tab-panel {{ display: block !important; page-break-before: auto; }}
  body {{ background: #fff; color: #000; }}
}}
@media (max-width: 600px) {{
  .outline-item {{ grid-template-columns: 1fr; }}
  .outline-time {{ margin-bottom: 4px; }}
  header {{ padding: 16px; }}
}}
</style>
</head>
<body>
<header>
  <div class="header-meta" data-testid="course-meta">{t_course} &bull; {t_level} &bull; {t_duration} min</div>
  <div class="header-title" data-testid="lecture-title">{t_topic}</div>
  <div class="header-sub">Generated by AI Lecture Builder</div>
  <div class="header-actions">
    <button class="btn btn-primary" onclick="exportMarkdown()" data-testid="export-btn">Export Markdown</button>
    <button class="btn" onclick="window.print()">Print</button>
  </div>
</header>
<main>
  <div class="tab-bar" role="tablist">
{tab_buttons}
  </div>
{tab_panels}
</main>
<script>
const LECTURE_DATA = {safe_data};
const TOPIC = {_safe_json(topic)};
const COURSE = {_safe_json(course)};

function showTab(tabId) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  document.querySelector('[data-tab="' + tabId + '"]').classList.add('active');
}}

function copySection(tabId) {{
  const panel = document.getElementById(tabId);
  const text = panel.innerText
    .replace(/^Copy\\n/, '')
    .replace(/^Show Answer\\n/gm, '');
  navigator.clipboard.writeText(text.trim()).then(() => {{
    const btn = panel.querySelector('.copy-btn');
    const orig = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => {{ btn.textContent = orig; }}, 1500);
  }}).catch(() => {{}});
}}

function toggleAnswer(idx) {{
  const el = document.getElementById('rationale-' + idx);
  const btn = document.getElementById('answerBtn-' + idx);
  const item = LECTURE_DATA.quiz_items[idx];
  if (!el || !item) return;
  if (el.classList.contains('visible')) {{
    el.classList.remove('visible');
    btn.textContent = 'Show Answer';
    document.querySelectorAll('.quiz-options li').forEach(li => li.classList.remove('correct'));
  }} else {{
    el.classList.add('visible');
    btn.textContent = 'Hide Answer';
    const opts = document.querySelectorAll('#quiz-item-' + idx + ' .quiz-options li');
    const answer = item.answer;
    opts.forEach(li => {{
      if (li.dataset.opt === answer) li.classList.add('correct');
    }});
  }}
}}

function exportMarkdown() {{
  const md = buildMarkdown();
  const blob = new Blob([md], {{type: 'text/markdown'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'lecture.md';
  a.click();
  URL.revokeObjectURL(url);
}}

function buildMarkdown() {{
  const d = LECTURE_DATA;
  const lines = [];
  lines.push('# ' + TOPIC);
  lines.push('**Course:** ' + COURSE);
  lines.push('');
  if (d.objectives && d.objectives.length) {{
    lines.push('## Learning Objectives');
    d.objectives.forEach((o, i) => lines.push((i + 1) + '. ' + o));
    lines.push('');
  }}
  if (d.outline && d.outline.length) {{
    lines.push('## Lecture Outline');
    d.outline.forEach(item => {{
      lines.push('**' + (item.time_range || '') + '** — ' + (item.title || ''));
      if (item.activity) lines.push('  ' + item.activity);
    }});
    lines.push('');
  }}
  if (d.hook) {{
    lines.push('## Opening Hook');
    lines.push(d.hook);
    lines.push('');
  }}
  if (d.discussion_questions && d.discussion_questions.length) {{
    lines.push('## Discussion Questions');
    d.discussion_questions.forEach((q, i) => {{
      lines.push((i + 1) + '. ' + q.question);
      if (q.teaching_note) lines.push('   *Teaching note:* ' + q.teaching_note);
    }});
    lines.push('');
  }}
  if (d.quiz_items && d.quiz_items.length) {{
    lines.push('## Quiz Items');
    d.quiz_items.forEach((q, i) => {{
      lines.push((i + 1) + '. ' + q.question);
      const opts = q.options || {{}};
      Object.entries(opts).forEach(([k, v]) => lines.push('   ' + k + '. ' + v));
      lines.push('   **Answer:** ' + q.answer);
      if (q.rationale) lines.push('   *Rationale:* ' + q.rationale);
    }});
    lines.push('');
  }}
  if (d.key_concepts && d.key_concepts.length) {{
    lines.push('## Key Concepts');
    d.key_concepts.forEach(c => lines.push('- ' + c));
    lines.push('');
  }}
  if (d.homework) {{
    lines.push('## Homework / Reflection');
    lines.push(d.homework);
    lines.push('');
  }}
  return lines.join('\\n');
}}
</script>
</body>
</html>"""


def _render_objectives(objectives: list) -> str:
    if not objectives:
        return "<p>No objectives generated.</p>"
    items = "".join(f"<li>{_esc(obj)}</li>" for obj in objectives)
    return f'<h2 class="section-title">Learning Objectives</h2><ol class="objectives">{items}</ol>'


def _render_outline(outline: list) -> str:
    if not outline:
        return "<p>No outline generated.</p>"
    items = []
    for item in outline:
        time_range = _esc(str(item.get("time_range", "")))
        title = _esc(str(item.get("title", "")))
        activity = _esc(str(item.get("activity", "")))
        items.append(
            f'<div class="outline-item">'
            f'<div class="outline-time">{time_range}</div>'
            f'<div>'
            f'<div class="outline-title">{title}</div>'
            f'<div class="outline-activity">{activity}</div>'
            f'</div></div>'
        )
    return f'<h2 class="section-title">Lecture Outline</h2>' + "".join(items)


def _render_hook(hook: str) -> str:
    return f'<h2 class="section-title">Opening Hook</h2><div class="hook-box">{_esc(hook)}</div>'


def _render_discussion(questions: list) -> str:
    if not questions:
        return "<p>No discussion questions generated.</p>"
    items = []
    for i, q in enumerate(questions, 1):
        question = _esc(str(q.get("question", "")))
        note = _esc(str(q.get("teaching_note", "")))
        note_html = (
            f'<div class="dq-note"><span class="dq-note-label">Teaching note:</span> {note}</div>'
            if note
            else ""
        )
        items.append(
            f'<div class="dq-item">'
            f'<div class="dq-num">Q{i}</div>'
            f'<div class="dq-question">{question}</div>'
            f'{note_html}</div>'
        )
    return f'<h2 class="section-title">Discussion Questions</h2>' + "".join(items)


def _render_quiz(items: list) -> str:
    if not items:
        return "<p>No quiz items generated.</p>"
    rendered = []
    for i, item in enumerate(items):
        question = _esc(str(item.get("question", "")))
        options = item.get("options", {})
        answer = str(item.get("answer", ""))
        rationale = _esc(str(item.get("rationale", "")))

        opts_html = "".join(
            f'<li data-opt="{_esc(k)}">'
            f'<strong>{_esc(k)}.</strong> {_esc(str(v))}'
            f"</li>"
            for k, v in options.items()
        )

        rendered.append(
            f'<div class="quiz-item" id="quiz-item-{i}">'
            f'<div class="quiz-num">Question {i + 1}</div>'
            f'<div class="quiz-question">{question}</div>'
            f'<ul class="quiz-options">{opts_html}</ul>'
            f'<button class="quiz-answer-btn" id="answerBtn-{i}" onclick="toggleAnswer({i})">Show Answer</button>'
            f'<div class="quiz-rationale" id="rationale-{i}">'
            f'<div class="quiz-rationale-label">Answer: {_esc(answer)} &bull; Rationale</div>'
            f'{rationale}</div>'
            f'</div>'
        )
    return f'<h2 class="section-title">Quiz Items</h2>' + "".join(rendered)


def _render_concepts(concepts: list) -> str:
    if not concepts:
        return "<p>No key concepts generated.</p>"
    items = []
    for concept in concepts:
        text = str(concept)
        if ":" in text:
            term, _, definition = text.partition(":")
            items.append(
                f'<li><span class="concept-term">{_esc(term.strip())}</span>: {_esc(definition.strip())}</li>'
            )
        else:
            items.append(f'<li>{_esc(text)}</li>')
    return f'<h2 class="section-title">Key Concepts</h2><ul class="concepts-list">{"".join(items)}</ul>'


def _render_homework(homework: str) -> str:
    return f'<h2 class="section-title">Homework / Reflection</h2><div class="homework-box">{_esc(homework)}</div>'


def render_markdown(topic: str, course: str, level: str, duration: int, data: dict) -> str:
    """Return a flat markdown string for the lecture package."""
    lines = [f"# {topic}", f"**Course:** {course} | **Level:** {level} | **Duration:** {duration} min", ""]

    objectives = data.get("objectives", [])
    if objectives:
        lines.append("## Learning Objectives")
        for i, obj in enumerate(objectives, 1):
            lines.append(f"{i}. {obj}")
        lines.append("")

    outline = data.get("outline", [])
    if outline:
        lines.append("## Lecture Outline")
        for item in outline:
            time_range = item.get("time_range", "")
            title = item.get("title", "")
            activity = item.get("activity", "")
            lines.append(f"**{time_range}** — {title}")
            if activity:
                lines.append(f"  {activity}")
        lines.append("")

    hook = data.get("hook", "")
    if hook:
        lines.append("## Opening Hook")
        lines.append(hook)
        lines.append("")

    discussion = data.get("discussion_questions", [])
    if discussion:
        lines.append("## Discussion Questions")
        for i, q in enumerate(discussion, 1):
            lines.append(f"{i}. {q.get('question', '')}")
            note = q.get("teaching_note", "")
            if note:
                lines.append(f"   *Teaching note:* {note}")
        lines.append("")

    quiz = data.get("quiz_items", [])
    if quiz:
        lines.append("## Quiz Items")
        for i, item in enumerate(quiz, 1):
            lines.append(f"{i}. {item.get('question', '')}")
            for k, v in (item.get("options") or {}).items():
                lines.append(f"   {k}. {v}")
            lines.append(f"   Answer: {item.get('answer', '')}")
            rationale = item.get("rationale", "")
            if rationale:
                lines.append(f"   *Rationale:* {rationale}")
        lines.append("")

    concepts = data.get("key_concepts", [])
    if concepts:
        lines.append("## Key Concepts")
        for c in concepts:
            lines.append(f"- {c}")
        lines.append("")

    homework = data.get("homework", "")
    if homework:
        lines.append("## Homework / Reflection")
        lines.append(homework)
        lines.append("")

    return "\n".join(lines)
