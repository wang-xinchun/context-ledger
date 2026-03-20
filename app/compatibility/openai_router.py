"""OpenAI-compatible gateway endpoints."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.v1.service import ChatRuntimeResult, run_chat_pipeline
from app.core import settings

router = APIRouter(prefix="/openai/v1", tags=["openai-compatibility"])

DEFAULT_COMPAT_PROJECT_ID = "compat_project"
DEFAULT_COMPAT_SESSION_ID = "compat_session"
OPENAI_CHAT_DEFAULT_MAX_TOKENS = 1200
OPENAI_CHAT_OBJECT = "chat.completion"
OPENAI_RESPONSE_OBJECT = "response"
OPENAI_CHAT_CHUNK_OBJECT = "chat.completion.chunk"
OPENAI_FINISH_REASON_STOP = "stop"
OPENAI_OUTPUT_MESSAGE_TYPE = "message"
OPENAI_OUTPUT_TEXT_TYPE = "output_text"
OPENAI_EMBEDDING_OBJECT = "embedding"
OPENAI_EMBEDDING_DIM = 64
CONTENT_TEXT_TYPES = frozenset({"text", "input_text"})
TRUE_BOOL_TEXTS = frozenset({"1", "true", "yes", "y", "on"})
FALSE_BOOL_TEXTS = frozenset({"0", "false", "no", "n", "off", ""})
USER_ROLE = "user"
SSE_DONE_BYTES = b"data: [DONE]\n\n"
_EMBEDDING_BYTE_TO_FLOAT = tuple(round((byte / 255.0) * 2.0 - 1.0, 3) for byte in range(256))


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


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in TRUE_BOOL_TEXTS:
            return True
        if normalized in FALSE_BOOL_TEXTS:
            return False
    return default


def _extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if not isinstance(content, list):
        return ""

    first_chunk = ""
    extra_chunks: list[str] | None = None
    for item in content:
        if not isinstance(item, dict):
            continue

        item_type = item.get("type")
        if isinstance(item_type, str):
            normalized = item_type.strip().lower()
            if normalized and normalized not in CONTENT_TEXT_TYPES:
                continue
        elif item_type is not None:
            continue

        text = item.get("text")
        if not isinstance(text, str):
            continue
        stripped = text.strip()
        if stripped:
            if not first_chunk:
                first_chunk = stripped
            elif extra_chunks is None:
                extra_chunks = [stripped]
            else:
                extra_chunks.append(stripped)

    if not first_chunk:
        return ""
    if extra_chunks is None:
        return first_chunk
    return "\n".join([first_chunk, *extra_chunks])


def _extract_prompt_from_messages(messages: list[Any]) -> str:
    fallback_latest = ""
    # Reverse scan to hit latest user message early for lower overhead on long history.
    for item in reversed(messages):
        if not isinstance(item, dict):
            continue

        text = _extract_text_from_content(item.get("content"))
        if not text:
            direct_text = item.get("text")
            if isinstance(direct_text, str):
                text = direct_text.strip()
        if not text:
            continue

        if not fallback_latest:
            fallback_latest = text

        role = item.get("role")
        if isinstance(role, str) and (role == USER_ROLE or role.strip().lower() == USER_ROLE):
            return text

    return fallback_latest


def _extract_prompt_from_responses_input(input_value: Any) -> str:
    if isinstance(input_value, str):
        return input_value.strip()

    if isinstance(input_value, dict):
        text = _extract_text_from_content(input_value.get("content"))
        if text:
            return text
        raw_text = input_value.get("text")
        if isinstance(raw_text, str):
            return raw_text.strip()
        return ""

    if not isinstance(input_value, list):
        return ""

    if input_value and isinstance(input_value[0], dict) and "role" in input_value[0]:
        return _extract_prompt_from_messages(input_value)

    fallback_latest = ""
    for item in reversed(input_value):
        if isinstance(item, str):
            stripped = item.strip()
            if stripped:
                return stripped
            continue

        if not isinstance(item, dict):
            continue

        text = _extract_text_from_content(item.get("content"))
        if not text:
            raw_text = item.get("text")
            if isinstance(raw_text, str):
                text = raw_text.strip()
        if not text:
            continue

        if not fallback_latest:
            fallback_latest = text

        role = item.get("role")
        if isinstance(role, str) and (role == USER_ROLE or role.strip().lower() == USER_ROLE):
            return text

    return fallback_latest


def _estimate_tokens_by_text(text: str) -> int:
    compact = text.strip()
    if not compact:
        return 1
    return max(1, (len(compact) + 3) // 4)


def _unix_timestamp() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp())


def _contextledger_meta(runtime: ChatRuntimeResult) -> dict[str, Any]:
    return {
        "request_id": runtime.request_id,
        "quality_score": runtime.quality_score,
        "retrieval_quality_score": runtime.retrieval_quality_score,
        "context_growth_ratio": runtime.context_growth_ratio,
        "balance_mode": runtime.balance_mode,
        "fallback_mode": runtime.fallback_mode,
    }


def _json_compact_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sse_json_bytes(payload: dict[str, Any]) -> bytes:
    return b"data: " + _json_compact_bytes(payload) + b"\n\n"


def _sse_done_bytes() -> bytes:
    return SSE_DONE_BYTES


def _run_compat_chat(
    *,
    payload: dict[str, Any],
    prompt: str,
    max_output_tokens: int,
    stream: bool,
) -> tuple[str, ChatRuntimeResult, str]:
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
        collect_used_memories=False,
        persist_turn=settings.COMPAT_CHAT_PERSIST_TURN,
    )
    return model_name, runtime, f"chatcmpl_{runtime.request_id}"


def _build_chat_completions_payload(
    *,
    completion_id: str,
    model_name: str,
    runtime: ChatRuntimeResult,
) -> dict[str, Any]:
    completion_tokens = _estimate_tokens_by_text(runtime.answer)
    prompt_tokens = runtime.budget.used_input_tokens
    return {
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
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
        "x_contextledger": _contextledger_meta(runtime),
    }


def _iter_chat_completions_stream(
    *,
    completion_id: str,
    model_name: str,
    runtime: ChatRuntimeResult,
) -> Iterator[bytes]:
    created = _unix_timestamp()
    chunk_common = {
        "id": completion_id,
        "object": OPENAI_CHAT_CHUNK_OBJECT,
        "created": created,
        "model": model_name,
    }
    yield _sse_json_bytes(
        {
            **chunk_common,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": None,
                }
            ],
            "x_contextledger": _contextledger_meta(runtime),
        }
    )
    answer = runtime.answer
    if answer:
        yield _sse_json_bytes(
            {
                **chunk_common,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": answer},
                        "finish_reason": None,
                    }
                ],
            }
        )
    yield _sse_json_bytes(
        {
            **chunk_common,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": OPENAI_FINISH_REASON_STOP,
                }
            ],
        }
    )
    yield _sse_done_bytes()


def _build_responses_payload(
    *,
    model_name: str,
    runtime: ChatRuntimeResult,
) -> dict[str, Any]:
    output_tokens, input_tokens = _response_usage_tokens(runtime)
    response_id = f"resp_{runtime.request_id}"
    output_message_id = f"msg_{runtime.request_id}"
    return {
        "id": response_id,
        "object": OPENAI_RESPONSE_OBJECT,
        "created": _unix_timestamp(),
        "status": "completed",
        "model": model_name,
        "output": [
            {
                "type": OPENAI_OUTPUT_MESSAGE_TYPE,
                "id": output_message_id,
                "role": "assistant",
                "content": [
                    {
                        "type": OPENAI_OUTPUT_TEXT_TYPE,
                        "text": runtime.answer,
                        "annotations": [],
                    }
                ],
            }
        ],
        "output_text": runtime.answer,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        },
        "x_contextledger": _contextledger_meta(runtime),
    }


def _response_usage_tokens(runtime: ChatRuntimeResult) -> tuple[int, int]:
    return _estimate_tokens_by_text(runtime.answer), runtime.budget.used_input_tokens


def _iter_responses_stream(
    *,
    model_name: str,
    runtime: ChatRuntimeResult,
) -> Iterator[bytes]:
    response_id = f"resp_{runtime.request_id}"
    created = _unix_timestamp()
    answer = runtime.answer
    output_tokens, input_tokens = _response_usage_tokens(runtime)
    yield _sse_json_bytes(
        {
            "type": "response.created",
            "response": {
                "id": response_id,
                "object": OPENAI_RESPONSE_OBJECT,
                "created": created,
                "model": model_name,
                "status": "in_progress",
            },
        }
    )
    if answer:
        yield _sse_json_bytes(
            {
                "type": "response.output_text.delta",
                "response_id": response_id,
                "output_index": 0,
                "content_index": 0,
                "delta": answer,
            }
        )
    yield _sse_json_bytes(
        {
            "type": "response.output_text.done",
            "response_id": response_id,
            "output_index": 0,
            "content_index": 0,
            "text": answer,
        }
    )
    yield _sse_json_bytes(
        {
            "type": "response.completed",
            "response": {
                "id": response_id,
                "object": OPENAI_RESPONSE_OBJECT,
                "created": created,
                "status": "completed",
                "model": model_name,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                },
                "x_contextledger": _contextledger_meta(runtime),
            },
        }
    )
    yield _sse_done_bytes()


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


@lru_cache(maxsize=2048)
def _cached_embedding_vector(text: str, dim: int) -> tuple[float, ...]:
    base = text.encode("utf-8", errors="ignore")
    if not base:
        base = b" "

    values: list[float] = [0.0] * dim
    write_index = 0
    counter = 0
    while write_index < dim:
        digest = hashlib.sha256(base + counter.to_bytes(4, "little")).digest()
        for byte_value in digest:
            values[write_index] = _EMBEDDING_BYTE_TO_FLOAT[byte_value]
            write_index += 1
            if write_index >= dim:
                break
        counter += 1

    return tuple(values)


@lru_cache(maxsize=128)
def _cached_embeddings_payload(
    model_name: str,
    texts: tuple[str, ...],
) -> dict[str, Any]:
    data: list[dict[str, Any]] = []
    append_item = data.append
    total_prompt_tokens = 0
    for index, text in enumerate(texts):
        vector = _cached_embedding_vector(text, OPENAI_EMBEDDING_DIM)
        append_item(
            {
                "object": OPENAI_EMBEDDING_OBJECT,
                "index": index,
                "embedding": vector,
            }
        )
        total_prompt_tokens += _estimate_tokens_by_text(text)

    return {
        "object": "list",
        "data": data,
        "model": model_name,
        "usage": {
            "prompt_tokens": total_prompt_tokens,
            "total_tokens": total_prompt_tokens,
        },
    }


@lru_cache(maxsize=128)
def _cached_embeddings_payload_bytes(
    model_name: str,
    texts: tuple[str, ...],
) -> bytes:
    payload = _cached_embeddings_payload(model_name, texts)
    return _json_compact_bytes(payload)


def _normalize_embedding_inputs(input_value: Any) -> list[str] | None:
    if isinstance(input_value, str):
        text = input_value.strip()
        return [text] if text else None

    if not isinstance(input_value, list):
        return None

    result: list[str] = []
    append_text = result.append
    for item in input_value:
        if isinstance(item, str):
            stripped = item.strip()
            if stripped:
                append_text(stripped)
            continue

        if isinstance(item, dict):
            text = _extract_text_from_content(item.get("content"))
            if not text:
                raw_text = item.get("text")
                if isinstance(raw_text, str):
                    text = raw_text.strip()
            if text:
                append_text(text)

    return result or None


@router.post("/chat/completions", response_model=None)
def post_chat_completions(payload: dict[str, Any]) -> Response:
    raw_messages = payload.get("messages")
    if not isinstance(raw_messages, list) or not raw_messages:
        return _bad_request("`messages` must be a non-empty list.")

    prompt = _extract_prompt_from_messages(raw_messages)
    if not prompt:
        return _bad_request("No text content could be extracted from `messages`.")

    max_output_tokens = _coerce_positive_int(
        payload.get("max_tokens"),
        OPENAI_CHAT_DEFAULT_MAX_TOKENS,
    )
    stream = _coerce_bool(payload.get("stream"), False)

    model_name, runtime, completion_id = _run_compat_chat(
        payload=payload,
        prompt=prompt,
        max_output_tokens=max_output_tokens,
        stream=stream,
    )
    if stream:
        return StreamingResponse(
            _iter_chat_completions_stream(
                completion_id=completion_id,
                model_name=model_name,
                runtime=runtime,
            ),
            media_type="text/event-stream",
        )
    completion_payload = _build_chat_completions_payload(
        completion_id=completion_id,
        model_name=model_name,
        runtime=runtime,
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=completion_payload,
    )


@router.post("/responses", response_model=None)
def post_responses(payload: dict[str, Any]) -> Response:
    input_value = payload.get("input")
    prompt = _extract_prompt_from_responses_input(input_value)
    if not prompt:
        raw_messages = payload.get("messages")
        if isinstance(raw_messages, list):
            prompt = _extract_prompt_from_messages(raw_messages)
    if not prompt:
        return _bad_request("`input` must contain at least one non-empty text item.")

    max_output_tokens = _coerce_positive_int(
        payload.get("max_output_tokens", payload.get("max_tokens")),
        OPENAI_CHAT_DEFAULT_MAX_TOKENS,
    )
    stream = _coerce_bool(payload.get("stream"), False)

    model_name, runtime, _ = _run_compat_chat(
        payload=payload,
        prompt=prompt,
        max_output_tokens=max_output_tokens,
        stream=stream,
    )
    response_payload = _build_responses_payload(
        model_name=model_name,
        runtime=runtime,
    )
    if stream:
        return StreamingResponse(
            _iter_responses_stream(
                model_name=model_name,
                runtime=runtime,
            ),
            media_type="text/event-stream",
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response_payload,
    )


@router.post("/embeddings", response_model=None)
def post_embeddings(payload: dict[str, Any]) -> JSONResponse:
    input_value = payload.get("input")
    texts = _normalize_embedding_inputs(input_value)
    if not texts:
        return _bad_request("`input` must be a non-empty string or string array.")

    model_name = _normalize_optional_str(
        payload.get("model"),
        "contextledger-m1-embedding",
    )

    content_bytes = _cached_embeddings_payload_bytes(model_name, tuple(texts))

    return Response(
        status_code=status.HTTP_200_OK,
        content=content_bytes,
        media_type="application/json",
    )


@router.get("/models", response_model=None)
def get_models() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=_models_payload(),
    )
