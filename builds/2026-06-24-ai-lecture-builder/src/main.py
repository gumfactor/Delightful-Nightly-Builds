"""AI Lecture Builder — CLI entry point."""

import argparse
import datetime
import pathlib
import sys

from client import call_api, AnthropicError
from parser import parse_response, make_slug
from prompt import SYSTEM_PROMPT, VALID_LEVELS, build_prompt
from renderer import render_html, render_markdown


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="lecture-builder",
        description="Generate a complete lecture package using AI.",
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="Lecture topic (e.g. 'cortisol and the stress response')",
    )
    parser.add_argument(
        "--course",
        required=True,
        help="Course name (e.g. 'Stress and Coping')",
    )
    parser.add_argument(
        "--level",
        required=True,
        choices=list(VALID_LEVELS),
        help="Audience level: undergrad | graduate | mixed",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=75,
        help="Lecture duration in minutes (default: 75)",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Output directory (default: output/)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Skip the API call and render a demo lecture using the provided topic/course metadata.",
    )
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if not args.topic.strip():
        raise ValueError("--topic cannot be empty.")
    if not args.course.strip():
        raise ValueError("--course cannot be empty.")
    if args.duration < 1 or args.duration > 300:
        raise ValueError(f"--duration must be between 1 and 300, got {args.duration}.")


def run(argv=None) -> int:
    args = parse_args(argv)

    try:
        validate_args(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    output_dir = pathlib.Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.date.today().isoformat()
    slug = make_slug(args.topic)
    base_name = f"{date_str}_{slug}"
    html_path = output_dir / f"{base_name}.html"
    md_path = output_dir / f"{base_name}.md"

    print(f"Generating lecture package for: {args.topic!r}")
    print(f"Course: {args.course} | Level: {args.level} | Duration: {args.duration} min")

    if args.demo:
        print("Demo mode: using sample content (no API call).")
        data = _demo_data(args.topic, args.duration)
    else:
        print("Calling Anthropic API...")
        user_prompt = build_prompt(
            topic=args.topic,
            course=args.course,
            level=args.level,
            duration=args.duration,
        )
        try:
            raw = call_api(SYSTEM_PROMPT, user_prompt)
        except AnthropicError as exc:
            print(f"Error: API call failed — {exc}", file=sys.stderr)
            return 1
        data = parse_response(raw)

    html_content = render_html(args.topic, args.course, args.level, args.duration, data)
    md_content = render_markdown(args.topic, args.course, args.level, args.duration, data)

    html_path.write_text(html_content, encoding="utf-8")
    md_path.write_text(md_content, encoding="utf-8")

    print(f"\nDone.")
    print(f"  HTML: {html_path}")
    print(f"  Markdown: {md_path}")

    return 0


def _demo_data(topic: str, duration: int) -> dict:
    """Return plausible demo lecture content for testing without an API key."""
    half = duration // 2
    return {
        "objectives": [
            f"Explain the key mechanisms underlying {topic}",
            f"Identify three real-world applications of {topic}",
            f"Evaluate current research evidence related to {topic}",
        ],
        "outline": [
            {"time_range": f"0-5 min", "title": "Introduction", "activity": "Welcome and hook activity"},
            {"time_range": f"5-{half} min", "title": f"Core concepts: {topic}", "activity": "Lecture with slides and Q&A pauses"},
            {"time_range": f"{half}-{duration - 10} min", "title": "Discussion", "activity": "Small group discussion using provided prompts"},
            {"time_range": f"{duration - 10}-{duration} min", "title": "Wrap-up", "activity": "Summary, key takeaways, and homework preview"},
        ],
        "hook": (
            f"Before we begin, take 60 seconds to write down everything you already know about {topic}. "
            "Then share with a neighbor. This activates prior knowledge and sets up the learning to come — "
            "we'll return to your notes at the end of class to see how your understanding has grown."
        ),
        "discussion_questions": [
            {"question": f"What is the most surprising thing you've learned about {topic} so far?", "teaching_note": "Open discussion — all answers valid."},
            {"question": f"How might {topic} affect everyday decision-making?", "teaching_note": "Encourage personal examples."},
            {"question": f"What are the ethical implications of applying knowledge about {topic}?", "teaching_note": "Think-pair-share."},
        ],
        "quiz_items": [
            {
                "question": f"Which of the following best describes the central finding in research on {topic}?",
                "options": {"A": "Individual differences are negligible", "B": "Context plays a significant role", "C": "The effect is purely biological", "D": "No consensus has been reached"},
                "answer": "B",
                "rationale": "Demo mode: context effects are well-documented across many domains of psychological research.",
            }
        ],
        "key_concepts": [
            f"{topic}: the central subject of today's lecture",
            "evidence-based practice: applying research findings to real-world contexts",
            "individual differences: variation in how people respond to the same stimulus",
        ],
        "homework": (
            f"Reflect on one way that {topic} has been relevant in your own life this week. "
            "Write 200–300 words connecting your personal experience to at least one concept from today's lecture. "
            "Bring your reflection to the next class — we will use these as discussion starters."
        ),
    }


if __name__ == "__main__":
    sys.exit(run())
