import pytest

from src import db


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(tmp_path / "test.db")
    yield connection
    connection.close()


def test_add_domain_and_list(conn):
    domain_id = db.add_domain(conn, "Example.COM", "Test Project", "2026-08-22T00:00:00")
    rows = db.list_domains(conn)
    assert len(rows) == 1
    assert rows[0]["id"] == domain_id
    assert rows[0]["domain"] == "example.com"  # normalized to lowercase
    assert rows[0]["project_label"] == "Test Project"


def test_add_duplicate_domain_raises(conn):
    db.add_domain(conn, "example.com", None, "2026-08-22T00:00:00")
    with pytest.raises(ValueError):
        db.add_domain(conn, "example.com", None, "2026-08-22T00:00:00")


def test_add_empty_domain_raises(conn):
    with pytest.raises(ValueError):
        db.add_domain(conn, "   ", None, "2026-08-22T00:00:00")


def test_same_day_snapshot_upserts_not_duplicates(conn):
    domain_id = db.add_domain(conn, "example.com", None, "2026-08-22T00:00:00")
    db.upsert_domain_snapshot(
        conn, domain_id, "2026-08-22",
        rdap_status="ok", rdap_expiration="2027-01-01", rdap_registrar="Registrar A",
        ssl_status="ok", ssl_expiration="2026-12-01", ssl_days_remaining=101,
    )
    db.upsert_domain_snapshot(
        conn, domain_id, "2026-08-22",
        rdap_status="ok", rdap_expiration="2027-01-01", rdap_registrar="Registrar A",
        ssl_status="ok", ssl_expiration="2026-12-01", ssl_days_remaining=100,
    )
    history = db.snapshot_history(conn, domain_id)
    assert len(history) == 1
    assert history[0]["ssl_days_remaining"] == 100  # second sync's value won


def test_latest_snapshot_returns_most_recent(conn):
    domain_id = db.add_domain(conn, "example.com", None, "2026-08-22T00:00:00")
    db.upsert_domain_snapshot(
        conn, domain_id, "2026-08-20",
        rdap_status="ok", rdap_expiration="2027-01-01", rdap_registrar="A",
        ssl_status="ok", ssl_expiration="2026-12-01", ssl_days_remaining=103,
    )
    db.upsert_domain_snapshot(
        conn, domain_id, "2026-08-22",
        rdap_status="ok", rdap_expiration="2027-01-01", rdap_registrar="A",
        ssl_status="ok", ssl_expiration="2026-12-01", ssl_days_remaining=101,
    )
    latest = db.latest_snapshot(conn, domain_id)
    assert latest["snapshot_date"] == "2026-08-22"
    assert latest["ssl_days_remaining"] == 101


def test_add_manual_renewal_invalid_category_raises(conn):
    with pytest.raises(ValueError):
        db.add_manual_renewal(
            conn, title="X", category="not-a-category", due_date="2027-01-01",
            recurrence="annual", created_at="2026-08-22T00:00:00",
        )


def test_add_manual_renewal_invalid_recurrence_raises(conn):
    with pytest.raises(ValueError):
        db.add_manual_renewal(
            conn, title="X", category="license", due_date="2027-01-01",
            recurrence="weekly", created_at="2026-08-22T00:00:00",
        )


def test_add_manual_renewal_every_n_months_requires_n(conn):
    with pytest.raises(ValueError):
        db.add_manual_renewal(
            conn, title="X", category="license", due_date="2027-01-01",
            recurrence="every-N-months", created_at="2026-08-22T00:00:00",
        )


def test_complete_manual_renewal_marks_done(conn):
    renewal_id = db.add_manual_renewal(
        conn, title="Business License", category="license", due_date="2027-01-01",
        recurrence="annual", created_at="2026-08-22T00:00:00",
    )
    db.complete_manual_renewal(conn, renewal_id, "2026-12-01T00:00:00")
    row = db.get_manual_renewal(conn, renewal_id)
    assert row["status"] == "done"
    assert row["completed_at"] == "2026-12-01T00:00:00"


def test_list_manual_renewals_filters_by_status(conn):
    id1 = db.add_manual_renewal(
        conn, title="A", category="license", due_date="2027-01-01",
        recurrence="annual", created_at="2026-08-22T00:00:00",
    )
    db.add_manual_renewal(
        conn, title="B", category="insurance", due_date="2027-02-01",
        recurrence="annual", created_at="2026-08-22T00:00:00",
    )
    db.complete_manual_renewal(conn, id1, "2026-12-01T00:00:00")

    pending = db.list_manual_renewals(conn, status="pending")
    done = db.list_manual_renewals(conn, status="done")
    assert len(pending) == 1
    assert pending[0]["title"] == "B"
    assert len(done) == 1
    assert done[0]["title"] == "A"
