from src.budget_audit import audit_budget
from src.models import AuditConfig, BudgetLine


def make_line(grant_id="G1", grant_name="Grant One", fiscal_year="2026", category="Personnel",
              description="desc", direct_cost=1000.0, row_number=2):
    return BudgetLine(grant_id, grant_name, fiscal_year, category, description, direct_cost, row_number)


def test_mtdc_excludes_default_equipment_category():
    lines = [
        make_line(category="Personnel", direct_cost=10000, row_number=2),
        make_line(category="Equipment", direct_cost=5000, row_number=3),
    ]
    config = AuditConfig(far_rate=0.5)
    flags, summaries = audit_budget(lines, config)
    assert summaries[0].mtdc == 10000
    assert summaries[0].direct_total == 15000


def test_subcontract_threshold_partial_exemption():
    lines = [
        make_line(category="Personnel", direct_cost=10000, row_number=2),
        make_line(category="Subcontract", direct_cost=40000, row_number=3),
    ]
    config = AuditConfig(far_rate=0.5, subcontract_exempt_threshold=25000)
    flags, summaries = audit_budget(lines, config)
    # MTDC = 10000 personnel + 25000 (first slice of subcontract) = 35000
    assert summaries[0].mtdc == 35000
    assert any(f.code == "subcontract_threshold_applied" for f in flags)


def test_indirect_mismatch_flagged_beyond_tolerance():
    lines = [
        make_line(category="Personnel", direct_cost=10000, row_number=2),
        make_line(category="Indirect", direct_cost=1000, row_number=3),  # should be 5000 at 50%
    ]
    config = AuditConfig(far_rate=0.5, tolerance=1.0)
    flags, summaries = audit_budget(lines, config)
    mismatch = [f for f in flags if f.code == "indirect_mismatch"]
    assert len(mismatch) == 1
    assert summaries[0].expected_indirect == 5000.0
    assert summaries[0].stated_indirect == 1000.0


def test_indirect_within_tolerance_not_flagged():
    lines = [
        make_line(category="Personnel", direct_cost=10000, row_number=2),
        make_line(category="Indirect", direct_cost=5000.50, row_number=3),
    ]
    config = AuditConfig(far_rate=0.5, tolerance=1.0)
    flags, summaries = audit_budget(lines, config)
    assert not any(f.code == "indirect_mismatch" for f in flags)


def test_no_indirect_line_flags_info_with_expected_value():
    lines = [make_line(category="Personnel", direct_cost=10000, row_number=2)]
    config = AuditConfig(far_rate=0.5)
    flags, summaries = audit_budget(lines, config)
    info_flags = [f for f in flags if f.code == "no_indirect_line"]
    assert len(info_flags) == 1
    assert info_flags[0].severity.value == "info"
    assert "5,000.00" in info_flags[0].message


def test_missing_fringe_flagged_when_personnel_present():
    lines = [make_line(category="Personnel", direct_cost=10000, row_number=2)]
    config = AuditConfig(far_rate=0.5)
    flags, summaries = audit_budget(lines, config)
    assert any(f.code == "missing_fringe" for f in flags)


def test_fringe_present_no_missing_fringe_flag():
    lines = [
        make_line(category="Personnel", direct_cost=10000, row_number=2),
        make_line(category="Fringe Benefits", direct_cost=2700, row_number=3),
    ]
    config = AuditConfig(far_rate=0.5)
    flags, summaries = audit_budget(lines, config)
    assert not any(f.code == "missing_fringe" for f in flags)


def test_zero_or_negative_cost_flagged():
    lines = [make_line(category="Personnel", direct_cost=0, row_number=2)]
    config = AuditConfig(far_rate=0.5)
    flags, summaries = audit_budget(lines, config)
    assert any(f.code == "zero_or_negative_cost" for f in flags)


def test_duplicate_line_flagged():
    lines = [
        make_line(category="Supplies", description="Gel pens", direct_cost=50, row_number=2),
        make_line(category="Supplies", description="Gel pens", direct_cost=50, row_number=3),
    ]
    config = AuditConfig(far_rate=0.5)
    flags, summaries = audit_budget(lines, config)
    dupes = [f for f in flags if f.code == "duplicate_line"]
    assert len(dupes) == 1
    assert dupes[0].row_numbers == (2, 3)


def test_unknown_category_flagged():
    lines = [make_line(category="Miscellaneous Widgets", direct_cost=100, row_number=2)]
    config = AuditConfig(far_rate=0.5)
    flags, summaries = audit_budget(lines, config)
    assert any(f.code == "unknown_category" for f in flags)


def test_multiple_grants_grouped_independently():
    lines = [
        make_line(grant_id="G1", grant_name="Grant One", category="Personnel", direct_cost=10000, row_number=2),
        make_line(grant_id="G2", grant_name="Grant Two", category="Personnel", direct_cost=20000, row_number=3),
    ]
    config = AuditConfig(far_rate=0.5)
    flags, summaries = audit_budget(lines, config)
    assert len(summaries) == 2
    grant_ids = {s.grant_id for s in summaries}
    assert grant_ids == {"G1", "G2"}
