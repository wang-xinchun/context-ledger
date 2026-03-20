"""Deterministic local provider for M1 adapter wiring."""

from __future__ import annotations

from app.providers.base import ChatProviderRequest, ChatProviderResult


class DeterministicChatProvider:
    def __init__(self, *, provider_name: str, model_name: str) -> None:
        self._provider_name = provider_name
        self._model_name = model_name

    def generate(self, request: ChatProviderRequest) -> ChatProviderResult:
        # M1 阶段先打通 Provider Adapter 调用链；
        # 响应保持确定性，避免引入外部网络依赖导致回归不稳定。
        answer = (
            f"[{self._provider_name}:{self._model_name}] "
            f"message received: {request.message}"
        )
        return ChatProviderResult(
            answer=answer,
            provider_name=self._provider_name,
            model_name=self._model_name,
            latency_ms=0,
        )

