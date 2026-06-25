"""Flask route integration tests using the test client."""
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest


MOCK_EXPLANATION = "This is a mocked AI explanation for testing purposes."


@pytest.fixture
def client(tmp_path):
    # Patch generate_explanation so tests never call the real Anthropic API.
    # Patch DB path to an isolated temp file so tests don't share state.
    with patch("server.DB_PATH", tmp_path / "test.db"), \
         patch("server.generate_explanation", return_value=MOCK_EXPLANATION):
        import server
        server._cache = None  # reset singleton between test runs
        server.app.config["TESTING"] = True
        with server.app.test_client() as c:
            yield c


VALID_PARAMS = {
    "outcome_type": "continuous",
    "num_groups": 2,
    "paired": False,
    "normality": "assumed",
    "relationship": False,
    "study_context": "",
}


def test_index_returns_200(client):
    res = client.get("/")
    assert res.status_code == 200


def test_index_returns_html(client):
    res = client.get("/")
    assert b"Stats Coach" in res.data


def test_advise_valid_continuous_two_groups(client):
    res = client.post("/api/advise", json=VALID_PARAMS)
    assert res.status_code == 200


def test_advise_returns_test_name(client):
    res = client.post("/api/advise", json=VALID_PARAMS)
    data = json.loads(res.data)
    assert "test_name" in data
    assert data["test_name"] == "Independent Samples t-test"


def test_advise_returns_r_code(client):
    res = client.post("/api/advise", json=VALID_PARAMS)
    data = json.loads(res.data)
    assert "r_code" in data
    assert len(data["r_code"]) > 5


def test_advise_returns_python_code(client):
    res = client.post("/api/advise", json=VALID_PARAMS)
    data = json.loads(res.data)
    assert "python_code" in data
    assert len(data["python_code"]) > 5


def test_advise_returns_ai_explanation(client):
    res = client.post("/api/advise", json=VALID_PARAMS)
    data = json.loads(res.data)
    assert "ai_explanation" in data
    assert data["ai_explanation"] == MOCK_EXPLANATION


def test_advise_missing_outcome_type_returns_400(client):
    params = {k: v for k, v in VALID_PARAMS.items() if k != "outcome_type"}
    res = client.post("/api/advise", json=params)
    assert res.status_code == 400


def test_advise_invalid_outcome_type_returns_400(client):
    res = client.post("/api/advise", json={**VALID_PARAMS, "outcome_type": "ratio"})
    assert res.status_code == 400


def test_advise_invalid_normality_returns_400(client):
    res = client.post("/api/advise", json={**VALID_PARAMS, "normality": "maybe"})
    assert res.status_code == 400


def test_advise_zero_groups_returns_400(client):
    res = client.post("/api/advise", json={**VALID_PARAMS, "num_groups": 0})
    assert res.status_code == 400


def test_advise_non_integer_groups_returns_400(client):
    res = client.post("/api/advise", json={**VALID_PARAMS, "num_groups": "two"})
    assert res.status_code == 400


def test_advise_second_identical_request_is_cached(client):
    client.post("/api/advise", json=VALID_PARAMS)
    res2 = client.post("/api/advise", json=VALID_PARAMS)
    data = json.loads(res2.data)
    assert data.get("cached") is True


def test_advise_cached_false_on_first_request(client):
    res = client.post("/api/advise", json=VALID_PARAMS)
    data = json.loads(res.data)
    assert data.get("cached") is False


def test_advise_error_response_contains_error_key(client):
    res = client.post("/api/advise", json={**VALID_PARAMS, "outcome_type": "bad_type"})
    data = json.loads(res.data)
    assert "error" in data


def test_advise_paired_t_test(client):
    res = client.post("/api/advise", json={**VALID_PARAMS, "paired": True})
    data = json.loads(res.data)
    assert data["test_name"] == "Paired Samples t-test"


def test_advise_anova_three_groups(client):
    res = client.post("/api/advise", json={**VALID_PARAMS, "num_groups": 3})
    data = json.loads(res.data)
    assert data["test_name"] == "One-Way ANOVA"


def test_advise_chi_square_categorical(client):
    res = client.post(
        "/api/advise",
        json={**VALID_PARAMS, "outcome_type": "categorical", "num_groups": 3},
    )
    data = json.loads(res.data)
    assert data["test_name"] == "Chi-Square Test of Independence"


def test_advise_returns_interpretation(client):
    res = client.post("/api/advise", json=VALID_PARAMS)
    data = json.loads(res.data)
    assert "interpretation" in data
    assert len(data["interpretation"]) > 5
