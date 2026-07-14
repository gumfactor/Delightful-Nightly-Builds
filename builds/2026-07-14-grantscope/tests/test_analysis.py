import analysis


def project(**overrides):
    base = {
        "project_num": "P1",
        "title": "Neural correlates of empathy in the amygdala",
        "abstract": "This study examines empathy and stress regulation using fMRI.",
        "pi_name": "Jane Smith",
        "org_name": "Big State University",
        "ic_admin": "NIMH",
        "activity_code": "R01",
        "award_amount": 100000,
        "fiscal_year": 2024,
    }
    base.update(overrides)
    return base


def test_funding_by_year_aggregates_totals_and_counts():
    projects = [
        project(project_num="P1", fiscal_year=2023, award_amount=100000),
        project(project_num="P2", fiscal_year=2023, award_amount=50000),
        project(project_num="P3", fiscal_year=2024, award_amount=200000),
    ]
    result = analysis.funding_by_year(projects)
    assert result[2023] == {"total_amount": 150000, "count": 2}
    assert result[2024] == {"total_amount": 200000, "count": 1}


def test_funding_by_year_skips_missing_year():
    projects = [project(fiscal_year=None, award_amount=999999)]
    result = analysis.funding_by_year(projects)
    assert result == {}


def test_funding_by_year_treats_missing_amount_as_zero():
    projects = [project(award_amount=None)]
    result = analysis.funding_by_year(projects)
    assert result[2024]["total_amount"] == 0
    assert result[2024]["count"] == 1


def test_top_institutes_ranks_by_total_amount_desc():
    projects = [
        project(project_num="P1", ic_admin="NIMH", award_amount=100000),
        project(project_num="P2", ic_admin="NIDA", award_amount=500000),
        project(project_num="P3", ic_admin="NIMH", award_amount=50000),
    ]
    ranked = analysis.top_institutes(projects, top_n=10)
    assert ranked[0] == ("NIDA", {"total_amount": 500000, "count": 1})
    assert ranked[1] == ("NIMH", {"total_amount": 150000, "count": 2})


def test_top_institutes_respects_top_n():
    projects = [project(project_num=str(i), ic_admin=f"IC{i}", award_amount=i) for i in range(5)]
    ranked = analysis.top_institutes(projects, top_n=2)
    assert len(ranked) == 2


def test_top_institutes_skips_missing_field():
    projects = [project(ic_admin=None)]
    assert analysis.top_institutes(projects) == []


def test_top_organizations_ranks_by_total_amount():
    projects = [
        project(project_num="P1", org_name="University A", award_amount=100),
        project(project_num="P2", org_name="University B", award_amount=300),
    ]
    ranked = analysis.top_organizations(projects)
    assert ranked[0][0] == "University B"


def test_mechanism_breakdown_counts_activity_codes():
    projects = [
        project(project_num="P1", activity_code="R01"),
        project(project_num="P2", activity_code="R01"),
        project(project_num="P3", activity_code="K01"),
    ]
    result = analysis.mechanism_breakdown(projects)
    assert result == {"R01": 2, "K01": 1}


def test_mechanism_breakdown_empty_when_no_projects():
    assert analysis.mechanism_breakdown([]) == {}


def test_extract_keywords_filters_stopwords_and_short_words():
    projects = [
        project(title="Empathy and stress", abstract="Empathy empathy empathy stress regulation study"),
    ]
    keywords = analysis.extract_keywords(projects, top_n=5)
    words = [word for word, count in keywords]
    assert "empathy" in words
    assert "and" not in words
    assert "study" not in words  # in stopword list


def test_extract_keywords_respects_top_n():
    projects = [project(title="alpha beta gamma delta epsilon zeta eta theta")]
    keywords = analysis.extract_keywords(projects, top_n=3)
    assert len(keywords) <= 3


def test_summary_stats_computes_headline_numbers():
    projects = [
        project(project_num="P1", fiscal_year=2022, award_amount=100000, ic_admin="NIMH", org_name="Uni A"),
        project(project_num="P2", fiscal_year=2024, award_amount=200000, ic_admin="NIDA", org_name="Uni B"),
    ]
    stats = analysis.summary_stats(projects)
    assert stats["project_count"] == 2
    assert stats["total_amount"] == 300000
    assert stats["fiscal_year_range"] == (2022, 2024)
    assert stats["distinct_institutes"] == 2
    assert stats["distinct_organizations"] == 2


def test_summary_stats_handles_empty_project_list():
    stats = analysis.summary_stats([])
    assert stats["project_count"] == 0
    assert stats["total_amount"] == 0
    assert stats["fiscal_year_range"] == (None, None)
