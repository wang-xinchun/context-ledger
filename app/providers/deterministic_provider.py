"""Deterministic local provider for M1 adapter wiring."""

from __future__ import annotations

from app.providers.base import ChatProviderRequest, ChatProviderResult


class DeterministicChatProvider:
    def __init__(self, *, provider_name: str, model_name: str) -> None:
        self._provider_name = provider_name
        self._model_name = model_name

    def generate(self, request: ChatProviderRequest) -> ChatProviderResult:
        # 按输出预算进行确定性截断，避免长输入在压测时放大回显开销。
        prefix = f"[{self._provider_name}:{self._model_name}] message received: "
        message = request.message.strip()
        char_budget = max(32, request.max_output_tokens * 4)
        if len(message) > char_budget:
            clipped = message[: max(1, char_budget - 10)] + "...[trunc]"
        else:
            clipped = message

        return ChatProviderResult(
            answer=prefix + clipped,
            provider_name=self._provider_name,
            model_name=self._model_name,
            latency_ms=0,
        )
