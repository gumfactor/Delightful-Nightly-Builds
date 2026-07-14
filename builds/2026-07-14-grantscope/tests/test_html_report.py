import html_report


def make_topic(key="empathy", label="Empathy", projects=None, briefing_text="Summary text.", briefing_source="template"):
    projects = projects if projects is not None else []
    return {
        "key": key,
        "label": label,
        "projects": projects,
        "funding_by_year": {2024: {"total_amount": 100000, "count": 1}} if projects else {},
        "top_institutes": [("NIMH", {"total_amount": 100000, "count": 1})] if projects else [],
        "top_organizations": [("Big State University", {"total_amount": 100000, "count": 1})] if projects else [],
        "mechanisms": {"R01": 1} if projects else {},
        "keywords": [("empathy", 3)],
        "stats": {
            "project_count": len(projects),
            "total_amount": sum(p.get("award_amount", 0) for p in projects),
            "fiscal_year_range": (2024, 2024) if projects else (None, None),
            "distinct_institutes": 1 if projects else 0,
            "distinct_organizations": 1 if projects else 0,
        },
        "briefing": {"text": briefing_text, "source": briefing_source},
    }


def sample_project(**overrides):
    base = {
        "project_num": "P1",
        "topic": "empathy",
        "title": "Neural correlates of empathy",
        "abstract": "abstract text",
        "pi_name": "Jane Smith",
        "org_name": "Big State University",
        "org_city": "Springfield",
        "org_state": "IL",
        "ic_admin": "NIMH",
        "activity_code": "R01",
        "award_amount": 100000,
        "fiscal_year": 2024,
        "project_start": "2022-05-01",
        "project_end": "2027-04-30",
    }
    base.update(overrides)
    return base


def test_render_includes_page_title_and_topic_labels():
    topics_data = [make_topic(key="empathy", label="Empathy & Prosocial Neuroscience", projects=[sample_project()])]
    output = html_report.render_dashboard(topics_data, "2026-07-14 09:00 UTC")
    assert "GrantScope" in output
    assert "Empathy &amp; Prosocial Neuroscience" in output
    assert "2026-07-14 09:00 UTC" in output


def test_render_includes_chartjs_cdn_reference():
    output = html_report.render_dashboard([make_topic()], "2026-07-14 09:00 UTC")
    assert "chart.js@4.4.4" in output


def test_render_embeds_project_data_as_json():
    topics_data = [make_topic(projects=[sample_project(title="A Special Title")])]
    output = html_report.render_dashboard(topics_data, "2026-07-14 09:00 UTC")
    assert "A Special Title" in output
    assert 'id="grantscope-data"' in output


def test_render_escapes_script_injection_in_project_title():
    malicious_title = "<script>alert('xss')</script>"
    topics_data = [make_topic(projects=[sample_project(title=malicious_title)])]
    output = html_report.render_dashboard(topics_data, "2026-07-14 09:00 UTC")
    # A raw, unescaped "</script>" sourced from project data must never appear in the
    # output, since that would let the embedded JSON payload break out of its <script>
    # block early and have the remainder of the payload parsed as live HTML.
    assert "xss')</script>" not in output
    assert "xss')<\\/script>" in output


def test_render_handles_empty_topic_list():
    output = html_report.render_dashboard([], "2026-07-14 09:00 UTC")
    assert "GrantScope" in output
    assert "Overview" in output


def test_render_handles_topic_with_no_projects():
    topics_data = [make_topic(key="stress_coping", label="Stress & Coping", projects=[])]
    output = html_report.render_dashboard(topics_data, "2026-07-14 09:00 UTC")
    assert "Stress &amp; Coping" in output
    assert "panel-stress_coping" in output


def test_render_includes_briefing_source_attribute():
    topics_data = [make_topic(briefing_source="ai", briefing_text="AI generated text")]
    output = html_report.render_dashboard(topics_data, "2026-07-14 09:00 UTC")
    assert 'data-source="ai"' in output


def test_aggregate_overview_sums_across_topics():
    topics_data = [
        make_topic(key="empathy", projects=[sample_project(project_num="P1", award_amount=100000)]),
        make_topic(key="stress_coping", projects=[sample_project(project_num="P2", award_amount=200000)]),
    ]
    overview = html_report._aggregate_overview(topics_data)
    assert overview["project_count"] == 2
    assert overview["total_amount"] == 300000


def test_aggregate_overview_handles_zero_topics():
    overview = html_report._aggregate_overview([])
    assert overview["project_count"] == 0
    assert overview["total_amount"] == 0


def test_render_produces_valid_looking_html_document():
    output = html_report.render_dashboard([make_topic()], "2026-07-14 09:00 UTC")
    assert output.strip().startswith("<!doctype html>")
    assert "</html>" in output


def test_render_distinguishes_no_data_from_no_search_results():
    # renderTable() must accept a distinct empty-state message for "search matched
    # nothing" vs. "topic has no synced data yet" — verified live in headless
    # Chromium during manual verification (see BUILD_LOG.md). This checks the
    # client-side logic that produces that distinction is present in the output.
    output = html_report.render_dashboard([make_topic(projects=[sample_project()])], "2026-07-14 09:00 UTC")
    assert "No projects match your search." in output
    assert 'function renderTable(tableId, projects, emptyMessage)' in output
