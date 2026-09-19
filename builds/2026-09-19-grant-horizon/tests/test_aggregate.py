import aggregate
from reporter_client import Project


def make_project(**overrides):
    defaults = dict(
        topic="psychopathy",
        project_num="P1",
        core_project_num="P1",
        title="Untitled",
        fiscal_year=2021,
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


# Hand-computed fixture (see PRD for the worked totals):
#   psychopathy/2021: Inst A $100k (Alice) + Inst B $200k (Bob) = $300k, 2 projects
#   psychopathy/2022: Inst A $300k (Alice, Carol) = $300k, 1 project
#   stress cortisol/2022: Inst C $50k (Dave) = $50k, 1 project
FIXTURE = [
    make_project(topic="psychopathy", project_num="P1", fiscal_year=2021, award_amount=100000.0,
                 org_name="Inst A", pi_names=["Alice"], agency_ic="NIMH"),
    make_project(topic="psychopathy", project_num="P2", fiscal_year=2021, award_amount=200000.0,
                 org_name="Inst B", pi_names=["Bob"], agency_ic="NIMH"),
    make_project(topic="psychopathy", project_num="P3", fiscal_year=2022, award_amount=300000.0,
                 org_name="Inst A", pi_names=["Alice", "Carol"], agency_ic="NIDA"),
    make_project(topic="stress cortisol", project_num="P4", fiscal_year=2022, award_amount=50000.0,
                 org_name="Inst C", pi_names=["Dave"], agency_ic="NIMH"),
]


def test_funding_by_year_totals_and_counts():
    psychopathy = [p for p in FIXTURE if p.topic == "psychopathy"]
    result = aggregate.funding_by_year(psychopathy)
    assert result[2021] == {"total_amount": 300000.0, "count": 2}
    assert result[2022] == {"total_amount": 300000.0, "count": 1}


def test_funding_by_year_per_topic_groups_correctly():
    result = aggregate.funding_by_year_per_topic(FIXTURE)
    assert set(result.keys()) == {"psychopathy", "stress cortisol"}
    assert result["stress cortisol"][2022]["total_amount"] == 50000.0


def test_year_over_year_growth_first_year_is_none():
    psychopathy = [p for p in FIXTURE if p.topic == "psychopathy"]
    year_totals = aggregate.funding_by_year(psychopathy)
    growth = aggregate.year_over_year_growth(year_totals)
    assert growth[2021] is None
    assert growth[2022] == 0.0  # $300k -> $300k, flat


def test_year_over_year_growth_handles_zero_prior_year_without_division_error():
    year_totals = {2020: {"total_amount": 0.0, "count": 0}, 2021: {"total_amount": 500.0, "count": 1}}
    growth = aggregate.year_over_year_growth(year_totals)
    assert growth[2020] is None
    assert growth[2021] is None


def test_top_institutions_ranking_and_totals():
    ranked = aggregate.top_institutions(FIXTURE, n=10)
    assert ranked[0] == ("Inst A", 400000.0, 2)
    assert ranked[1] == ("Inst B", 200000.0, 1)
    assert ranked[2] == ("Inst C", 50000.0, 1)


def test_top_institutions_respects_n_limit():
    ranked = aggregate.top_institutions(FIXTURE, n=1)
    assert ranked == [("Inst A", 400000.0, 2)]


def test_top_pis_ranking_multi_pi_project_credits_each_pi_full_amount():
    ranked = aggregate.top_pis(FIXTURE, n=10)
    assert ranked[0] == ("Alice", 400000.0, 2)
    assert ranked[1] == ("Carol", 300000.0, 1)
    assert ranked[2] == ("Bob", 200000.0, 1)
    assert ranked[3] == ("Dave", 50000.0, 1)


def test_agency_breakdown_totals():
    result = aggregate.agency_breakdown(FIXTURE)
    assert result["NIMH"] == {"total_amount": 350000.0, "count": 3}
    assert result["NIDA"] == {"total_amount": 300000.0, "count": 1}


def test_total_funding_sums_all_projects():
    assert aggregate.total_funding(FIXTURE) == 650000.0


def test_top_institutions_ties_break_alphabetically():
    tied = [
        make_project(project_num="A", org_name="Zeta Univ", award_amount=100.0),
        make_project(project_num="B", org_name="Alpha Univ", award_amount=100.0),
    ]
    ranked = aggregate.top_institutions(tied, n=10)
    assert [row[0] for row in ranked] == ["Alpha Univ", "Zeta Univ"]
