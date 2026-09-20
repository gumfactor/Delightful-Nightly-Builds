from src.ai_polish import fallback_format, polish_response


def test_fallback_format_capitalizes_and_punctuates():
    assert fallback_format("we fixed the figure") == "We fixed the figure."


def test_fallback_format_collapses_whitespace():
    result = fallback_format("we   fixed\t\tthe   figure.")
    assert result == "We fixed the figure."


def test_fallback_format_empty_string_stays_empty():
    assert fallback_format("   ") == ""


def test_no_ai_flag_never_calls_client_factory():
    calls = []

    def factory(api_key):
        calls.append(api_key)
        raise AssertionError("client_factory must not be called when use_ai=False")

    result = polish_response(
        "reviewer comment",
        "raw response",
        api_key="sk-fake-key",
        use_ai=False,
        client_factory=factory,
    )
    assert calls == []
    assert result == "Raw response."


def test_no_api_key_never_calls_client_factory_even_with_use_ai_true():
    calls = []

    def factory(api_key):
        calls.append(api_key)
        raise AssertionError("client_factory must not be called without an api key")

    result = polish_response(
        "reviewer comment",
        "raw response",
        api_key=None,
        use_ai=True,
        client_factory=factory,
    )
    assert calls == []
    assert result == "Raw response."


class _FakeMessage:
    def __init__(self, text):
        self.content = [_FakeContentBlock(text)]


class _FakeContentBlock:
    def __init__(self, text):
        self.text = text


class _FakeMessagesAPI:
    def __init__(self, text_to_return, recorded_calls):
        self._text = text_to_return
        self._recorded_calls = recorded_calls

    def create(self, **kwargs):
        self._recorded_calls.append(kwargs)
        return _FakeMessage(self._text)


class _FakeClient:
    def __init__(self, text_to_return, recorded_calls):
        self.messages = _FakeMessagesAPI(text_to_return, recorded_calls)


def test_ai_polish_calls_client_with_expected_arguments_when_enabled():
    recorded_calls = []

    def factory(api_key):
        assert api_key == "sk-fake-key"
        return _FakeClient("Polished, professional response text.", recorded_calls)

    result = polish_response(
        "Please clarify X.",
        "we clarified x in section 2",
        api_key="sk-fake-key",
        model="claude-haiku-test",
        use_ai=True,
        client_factory=factory,
    )

    assert result == "Polished, professional response text."
    assert len(recorded_calls) == 1
    call = recorded_calls[0]
    assert call["model"] == "claude-haiku-test"
    assert "we clarified x in section 2" in call["messages"][0]["content"]
    assert "Please clarify X." in call["messages"][0]["content"]
    assert "do not add" in call["system"].lower() or "not add" in call["system"].lower()


def test_ai_polish_falls_back_gracefully_on_client_exception():
    def factory(api_key):
        raise RuntimeError("simulated network failure")

    result = polish_response(
        "reviewer comment",
        "raw response text",
        api_key="sk-fake-key",
        use_ai=True,
        client_factory=factory,
    )
    assert result == "Raw response text."


def test_ai_polish_falls_back_when_model_returns_empty_text():
    recorded_calls = []

    def factory(api_key):
        return _FakeClient("   ", recorded_calls)

    result = polish_response(
        "reviewer comment",
        "raw response text",
        api_key="sk-fake-key",
        use_ai=True,
        client_factory=factory,
    )
    assert result == "Raw response text."
