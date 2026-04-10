from pathlib import Path
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

def client_wrapper():
    with patch("llm_wrapper.genai.Client") as mock_client_cls:
        client = MagicMock()
        mock_client_cls.return_value = client
        yield LLMWrapper(api_key="test-key"), client


@pytest.fixture

def repo_files(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_wrapper.LLMWrapper, "repo_root", property(lambda self: tmp_path))
    return tmp_path


def test_primary_success_returns_primary_text(client_wrapper):
    llm, client = client_wrapper
    client.models.generate_content.return_value = SimpleNamespace(text="primary result")

    result = llm.generate_content("hello")

    assert result == "primary result"
    client.models.generate_content.assert_called_once()
    assert client.models.generate_content.call_args.kwargs["model"] == "gemma-4-31b-it"
    assert "hello" in client.models.generate_content.call_args.kwargs["contents"]


def test_primary_error_triggers_fallback(client_wrapper, monkeypatch):
    llm, client = client_wrapper
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


def test_fallback_error_raises(client_wrapper, monkeypatch):
    llm, client = client_wrapper
    monkeypatch.setattr(llm_wrapper.errors, "APIError", MockAPIError)
    client.models.generate_content.side_effect = [
        MockAPIError(code=503, message="primary down"),
        MockAPIError(code=500, message="fallback down"),
    ]

    with pytest.raises(MockAPIError) as excinfo:
        llm.generate_content("hello")

    assert excinfo.value.message == "fallback down"
    assert client.models.generate_content.call_count == 2


def test_layer_injection_prepends_files_in_order(tmp_path, monkeypatch, client_wrapper):
    llm, client = client_wrapper
    monkeypatch.setattr(llm, "repo_root", tmp_path)
    (tmp_path / "memory.md").write_text("MEMORY", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("AGENTS", encoding="utf-8")
    (tmp_path / "SOUL.md").write_text("SOUL", encoding="utf-8")
    client.models.generate_content.return_value = SimpleNamespace(text="ok")

    llm.generate_content("PROMPT")

    sent = client.models.generate_content.call_args.kwargs["contents"]
    assert sent == "MEMORY\n\n---\n\nAGENTS\n\n---\n\nSOUL\n\n---\n\nPROMPT"


def test_missing_layers_warn_and_continue(tmp_path, monkeypatch, client_wrapper, caplog):
    llm, client = client_wrapper
    monkeypatch.setattr(llm, "repo_root", tmp_path)
    (tmp_path / "memory.md").write_text("MEMORY", encoding="utf-8")
    client.models.generate_content.return_value = SimpleNamespace(text="ok")

    with caplog.at_level("WARNING"):
        llm.generate_content("PROMPT")

    sent = client.models.generate_content.call_args.kwargs["contents"]
    assert sent == "MEMORY\n\n---\n\nPROMPT"
    assert any("Missing prompt layer file" in rec.message for rec in caplog.records)


def test_read_vault_file_returns_content_and_empty_on_missing(tmp_path, monkeypatch, client_wrapper):
    llm, _ = client_wrapper
    monkeypatch.setattr(llm, "repo_root", tmp_path)
    vault = tmp_path / "vault"
    (tmp_path / "memory.md").write_text(f"VAULT_PATH: {vault}\n", encoding="utf-8")
    file_path = vault / "Agent-Shared" / "sample.md"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("hello vault", encoding="utf-8")

    assert llm.read_vault_file("Agent-Shared/sample.md") == "hello vault"
    assert llm.read_vault_file("Agent-Shared/missing.md") == ""


def test_write_vault_file_creates_and_appends(tmp_path, monkeypatch, client_wrapper):
    llm, _ = client_wrapper
    monkeypatch.setattr(llm, "repo_root", tmp_path)
    (tmp_path / "memory.md").write_text(f"VAULT_PATH: {tmp_path / 'vault'}\n", encoding="utf-8")

    llm.write_vault_file("Agent-Steven/daily/2026-04-09.md", "one\n")
    llm.write_vault_file("Agent-Steven/daily/2026-04-09.md", "two\n", append=True)

    content = (tmp_path / "vault" / "Agent-Steven" / "daily" / "2026-04-09.md").read_text(encoding="utf-8")
    assert content == "one\ntwo\n"
