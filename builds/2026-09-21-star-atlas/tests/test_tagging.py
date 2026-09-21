import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import tagging  # noqa: E402


def test_rule_tag_ai_ml_by_topic():
    tag, note = tagging.rule_tag("Python", ["llm", "agent"], "An LLM agent framework.")
    assert tag == "AI/ML"
    assert note == "An LLM agent framework."


def test_rule_tag_data_analytics_by_topic():
    tag, note = tagging.rule_tag("Python", ["etl", "pandas"], "ETL pipelines.")
    assert tag == "Data & Analytics"


def test_rule_tag_dev_tools_by_topic():
    tag, note = tagging.rule_tag("Go", ["cli", "productivity"], None)
    assert tag == "Dev Tools & CLI"


def test_rule_tag_web_frontend_by_topic():
    tag, note = tagging.rule_tag("TypeScript", ["react", "web"], "Chart components.")
    assert tag == "Web & Frontend"


def test_rule_tag_infra_devops_by_topic():
    tag, note = tagging.rule_tag("HCL", ["terraform", "devops"], None)
    assert tag == "Infra & DevOps"


def test_rule_tag_testing_qa_by_topic():
    tag, note = tagging.rule_tag("Python", ["pytest", "testing"], None)
    assert tag == "Testing & QA"


def test_rule_tag_docs_by_topic():
    tag, note = tagging.rule_tag(None, ["awesome-list"], None)
    assert tag == "Docs & Reference"


def test_rule_tag_falls_back_to_language_hint():
    tag, note = tagging.rule_tag("Python", [], "A generic utility.")
    assert tag == "Dev Tools & CLI"


def test_rule_tag_falls_back_to_other_when_unknown():
    tag, note = tagging.rule_tag("COBOL", [], None)
    assert tag == "Other"


def test_rule_tag_note_truncates_long_description():
    long_desc = "x" * 200
    _, note = tagging.rule_tag("Python", [], long_desc)
    assert len(note) <= 140
    assert note.endswith("...")


def test_rule_tag_note_handles_missing_description_with_topics():
    _, note = tagging.rule_tag("Python", ["llm"], None)
    assert "llm" in note


def test_rule_tag_note_handles_no_description_no_topics():
    _, note = tagging.rule_tag(None, [], None)
    assert "Untagged" in note


def test_ai_enrich_returns_rule_fallback_when_no_api_key():
    repo = {"full_name": "a/b", "description": "An LLM agent.", "language": "Python", "topics": ["llm"]}
    tag, note, source = tagging.ai_enrich(repo, api_key=None)
    assert source == "rule"
    assert tag == "AI/ML"


def test_ai_enrich_parses_successful_response():
    repo = {"full_name": "a/b", "description": "desc", "language": "Python", "topics": []}

    def fake_request(payload, api_key):
        assert api_key == "sk-test"
        assert payload["model"]
        return {"content": [{"type": "text", "text": "TAG: Data Tools | NOTE: Handy for ETL work."}]}

    tag, note, source = tagging.ai_enrich(repo, api_key="sk-test", request_fn=fake_request)
    assert source == "ai"
    assert tag == "Data Tools"
    assert note == "Handy for ETL work."


def test_ai_enrich_falls_back_on_network_error():
    import urllib.error

    repo = {"full_name": "a/b", "description": "An LLM agent.", "language": "Python", "topics": ["llm"]}

    def failing_request(payload, api_key):
        raise urllib.error.URLError("boom")

    tag, note, source = tagging.ai_enrich(repo, api_key="sk-test", request_fn=failing_request)
    assert source == "rule"
    assert tag == "AI/ML"


def test_ai_enrich_falls_back_on_malformed_reply():
    repo = {"full_name": "a/b", "description": "An LLM agent.", "language": "Python", "topics": ["llm"]}

    def malformed_request(payload, api_key):
        return {"content": [{"type": "text", "text": "not the expected format"}]}

    tag, note, source = tagging.ai_enrich(repo, api_key="sk-test", request_fn=malformed_request)
    assert source == "rule"
    assert tag == "AI/ML"


def test_ai_enrich_truncates_long_note():
    repo = {"full_name": "a/b", "description": "desc", "language": "Python", "topics": []}
    long_note = "y" * 300

    def fake_request(payload, api_key):
        return {"content": [{"type": "text", "text": f"TAG: Data Tools | NOTE: {long_note}"}]}

    _, note, source = tagging.ai_enrich(repo, api_key="sk-test", request_fn=fake_request)
    assert source == "ai"
    assert len(note) <= 200
    assert note.endswith("...")
