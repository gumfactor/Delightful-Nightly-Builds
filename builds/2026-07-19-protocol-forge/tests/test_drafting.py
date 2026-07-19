import pytest

from src import drafting
from src.checklist import run_checklist
from src.library import ProtocolLibrary
from src.models import Study
from tests.factories import make_study_dict


@pytest.fixture
def library(tmp_path):
    lib = ProtocolLibrary(tmp_path / "drafting_test.db")
    yield lib
    lib.close()


def test_template_fallback_used_when_no_api_key_and_no_reuse(library, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def _fail_if_called(*_args, **_kwargs):
        raise AssertionError("_call_anthropic must not be called when no API key is set")

    monkeypatch.setattr(drafting, "_call_anthropic", _fail_if_called)

    study = Study.from_dict(make_study_dict())
    draft = drafting.draft_section("study_summary", study, library)
    assert draft.source == "template"
    assert study.title in draft.text


def test_ai_tier_used_when_key_set_and_call_succeeds(library, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake-test-key")
    monkeypatch.setattr(drafting, "_call_anthropic", lambda prompt, api_key: "AI-drafted section text.")

    study = Study.from_dict(make_study_dict())
    draft = drafting.draft_section("procedures", study, library)
    assert draft.source == "ai"
    assert draft.text == "AI-drafted section text."


def test_ai_failure_falls_back_to_template(library, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake-test-key")
    monkeypatch.setattr(drafting, "_call_anthropic", lambda prompt, api_key: None)

    study = Study.from_dict(make_study_dict())
    draft = drafting.draft_section("data_management", study, library)
    assert draft.source == "template"


def test_call_anthropic_returns_none_on_network_error(monkeypatch):
    """_call_anthropic must degrade to None (never raise) on a network failure,
    so draft_section can fall through to the template tier. urlopen is
    monkeypatched here — this never makes a real network call."""

    def _raise_url_error(*_args, **_kwargs):
        raise drafting.urllib.error.URLError("simulated network failure")

    monkeypatch.setattr(drafting.urllib.request, "urlopen", _raise_url_error)
    result = drafting._call_anthropic("irrelevant prompt", "sk-fake")
    assert result is None


def test_call_anthropic_returns_none_on_malformed_response(monkeypatch):
    """A 200 response with no usable content should also degrade to None,
    not raise. urlopen is monkeypatched — no real network call is made."""
    import io

    class _FakeResponse(io.BytesIO):
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

    monkeypatch.setattr(
        drafting.urllib.request, "urlopen", lambda *_a, **_k: _FakeResponse(b'{"content": []}')
    )
    result = drafting._call_anthropic("irrelevant prompt", "sk-fake")
    assert result is None


def test_reuse_tier_takes_priority_over_ai_and_template(library, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake-test-key")
    monkeypatch.setattr(
        drafting,
        "_call_anthropic",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("should not reach AI tier")),
    )

    data = make_study_dict()
    data["population"]["vulnerable_groups"] = ["minors"]
    approved_study = Study.from_dict(data)
    protocol_id = library.save_protocol(
        approved_study, {"study_summary": ("Previously approved summary.", "template")}, completeness_score=100
    )
    library.approve(protocol_id)

    new_study = Study.from_dict(data)
    draft = drafting.draft_section("study_summary", new_study, library)
    assert draft.source == "reused"
    assert draft.text == "Previously approved summary."
    assert draft.source_protocol_id == protocol_id


def test_assemble_markdown_omits_vulnerable_section_when_not_applicable(library, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    study = Study.from_dict(make_study_dict())
    report = run_checklist(study)
    markdown, drafts = drafting.assemble_markdown(study, library, report)
    assert "vulnerable_populations" not in drafts
    assert "Vulnerable Populations Safeguards" not in markdown


def test_assemble_markdown_includes_vulnerable_section_when_applicable(library, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    data = make_study_dict()
    data["population"]["vulnerable_groups"] = ["minors"]
    study = Study.from_dict(data)
    report = run_checklist(study)
    markdown, drafts = drafting.assemble_markdown(study, library, report)
    assert "vulnerable_populations" in drafts
    assert "Vulnerable Populations Safeguards" in markdown


def test_assemble_markdown_includes_compliance_summary(library, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    data = make_study_dict(data_retention_years=0)
    study = Study.from_dict(data)
    report = run_checklist(study)
    markdown, _drafts = drafting.assemble_markdown(study, library, report)
    assert "Compliance Check Summary" in markdown
    assert "missing_retention_period" in markdown
    assert f"{report.completeness_score}/100" in markdown


def test_assemble_markdown_reused_section_gets_marker(library, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    data = make_study_dict()
    study = Study.from_dict(data)
    protocol_id = library.save_protocol(
        study, {"study_summary": ("Reused summary text.", "template")}, completeness_score=100
    )
    library.approve(protocol_id)

    new_study = Study.from_dict(data)
    report = run_checklist(new_study)
    markdown, drafts = drafting.assemble_markdown(new_study, library, report)
    assert f"reused from protocol #{protocol_id}" in markdown
    # the stored (raw) text for a subsequent save must stay unmarked
    assert drafts["study_summary"].text == "Reused summary text."


def test_render_stored_protocol_shows_source_tags(library):
    study = Study.from_dict(make_study_dict())
    protocol_id = library.save_protocol(
        study,
        {"study_summary": ("Summary text.", "template"), "procedures": ("Procedure text.", "ai")},
        completeness_score=88,
    )
    record = library.get_protocol(protocol_id)
    rendered = drafting.render_stored_protocol(record)
    assert "(source: template)" in rendered
    assert "(source: ai)" in rendered
    assert "88/100" in rendered
