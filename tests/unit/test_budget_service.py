from __future__ import annotations

from app.api.v1 import service
from app.api.v1.schemas import ChatOptions, ChatRequest


def test_estimate_input_tokens_cjk_message_is_not_underestimated() -> None:
    ascii_tokens = service._estimate_input_tokens("continue refactor login module")
    cjk_tokens = service._estimate_input_tokens(
        "\u7ee7\u7eed\u91cd\u6784\u767b\u5f55\u6a21\u5757\u5e76\u4fee\u590d\u6743\u9650\u6821\u9a8c"
    )
    assert cjk_tokens >= ascii_tokens


def test_build_budget_respects_reserved_output_cap() -> None:
    budget = service._build_budget(max_output_tokens=100000, message="hello")
    assert budget.max_context_tokens == 4096
    assert budget.reserved_output_tokens == 900
    assert budget.used_input_tokens + budget.reserved_output_tokens <= budget.max_context_tokens


def test_build_budget_respects_requested_output_when_lower_than_default() -> None:
    budget = service._build_budget(max_output_tokens=256, message="hello")
    assert budget.reserved_output_tokens == 256
    assert budget.used_input_tokens + budget.reserved_output_tokens <= budget.max_context_tokens


def test_build_budget_handles_small_context(monkeypatch) -> None:
    monkeypatch.setattr(service.settings, "DEFAULT_MAX_CONTEXT_TOKENS", 10)
    monkeypatch.setattr(service.settings, "DEFAULT_RESERVED_OUTPUT_TOKENS", 9)
    budget = service._build_budget(max_output_tokens=1000, message="x" * 1000)
    assert budget.max_context_tokens == 10
    assert budget.reserved_output_tokens == 9
    assert budget.used_input_tokens <= 1
    assert budget.used_input_tokens + budget.reserved_output_tokens <= 10


def test_quality_and_fallback_signals_change_when_output_is_clamped() -> None:
    response = service.build_chat_response(
        payload=ChatRequest(
            project_id="proj_001",
            session_id="sess_001",
            message="x" * 50000,
            options=ChatOptions(max_output_tokens=20000, stream=False),
        )
    )
    assert response.meta.fallback_mode == "output_clamped"
    assert 0 <= response.meta.quality_score <= 1
    assert 0 <= response.meta.retrieval_quality_score <= 1


def test_build_budget_uses_reused_profile_path() -> None:
    profile = service._build_message_profile("hello world")
    budget = service._build_budget(
        max_output_tokens=900,
        message="hello world",
        profile=profile,
    )
    assert budget.max_context_tokens == 4096
    assert budget.reserved_output_tokens == 900
