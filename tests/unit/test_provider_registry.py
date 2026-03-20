from __future__ import annotations

from app.providers.base import ChatProviderRequest
from app.providers.registry import clear_chat_provider_cache, get_chat_provider


def _request(message: str) -> ChatProviderRequest:
    return ChatProviderRequest(
        request_id="req_test",
        project_id="proj_test",
        session_id="sess_test",
        message=message,
        max_output_tokens=256,
        reserved_output_tokens=128,
        used_input_tokens=64,
        stream=False,
    )


def test_registry_returns_cached_provider_instance() -> None:
    clear_chat_provider_cache()
    provider_1 = get_chat_provider("lmstudio")
    provider_2 = get_chat_provider("lmstudio")
    assert provider_1 is provider_2


def test_registry_unknown_provider_falls_back_to_deterministic() -> None:
    clear_chat_provider_cache()
    provider = get_chat_provider("unknown-provider")
    result = provider.generate(_request("hello adapter"))
    assert "hello adapter" in result.answer
    assert result.provider_name.startswith("fallback:")


def test_registry_ollama_provider_returns_deterministic_answer() -> None:
    clear_chat_provider_cache()
    provider = get_chat_provider("ollama")
    result = provider.generate(_request("continue pipeline"))
    assert "continue pipeline" in result.answer
    assert result.provider_name == "ollama"

