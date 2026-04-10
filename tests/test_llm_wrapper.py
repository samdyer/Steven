from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import llm_wrapper
from llm_wrapper import LLMWrapper


class MockAPIError(Exception):
    def __init__(self, code=429, message="rate limited"):
        super().__init__(message)
        self.code = code
        self.message = message


@pytest.fixture

def wrapper():
    with patch("llm_wrapper.genai.Client") as mock_client_cls:
        client = MagicMock()
        mock_client_cls.return_value = client
        yield LLMWrapper(api_key="test-key"), client


def test_primary_success_returns_primary_text(wrapper):
    llm, client = wrapper
    client.models.generate_content.return_value = SimpleNamespace(text="primary result")

    result = llm.generate_content("hello")

    assert result == "primary result"
    client.models.generate_content.assert_called_once_with(
        model="gemma-4-31b-it",
        contents="hello",
    )


def test_primary_error_triggers_fallback(wrapper, monkeypatch):
    llm, client = wrapper
    monkeypatch.setattr(llm_wrapper.errors, "APIError", MockAPIError)
    client.models.generate_content.side_effect = [
        MockAPIError(code=429, message="primary failed"),
        SimpleNamespace(text="fallback result"),
    ]

    result = llm.generate_content("hello")

    assert result == "fallback result"
    assert client.models.generate_content.call_count == 2
    assert client.models.generate_content.call_args_list[0].kwargs["model"] == "gemma-4-31b-it"
    assert client.models.generate_content.call_args_list[1].kwargs["model"] == "gemini-2.5-flash"


def test_fallback_error_raises(wrapper, monkeypatch):
    llm, client = wrapper
    monkeypatch.setattr(llm_wrapper.errors, "APIError", MockAPIError)
    primary_error = MockAPIError(code=503, message="primary down")
    fallback_error = MockAPIError(code=500, message="fallback down")
    client.models.generate_content.side_effect = [primary_error, fallback_error]

    with pytest.raises(MockAPIError) as excinfo:
        llm.generate_content("hello")

    assert excinfo.value.message == "fallback down"
    assert client.models.generate_content.call_count == 2
