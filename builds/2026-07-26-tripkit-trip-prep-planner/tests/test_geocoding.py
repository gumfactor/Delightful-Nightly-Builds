import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import geocoding  # noqa: E402


def test_resolve_destination_parses_successful_match():
    fake_response = {
        "results": [
            {"name": "Boston", "admin1": "Massachusetts", "country": "United States", "latitude": 42.36, "longitude": -71.06}
        ]
    }
    with patch("geocoding.fetch_json", return_value=fake_response) as mocked:
        place = geocoding.resolve_destination("Boston")

    mocked.assert_called_once()
    assert place.display_name == "Boston, Massachusetts, United States"
    assert place.country == "United States"
    assert place.latitude == 42.36
    assert place.longitude == -71.06


def test_resolve_destination_raises_on_empty_query():
    with patch("geocoding.fetch_json") as mocked:
        try:
            geocoding.resolve_destination("   ")
            assert False, "expected GeocodingError"
        except geocoding.GeocodingError:
            pass
    mocked.assert_not_called()


def test_resolve_destination_raises_when_no_results():
    with patch("geocoding.fetch_json", return_value={"results": []}):
        try:
            geocoding.resolve_destination("Nowhereville")
            assert False, "expected GeocodingError"
        except geocoding.GeocodingError as exc:
            assert "Nowhereville" in str(exc)


def test_resolve_destination_raises_on_network_error():
    with patch("geocoding.fetch_json", side_effect=OSError("boom")):
        try:
            geocoding.resolve_destination("Toronto")
            assert False, "expected GeocodingError"
        except geocoding.GeocodingError:
            pass
