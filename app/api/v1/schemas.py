"""Pydantic contracts for v1 API endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProviderInfo(BaseModel):
    chat: str
    embedding: str


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    provider: ProviderInfo


class ChatOptions(BaseModel):
    max_output_tokens: int = Field(default=1200, ge=1)
    stream: bool = False


class ChatRequest(BaseModel):
    project_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    options: ChatOptions = Field(default_factory=ChatOptions)


class BudgetMeta(BaseModel):
    max_context_tokens: int
    reserved_output_tokens: int
    used_input_tokens: int


class ChatMeta(BaseModel):
    request_id: str
    continuations: int
    quality_score: float
    retrieval_quality_score: float
    context_growth_ratio: float
    balance_mode: str
    fallback_mode: str
    budget: BudgetMeta


class UsedMemory(BaseModel):
    memory_id: str
    type: str
    score: float
    source_ref: str


class ChatResponse(BaseModel):
    answer: str
    meta: ChatMeta
    used_memories: list[UsedMemory] = Field(default_factory=list)


class ResumeRequest(BaseModel):
    project_id: str = Field(min_length=1)


class ResumeResponse(BaseModel):
    project_snapshot: str
    recent_decisions: list[str] = Field(default_factory=list)
    open_todos: list[str] = Field(default_factory=list)


class TimelineRequest(BaseModel):
    project_id: str = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = None


class TimelineItem(BaseModel):
    id: str
    type: str
    content: str
    timestamp: str


class TimelineResponse(BaseModel):
    items: list[TimelineItem] = Field(default_factory=list)
    next_cursor: str | None = None
