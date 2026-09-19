import csv
import io
import json
import re

import pytest

import render
from reporter_client import Project


def make_project(**overrides):
    defaults = dict(
        topic="psychopathy",
        project_num="P1",
        core_project_num="P1",
        title="Untitled",
        fiscal_year=2022,
        award_amount=0.0,
        org_name="Inst",
        org_city="",
        org_state="",
        org_country="",
        pi_names=[],
        agency_ic="Agency",
        start_date=None,
        end_date=None,
    )
    defaults.update(overrides)
    return Project(**defaults)


FIXTURE = [
    make_project(topic="psychopathy", project_num="P1", fiscal_year=2021, award_amount=100000.0,
                 org_name="Inst A"),
    make_project(topic="psychopathy", project_num="P2", fiscal_year=2022, award_amount=200000.0,
                 org_name="Inst B"),
    make_project(topic="stress cortisol", project_num="P3", fiscal_year=2022, award_amount=50000.0,
                 org_name="Inst A"),
]


def test_build_dashboard_data_hero_totals_match_fixture():
    data = render.build_dashboard_data(
        FIXTURE, ["psychopathy", "stress cortisol"], 2020, 2026, "2026-09-19 00:00 UTC"
    )
    assert data["hero"]["total_funding"] == 350000.0
    assert data["hero"]["total_projects"] == 3
    assert data["hero"]["topic_count"] == 2


def test_build_dashboard_data_per_topic_totals():
    data = render.build_dashboard_data(
        FIXTURE, ["psychopathy", "stress cortisol"], 2020, 2026, "2026-09-19 00:00 UTC"
    )
    by_topic = {row["topic"]: row for row in data["topics"]}
    assert by_topic["psychopathy"]["total_funding"] == 300000.0
    assert by_topic["psychopathy"]["project_count"] == 2
    assert by_topic["stress cortisol"]["total_funding"] == 50000.0


def test_build_dashboard_data_top_institutions_ranked():
    data = render.build_dashboard_data(
        FIXTURE, ["psychopathy", "stress cortisol"], 2020, 2026, "2026-09-19 00:00 UTC"
    )
    names = [row["name"] for row in data["top_institutions"]]
    # Inst B: $200k (P2 alone). Inst A: $100k (P1) + $50k (P3) = $150k. Inst B ranks first.
    assert names[0] == "Inst B"
    assert data["top_institutions"][0]["total"] == 200000.0
    assert names[1] == "Inst A"
    assert data["top_institutions"][1]["total"] == 150000.0


def test_build_dashboard_data_hero_dedupes_award_matched_by_multiple_topics():
    same_award = [
        make_project(topic="psychopathy", project_num="X1", fiscal_year=2022, award_amount=500000.0,
                     org_name="Shared Inst"),
        make_project(topic="affective neuroscience", project_num="X1", fiscal_year=2022, award_amount=500000.0,
                     org_name="Shared Inst"),
    ]
    data = render.build_dashboard_data(
        same_award, ["psychopathy", "affective neuroscience"], 2020, 2026, "2026-09-19 00:00 UTC"
    )
    # Hero counts the underlying award once, not once per topic it matched.
    assert data["hero"]["total_funding"] == 500000.0
    assert data["hero"]["total_projects"] == 1
    assert data["top_institutions"] == [{"name": "Shared Inst", "total": 500000.0, "count": 1}]
    # But each topic still legitimately shows the award in its own per-topic total.
    by_topic = {row["topic"]: row for row in data["topics"]}
    assert by_topic["psychopathy"]["total_funding"] == 500000.0
    assert by_topic["affective neuroscience"]["total_funding"] == 500000.0
    # And the raw project table still lists both topic-matches (each correctly labeled).
    assert len(data["projects"]) == 2


