"""OpenAI-compatible gateway endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.api.v1.service import run_chat_pipeline
from app.core import settings

router = APIRouter(prefix="/openai/v1", tags=["openai-compatibility"])

DEFAULT_COMPAT_PROJECT_ID = "compat_project"
DEFAULT_COMPAT_SESSION_ID = "compat_session"
OPENAI_CHAT_DEFAULT_MAX_TOKENS = 1200
OPENAI_CHAT_OBJECT = "chat.completion"
OPENAI_FINISH_REASON_STOP = "stop"


def _request_id() -> str:
    return f"req_{uuid4().hex[:12]}"


def _error_response(*, status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": _request_id(),
            }
        },
    )


def _not_implemented(endpoint: str) -> JSONResponse:
    return _error_response(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        code="NOT_IMPLEMENTED",
        message=f"{endpoint} is reserved for M1 compatibility stage.",
    )


def _bad_request(message: str) -> JSONResponse:
    return _error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="INVALID_REQUEST",
        message=message,
    )


def _normalize_optional_str(value: Any, default: str) -> str:
    if isinstance(value, str):
        text = value.strip()
        return text or default
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _coerce_positive_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return max(1, value)
    if isinstance(value, float):
        return max(1, int(value))
    return default


def _extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if not isinstance(content, list):
        return ""

    chunks: list[str] = []
    append_chunk = chunks.append
    for item in content:
        if not isinstance(item, dict):
            continue

        item_type = item.get("type")
        if isinstance(item_type, str):
            normalized = item_type.strip().lower()
            if normalized and normalized != "text":
                continue
        elif item_type is not None:
            continue

        text = item.get("text")
        if not isinstance(text, str):
            continue
        stripped = text.strip()
        if stripped:
            append_chunk(stripped)

    if not chunks:
        return ""
    if len(chunks) == 1:
        return chunks[0]
    return "\n".join(chunks)


def _extract_prompt(messages: list[Any]) -> str:
    fallback_latest = ""
    # 逆序扫描优先命中“最近一条 user”，减少长历史下的无效遍历。
    for item in reversed(messages):
        if not isinstance(item, dict):
            continue
        text = _extract_text_from_content(item.get("content"))
        if not text:
            continue
        if not fallback_latest:
            fallback_latest = text

        role = item.get("role")
        if isinstance(role, str) and role.strip().lower() == "user":
            return text

    return fallback_latest


def _estimate_output_tokens(answer: str) -> int:
    compact = answer.strip()
    if not compact:
        return 1
    # 向上取整，避免短答案出现 0 completion tokens。
    return max(1, (len(compact) + 3) // 4)


def _unix_timestamp() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp())


@lru_cache(maxsize=1)
def _models_payload() -> dict[str, Any]:
    now_ts = _unix_timestamp()
    return {
        "object": "list",
        "data": [
            {
                "id": settings.LMSTUDIO_DEFAULT_MODEL,
                "object": "model",
                "created": now_ts,
                "owned_by": "contextledger",
            },
            {
                "id": settings.OLLAMA_DEFAULT_MODEL,
                "object": "model",
                "created": now_ts,
                "owned_by": "contextledger",
            },
            {
                "id": "contextledger-m1-deterministic",
                "object": "model",
                "created": now_ts,
                "owned_by": "contextledger",
            },
        ],
    }


@router.post("/chat/completions", response_model=None)
def post_chat_completions(payload: dict[str, Any]) -> JSONResponse:
    raw_messages = payload.get("messages")
    if not isinstance(raw_messages, list) or not raw_messages:
        return _bad_request("`messages` must be a non-empty list.")

    prompt = _extract_prompt(raw_messages)
    if not prompt:
        return _bad_request("No text content could be extracted from `messages`.")

    max_output_tokens = _coerce_positive_int(
        payload.get("max_tokens"),
        OPENAI_CHAT_DEFAULT_MAX_TOKENS,
    )

    stream = bool(payload.get("stream", False))
    project_id = _normalize_optional_str(
        payload.get("project_id"),
        DEFAULT_COMPAT_PROJECT_ID,
    )
    session_id = _normalize_optional_str(
        payload.get("session_id"),
        DEFAULT_COMPAT_SESSION_ID,
    )
    model_name = _normalize_optional_str(
        payload.get("model"),
        settings.LMSTUDIO_DEFAULT_MODEL,
    )

    runtime = run_chat_pipeline(
        project_id=project_id,
        session_id=session_id,
        message=prompt,
        max_output_tokens=max_output_tokens,
        stream=stream,
    )
    completion_id = f"chatcmpl_{runtime.request_id}"
    completion_tokens = _estimate_output_tokens(runtime.answer)
    prompt_tokens = runtime.budget.used_input_tokens
    usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "id": completion_id,
            "object": OPENAI_CHAT_OBJECT,
            "created": _unix_timestamp(),
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": runtime.answer,
                    },
                    "finish_reason": OPENAI_FINISH_REASON_STOP,
                }
            ],
            "usage": usage,
            "x_contextledger": {
                "request_id": runtime.request_id,
                "quality_score": runtime.quality_score,
                "retrieval_quality_score": runtime.retrieval_quality_score,
                "context_growth_ratio": runtime.context_growth_ratio,
                "balance_mode": runtime.balance_mode,
                "fallback_mode": runtime.fallback_mode,
            },
        },
    )


@router.post("/responses", response_model=None)
def post_responses() -> JSONResponse:
    return _not_implemented("/openai/v1/responses")


@router.post("/embeddings", response_model=None)
def post_embeddings() -> JSONResponse:
    return _not_implemented("/openai/v1/embeddings")


@router.get("/models", response_model=None)
def get_models() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=_models_payload(),
    )
