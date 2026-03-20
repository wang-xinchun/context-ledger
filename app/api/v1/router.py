"""Versioned API router for ContextLedger v1."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.v1.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ResumeRequest,
    ResumeResponse,
    TimelineRequest,
    TimelineResponse,
)
from app.api.v1.service import (
    build_chat_response,
    build_health_response,
    build_resume_response,
    build_timeline_response,
)

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return build_health_response()


@router.post("/chat", response_model=ChatResponse)
def post_chat(payload: ChatRequest) -> ChatResponse:
    return build_chat_response(payload)


@router.post("/resume", response_model=ResumeResponse)
def post_resume(payload: ResumeRequest) -> ResumeResponse:
    return build_resume_response(payload)


@router.get("/timeline", response_model=TimelineResponse)
def get_timeline(
    project_id: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> TimelineResponse:
    payload = TimelineRequest(
        project_id=project_id,
        limit=limit,
        cursor=cursor,
    )
    return build_timeline_response(payload)
