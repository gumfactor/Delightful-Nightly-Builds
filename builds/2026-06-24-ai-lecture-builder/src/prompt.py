"""Build the Anthropic API prompt for lecture package generation."""

SYSTEM_PROMPT = (
    "You are an expert university course designer specializing in psychology and neuroscience education. "
    "You generate complete, pedagogically sound lecture packages. "
    "Always respond with valid JSON only — no prose, no markdown fences, no code blocks. "
    "Start your response with { and end with }. "
    "All content must be appropriate for the specified audience level."
)

VALID_LEVELS = ("undergrad", "graduate", "mixed")
VALID_DURATIONS = (45, 50, 60, 75, 90, 120)


def build_prompt(topic: str, course: str, level: str, duration: int) -> str:
    """Return the user-turn prompt for lecture generation."""
    return f"""Generate a complete lecture package for the following:

Topic: {topic}
Course: {course}
Audience Level: {level}
Lecture Duration: {duration} minutes

Respond with ONLY a JSON object (no markdown fences, no other text) with this exact structure:
{{
  "objectives": ["Bloom's verb + measurable outcome", "..."],
  "outline": [
    {{"time_range": "0-5 min", "title": "Section title", "activity": "What happens here"}}
  ],
  "hook": "Engaging opening activity or question (150-250 words)",
  "discussion_questions": [
    {{"question": "Question text", "teaching_note": "Brief facilitation note"}}
  ],
  "quiz_items": [
    {{
      "question": "MCQ stem",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "answer": "A",
      "rationale": "Why this is correct and why distractors are plausible but wrong"
    }}
  ],
  "key_concepts": ["term: definition", "..."],
  "homework": "Reflection or application assignment (80-120 words)"
}}

Requirements:
- 3-5 learning objectives using Bloom's taxonomy verbs (analyze, evaluate, explain, apply, compare, etc.)
- Lecture outline where time ranges sum exactly to {duration} minutes; include introduction, body sections, discussion, and wrap-up
- Hook: an engaging opening question, scenario, or demonstration activity that activates prior knowledge (150-250 words)
- 8-10 discussion questions at a level appropriate for {level} students, with brief teaching notes for facilitation
- 5 multiple-choice quiz items testing key concepts; each with 4 plausible options (A–D) and rationale explaining the correct answer and why distractors are wrong
- 5-8 key concepts with concise, accurate definitions (format: "term: definition")
- One homework or reflection assignment appropriate for {level} level (80-120 words)

Tailor depth, vocabulary, and sophistication to a {level} audience."""
