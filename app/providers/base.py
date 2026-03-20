"""Provider contracts for chat generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ChatProviderRequest:
    request_id: str
    project_id: str
    session_id: str
    message: str
    max_output_tokens: int
    reserved_output_tokens: int
    used_input_tokens: int
    stream: bool


@dataclass(frozen=True, slots=True)
class ChatProviderResult:
    answer: str
    provider_name: str
    model_name: str
    latency_ms: int


class ChatProvider(Protocol):
    def generate(self, request: ChatProviderRequest) -> ChatProviderResult: ...

