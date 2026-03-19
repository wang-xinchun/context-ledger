"""OpenAI-compatible gateway skeleton endpoints."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/openai/v1", tags=["openai-compatibility"])


def _not_implemented(endpoint: str) -> JSONResponse:
    request_id = f"req_{uuid4().hex[:12]}"
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "error": {
                "code": "NOT_IMPLEMENTED",
                "message": f"{endpoint} is reserved for M1 compatibility stage.",
                "request_id": request_id,
            }
        },
    )


@router.post("/chat/completions", response_model=None)
def post_chat_completions() -> JSONResponse:
    return _not_implemented("/openai/v1/chat/completions")


@router.post("/responses", response_model=None)
def post_responses() -> JSONResponse:
    return _not_implemented("/openai/v1/responses")


@router.post("/embeddings", response_model=None)
def post_embeddings() -> JSONResponse:
    return _not_implemented("/openai/v1/embeddings")


@router.get("/models", response_model=None)
def get_models() -> JSONResponse:
    return _not_implemented("/openai/v1/models")