def test_build_dashboard_data_includes_briefing_text():
    data = render.build_dashboard_data(
        FIXTURE, ["psychopathy"], 2020, 2026, "2026-09-19 00:00 UTC",
        briefings={"psychopathy": "A grounded briefing paragraph."},
    )
    assert data["topics"][0]["briefing"] == "A grounded briefing paragraph."


def test_embed_json_neutralizes_script_close_and_round_trips():
    payload = {"title": "</script><script>window.__xss=true;</script>"}
    embedded = render._embed_json(payload)
    assert "</script" not in embedded
    recovered = json.loads(embedded)
    assert recovered == payload


def test_render_dashboard_hostile_title_never_breaks_out_of_script_block():
    hostile = "</script><script>window.__xss=true;</script>"
    hostile_projects = [make_project(topic="psychopathy", project_num="P1", title=hostile)]
    data = render.build_dashboard_data(
        hostile_projects, ["psychopathy"], 2020, 2026, "2026-09-19 00:00 UTC"
    )
    html = render.render_dashboard(data)

    # Exactly the page's own 3 legitimate closing script tags remain.
    assert len(re.findall(r"</script", html, flags=re.IGNORECASE)) == 3
    assert "window.__xss=true" not in html or "<\\/script" in html


def test_render_dashboard_json_payload_recovers_hostile_title_exactly():
    hostile = "</script><script>window.__xss=true;</script>"
    hostile_projects = [make_project(topic="psychopathy", project_num="P1", title=hostile)]
    data = render.build_dashboard_data(
        hostile_projects, ["psychopathy"], 2020, 2026, "2026-09-19 00:00 UTC"
    )
    html = render.render_dashboard(data)
    match = re.search(
        r'<script type="application/json" id="data-payload">(.*?)</script>', html, flags=re.DOTALL
    )
    assert match is not None
    recovered = json.loads(match.group(1))
    recovered_title = recovered["projects"][0]["title"]
    assert recovered_title == hostile


def test_render_dashboard_never_uses_innerhtml():
    data = render.build_dashboard_data(FIXTURE, ["psychopathy"], 2020, 2026, "2026-09-19 00:00 UTC")
    html = render.render_dashboard(data)
    assert "innerHTML" not in html


def test_render_projects_csv_header():
    csv_text = render.render_projects_csv(FIXTURE)
    header = next(csv.reader(io.StringIO(csv_text)))
    assert header == [
        "topic", "project_num", "core_project_num", "title", "fiscal_year",
        "award_amount", "org_name", "org_city", "org_state", "org_country",
        "pi_names", "agency_ic", "start_date", "end_date",
    ]


def test_render_projects_csv_quotes_comma_in_title_and_round_trips():
    projects = [make_project(project_num="P1", title="Stress, cortisol, and coping")]
    csv_text = render.render_projects_csv(projects)
    rows = list(csv.reader(io.StringIO(csv_text)))
    assert rows[1][3] == "Stress, cortisol, and coping"


@pytest.mark.parametrize("leading_char", ["=", "+", "-", "@", "\t", "\r"])
def test_csv_safe_neutralizes_formula_injection_leading_characters(leading_char):
    dangerous = f"{leading_char}cmd|'/bin/calc'!A1"
    safe = render._csv_safe(dangerous)
    assert safe.startswith("'")
    assert safe == "'" + dangerous


def test_csv_safe_leaves_ordinary_text_untouched():
    assert render._csv_safe("Neural correlates of psychopathy") == "Neural correlates of psychopathy"
    assert render._csv_safe("") == ""


def test_render_projects_csv_neutralizes_hostile_title_and_institution():
    projects = [make_project(
        project_num="P1",
        title="=cmd|'/bin/calc'!A1",
        org_name="+SUM(A1:A9)",
    )]
    csv_text = render.render_projects_csv(projects)
    rows = list(csv.reader(io.StringIO(csv_text)))
    assert rows[1][3] == "'=cmd|'/bin/calc'!A1"
    assert rows[1][6] == "'+SUM(A1:A9)"
