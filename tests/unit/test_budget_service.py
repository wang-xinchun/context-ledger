from __future__ import annotations

from app.api.v1 import service


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
