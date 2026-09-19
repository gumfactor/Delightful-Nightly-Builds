import urllib.request

import briefing
from reporter_client import Project


def make_project(**overrides):
    defaults = dict(
        topic="psychopathy",
        project_num="P1",
        core_project_num="P1",
        title="Neural correlates of psychopathy",
        fiscal_year=2022,
        award_amount=250000.0,
        org_name="University of Example",
        org_city="",
        org_state="",
        org_country="",
        pi_names=["Jane Researcher"],
        agency_ic="NIMH",
        start_date=None,
        end_date=None,
    )
    defaults.update(overrides)
    return Project(**defaults)


PROJECTS = [
    make_project(project_num="P1", fiscal_year=2021, award_amount=100000.0,
                 org_name="Inst A", pi_names=["Jane Researcher"]),
    make_project(project_num="P2", fiscal_year=2022, award_amount=200000.0,
                 org_name="Inst A", pi_names=["Sam Co-PI"]),
]


def test_deterministic_fallback_no_projects():
    summary = briefing.build_topic_summary("nonexistent topic", [])
    text = briefing.deterministic_fallback(summary)
    assert "nonexistent topic" in text
    assert "No funded NIH projects" in text


def test_deterministic_fallback_reports_real_totals():
    summary = briefing.build_topic_summary("psychopathy", PROJECTS)
    text = briefing.deterministic_fallback(summary)
    assert "$300,000" in text
    assert "2 NIH-funded projects" in text
    assert "Inst A" in text


def test_generate_briefing_with_no_api_key_makes_zero_network_calls(monkeypatch):
    def forbidden_urlopen(*args, **kwargs):
        raise AssertionError("urlopen should never be called with no API key")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden_urlopen)
    result = briefing.generate_briefing("psychopathy", PROJECTS, api_key=None)
    assert "$300,000" in result


def test_generate_briefing_uses_mocked_successful_response():
    def fake_http_post(url, headers, body):
        assert url == briefing.ANTHROPIC_URL
        assert headers["x-api-key"] == "test-key"
        return {"content": [{"type": "text", "text": "A concise, grounded landscape summary."}]}

    result = briefing.generate_briefing(
        "psychopathy", PROJECTS, api_key="test-key", http_post=fake_http_post
    )
    assert result == "A concise, grounded landscape summary."


def test_generate_briefing_falls_back_on_http_post_failure():
    def failing_http_post(url, headers, body):
        raise ConnectionError("simulated network failure")

    result = briefing.generate_briefing(
        "psychopathy", PROJECTS, api_key="test-key", http_post=failing_http_post
    )
    assert "$300,000" in result  # deterministic fallback text


def test_generate_briefing_falls_back_on_empty_response_text():
    def empty_http_post(url, headers, body):
        return {"content": []}

    result = briefing.generate_briefing(
        "psychopathy", PROJECTS, api_key="test-key", http_post=empty_http_post
    )
    assert "$300,000" in result


def test_build_prompt_never_contains_any_pi_name():
    summary = briefing.build_topic_summary("psychopathy", PROJECTS)
    prompt = briefing.build_prompt(summary)
    for project in PROJECTS:
        for pi_name in project.pi_names:
            assert pi_name not in prompt


def test_build_topic_summary_excludes_pi_names_field_entirely():
    summary = briefing.build_topic_summary("psychopathy", PROJECTS)
    assert "pi_names" not in summary
    assert "principal_investigators" not in summary
