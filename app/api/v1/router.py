"""Versioned API router for ContextLedger v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.schemas import ChatRequest, ChatResponse, HealthResponse
from app.api.v1.service import build_chat_response, build_health_response

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return build_health_response()


@router.post("/chat", response_model=ChatResponse)
def post_chat(payload: ChatRequest) -> ChatResponse:
    return build_chat_response(payload)
