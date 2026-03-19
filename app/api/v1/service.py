"""Minimal service logic for v1 endpoints."""

from __future__ import annotations

from uuid import uuid4

from app.api.v1.schemas import (
    BudgetMeta,
    ChatMeta,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ProviderInfo,
)
from app.core import settings


def build_health_response() -> HealthResponse:
    return HealthResponse(
        version=settings.APP_VERSION,
        provider=ProviderInfo(
            chat=settings.DEFAULT_CHAT_PROVIDER,
            embedding=settings.DEFAULT_EMBEDDING_PROVIDER,
        ),
    )


def _estimate_input_tokens(text: str) -> int:
    # Placeholder heuristic for M1 scaffold until tokenizer/provider metrics are wired.
    estimated = max(1, len(text) // 4)
    return estimated


def _build_budget(max_output_tokens: int, message: str) -> BudgetMeta:
    max_context_tokens = max(1, settings.DEFAULT_MAX_CONTEXT_TOKENS)
    default_reserved_tokens = max(1, settings.DEFAULT_RESERVED_OUTPUT_TOKENS)

    reserve_cap = max_context_tokens if max_context_tokens == 1 else max_context_tokens - 1
    reserved_output_tokens = min(max_output_tokens, default_reserved_tokens, reserve_cap)

    available_input_tokens = max_context_tokens - reserved_output_tokens
    estimated_input_tokens = _estimate_input_tokens(message)
    used_input_tokens = min(estimated_input_tokens, available_input_tokens)

    return BudgetMeta(
        max_context_tokens=max_context_tokens,
        reserved_output_tokens=reserved_output_tokens,
        used_input_tokens=used_input_tokens,
    )


def build_chat_response(payload: ChatRequest) -> ChatResponse:
    request_id = f"req_{uuid4().hex[:12]}"
    budget = _build_budget(payload.options.max_output_tokens, payload.message)
    answer = f"[contextledger:m1] message received: {payload.message}"

    return ChatResponse(
        answer=answer,
        meta=ChatMeta(
            request_id=request_id,
            continuations=0,
            quality_score=0.8,
            retrieval_quality_score=0.0,
            context_growth_ratio=0.0,
            balance_mode="balanced",
            fallback_mode="none",
            budget=budget,
        ),
    )
