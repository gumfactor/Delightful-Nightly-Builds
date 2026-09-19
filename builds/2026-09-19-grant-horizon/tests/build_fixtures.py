"""Regenerates the static HTML fixtures the Playwright suite loads via file://.

Run automatically by playwright.config.js's globalSetup before every
`npx playwright test`, so the fixtures always reflect the current render.py
template rather than risking a stale, hand-committed copy drifting from it.
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

import render  # noqa: E402
from reporter_client import Project  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def make_project(**overrides) -> Project:
    defaults = dict(
        topic="psychopathy", project_num="P1", core_project_num="P1", title="Untitled",
        fiscal_year=2022, award_amount=100000.0, org_name="Inst", org_city="", org_state="",
        org_country="", pi_names=[], agency_ic="NIMH", start_date=None, end_date=None,
    )
    defaults.update(overrides)
    return Project(**defaults)


def build_normal_fixture() -> str:
    projects = [
        make_project(topic="psychopathy", project_num="P1", fiscal_year=2021, award_amount=100000.0,
                     org_name="Inst A", title="Neural correlates of psychopathy",
                     pi_names=["Jane Researcher"], agency_ic="NIMH"),
        make_project(topic="psychopathy", project_num="P2", fiscal_year=2022, award_amount=300000.0,
                     org_name="Inst B", title="Longitudinal psychopathy study",
                     pi_names=["Sam Co-PI"], agency_ic="NIDA"),
        make_project(topic="stress cortisol", project_num="P3", fiscal_year=2022, award_amount=50000.0,
                     org_name="Inst A", title="Cortisol reactivity in stress paradigms",
                     pi_names=["Dave Holt"], agency_ic="NIMH"),
    ]
    data = render.build_dashboard_data(
        projects, ["psychopathy", "stress cortisol"], 2020, 2026, "fixture-generated-at",
        briefings={"psychopathy": "A grounded test briefing paragraph."},
    )
    return render.render_dashboard(data)


def build_hostile_fixture() -> str:
    hostile_title = (
        '</script><script>window.__xss=true;</script>'
        '<img src=x onerror="window.__xss2=true">'
    )
    hostile_org = '<img src=x onerror="window.__xss3=true">'
    hostile_pi = '</script><script>window.__xss4=true;</script>'
    hostile_briefing = '</script><script>window.__xss5=true;</script>'
    projects = [make_project(
        topic="psychopathy", project_num="X1", fiscal_year=2023, award_amount=1234.0,
        title=hostile_title, org_name=hostile_org, pi_names=[hostile_pi],
    )]
    data = render.build_dashboard_data(
        projects, ["psychopathy"], 2020, 2026, "fixture-generated-at",
        briefings={"psychopathy": hostile_briefing},
    )
    return render.render_dashboard(data)


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    (FIXTURES_DIR / "dashboard_normal.html").write_text(build_normal_fixture(), encoding="utf-8")
    (FIXTURES_DIR / "dashboard_hostile.html").write_text(build_hostile_fixture(), encoding="utf-8")
    print(f"Fixtures written to {FIXTURES_DIR}")


if __name__ == "__main__":
    main()
