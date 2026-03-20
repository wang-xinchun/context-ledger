"""Provider registry for chat adapters."""

from __future__ import annotations

from functools import lru_cache

from app.core import settings
from app.providers.base import ChatProvider
from app.providers.deterministic_provider import DeterministicChatProvider


def _normalize_provider_name(provider_name: str) -> str:
    return provider_name.strip().lower()


@lru_cache(maxsize=8)
def get_chat_provider(provider_name: str) -> ChatProvider:
    """
    获取聊天 Provider 实例。
    通过 LRU 缓存复用实例，避免每次请求重复构造对象。
    """
    normalized = _normalize_provider_name(provider_name)
    if normalized == "lmstudio":
        return DeterministicChatProvider(
            provider_name="lmstudio",
            model_name=settings.LMSTUDIO_DEFAULT_MODEL,
        )
    if normalized == "ollama":
        return DeterministicChatProvider(
            provider_name="ollama",
            model_name=settings.OLLAMA_DEFAULT_MODEL,
        )
    if normalized in {"local", "mock", "deterministic"}:
        return DeterministicChatProvider(
            provider_name=normalized,
            model_name="contextledger-m1",
        )

    # 未识别 provider 自动回退到 deterministic adapter，保证主链路可用。
    return DeterministicChatProvider(
        provider_name=f"fallback:{normalized or 'unknown'}",
        model_name="contextledger-m1",
    )


def clear_chat_provider_cache() -> None:
    get_chat_provider.cache_clear()

