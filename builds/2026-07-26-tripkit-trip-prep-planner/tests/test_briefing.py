import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import briefing  # noqa: E402

COMMON_ARGS = dict(
    trip_name="ICON Conference",
    destination_name="Boston, Massachusetts, United States",
    start_date="2026-08-15",
    end_date="2026-08-18",
    activity_tags=["conference"],
    mode="forecast",
    avg_high_c=27.0,
    avg_low_c=19.0,
    any_rain=False,
    any_wind=False,
    packing_list={"Clothing": ["item"], "Gear": [], "Documents & Admin": [], "Health & Comfort": []},
)


def test_generate_briefing_returns_ai_text_on_success():
    with patch.object(briefing, "_call_anthropic_api", return_value="A sunny conference trip awaits.") as mocked:
        result = briefing.generate_briefing(**COMMON_ARGS, api_key="fake-key")

    mocked.assert_called_once()
    assert result == "A sunny conference trip awaits."


def test_generate_briefing_uses_template_when_no_api_key():
    with patch.object(briefing, "_call_anthropic_api") as mocked:
        result = briefing.generate_briefing(**COMMON_ARGS, api_key=None)

    mocked.assert_not_called()
    assert "ICON Conference" in result
    assert "Boston" in result


def test_generate_briefing_falls_back_on_api_failure():
    with patch.object(briefing, "_call_anthropic_api", side_effect=OSError("network down")) as mocked:
        result = briefing.generate_briefing(**COMMON_ARGS, api_key="fake-key")

    mocked.assert_called_once()
    assert "ICON Conference" in result


def test_deterministic_template_mentions_rain_when_expected():
    args = dict(COMMON_ARGS)
    args["any_rain"] = True
    result = briefing.generate_briefing(**args, api_key=None)
    assert "rain" in result.lower()


def test_call_anthropic_api_raises_on_empty_text_content():
    fake_response_body = b'{"content": [{"type": "text", "text": ""}]}'

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return fake_response_body

    with patch("urllib.request.urlopen", return_value=FakeResponse()):
        try:
            briefing._call_anthropic_api("fake-key", "prompt text")
            assert False, "expected ValueError"
        except ValueError:
            pass
