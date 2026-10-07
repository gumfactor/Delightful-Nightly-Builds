import json

import pytest

from canpulse import sources

VALET = {"observations": [
    {"d": "2024-01-03", "FXUSDCAD": {"v": "1.3300"}},
    {"d": "2024-01-02", "FXUSDCAD": {"v": "1.3400"}},
    {"d": "2024-01-04", "FXUSDCAD": {"v": ""}},
    {"d": "2024-01-05"},
    {"d": "2024-01-08", "FXUSDCAD": {"v": "n/a"}},
]}


def wds(vector, values, status="SUCCESS"):
    return [{"status": status, "object": {"vectorId": vector, "vectorDataPoint": [
        {"refPer": ref, "value": val} for ref, val in values]}}]


def test_parse_valet_sorts_and_skips_blank_or_bad_values():
    assert sources.parse_valet(VALET, "FXUSDCAD") == [["2024-01-02", 1.34], ["2024-01-03", 1.33]]


def test_parse_wds_normalises_month_dates_and_skips_nulls():
    payload = wds(5, [("2024-02", "101.5"), ("2024-01", "100.0"), ("2024-03", None)])
    points, _ = sources.parse_wds(payload, 5)
    assert points == [["2024-01-01", 100.0], ["2024-02-01", 101.5]]


def test_parse_wds_rejects_failed_status():
    with pytest.raises(ValueError):
        sources.parse_wds(wds(5, [], status="FAILED"), 5)


def test_parse_wds_rejects_wrong_vector():
    with pytest.raises(ValueError):
        sources.parse_wds(wds(6, [("2024-01", "1")]), 5)


def test_iso_date_rejects_garbage():
    with pytest.raises(ValueError):
        sources._iso_date("Q1-2024")


def test_fetch_valet_builds_url_and_raises_on_empty():
    seen = []

    def fake(url, body):
        seen.append(url)
        return {"observations": []}

    with pytest.raises(ValueError):
        sources.fetch_valet("FXUSDCAD", fake)
    assert "/FXUSDCAD/json?recent=" in seen[0]


def test_fetch_wds_posts_vector_request():
    captured = {}

    def fake(url, body):
        captured["body"] = json.loads(body)
        return wds(41690973, [("2024-01", "150")])

    assert sources.fetch_wds(41690973, fake) == [["2024-01-01", 150.0]]
    assert captured["body"][0]["vectorId"] == 41690973


def test_fetch_all_isolates_failures():
    specs = [
        {"id": "a", "label": "A", "unit": "%", "source": "valet", "series": "X", "freq": "D", "higher_is": "good", "group": "g"},
        {"id": "b", "label": "B", "unit": "%", "source": "statcan", "vector": 9, "freq": "M", "higher_is": "good", "group": "g"},
    ]

    def fake(url, body):
        if "valet" in url:
            raise OSError("proxy 403")
        return wds(9, [("2024-01", "1")])

    series, errors = sources.fetch_all(fake, specs)
    assert list(series) == ["b"] and "OSError" in errors["a"]


def test_verify_vectors_flags_title_mismatch():
    specs = [{"id": "cpi", "source": "statcan", "vector": 1, "expect": "consumer price"},
             {"id": "gdp", "source": "statcan", "vector": 2, "expect": "all industries"}]

    def fake(url, body):
        vec = json.loads(body)[0]["vectorId"]
        title = "Canada; All-items; Consumer Price Index" if vec == 1 else "Unrelated"
        return [{"object": {"SeriesTitleEn": title, "productId": 123}}]

    res = {r["id"]: r["ok"] for r in sources.verify_vectors(fake, specs)}
    assert res == {"cpi": True, "gdp": False}
