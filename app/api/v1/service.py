"""Service logic for v1 endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
from uuid import uuid4

from app.api.v1.schemas import (
    BudgetMeta,
    ChatMeta,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ProviderInfo,
    ResumeRequest,
    ResumeResponse,
    TimelineItem,
    TimelineRequest,
    TimelineResponse,
    UsedMemory,
)
from app.core import settings
from app.memory import ledger


PUNCTUATION_SYMBOLS = frozenset({",", ".", ";", ":", "?", "!", "，", "。", "？", "！"})
CODE_KEYWORDS = frozenset(
    {
        "def",
        "class",
        "select",
        "from",
        "where",
        "function",
        "import",
        "error",
        "exception",
    }
)
TOKEN_KIND_NONE = 0
TOKEN_KIND_ASCII = 1
TOKEN_KIND_CJK = 2
PROFILE_CACHE_CHAR_LIMIT = 4096
PROFILE_CACHE_SIZE = 512
ANCHOR_KEYWORDS = frozenset(
    {
        "project",
        "session",
        "todo",
        "risk",
        "milestone",
        "模块",
        "接口",
        "测试",
        "需求",
        "上线",
    }
)


@dataclass(frozen=True, slots=True)
class MessageProfile:
    """缓存消息特征，避免重复计算。"""

    token_count: int
    unique_token_count: int
    anchor_hits: int
    non_space_chars: int
    cjk_chars: int
    line_breaks: int
    punctuation_hits: int
    code_hint_hits: int
    complexity_ratio: float
    estimated_input_tokens: int


def build_health_response() -> HealthResponse:
    return HealthResponse(
        version=settings.APP_VERSION,
        provider=ProviderInfo(
            chat=settings.DEFAULT_CHAT_PROVIDER,
            embedding=settings.DEFAULT_EMBEDDING_PROVIDER,
        ),
    )


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def _is_cjk_code(code: int) -> bool:
    return (
        0x4E00 <= code <= 0x9FFF
        or 0x3400 <= code <= 0x4DBF
        or 0x3040 <= code <= 0x30FF
        or 0xAC00 <= code <= 0xD7AF
    )


def _token_char_kind(code: int) -> int:
    if code == 95 or 48 <= code <= 57 or 65 <= code <= 90 or 97 <= code <= 122:
        return TOKEN_KIND_ASCII
    if _is_cjk_code(code):
        return TOKEN_KIND_CJK
    return TOKEN_KIND_NONE


def _compute_message_profile(text: str) -> MessageProfile:
    """
    单次提取文本特征，供预算和评分共用。
    将原先多处重复扫描收敛为集中计算，降低运行时常数开销。
    """
    if not text:
        return MessageProfile(
            token_count=0,
            unique_token_count=0,
            anchor_hits=0,
            non_space_chars=0,
            cjk_chars=0,
            line_breaks=0,
            punctuation_hits=0,
            code_hint_hits=0,
            complexity_ratio=0.0,
            estimated_input_tokens=1,
        )

    non_space_chars = 0
    cjk_chars = 0
    line_breaks = 0
    punctuation_hits = 0
    backtick_count = 0

    token_count = 0
    latin_token_count = 0
    code_keyword_hits = 0
    anchor_hits = 0
    unique_tokens: set[str] = set()
    current_token_kind = TOKEN_KIND_NONE
    token_start = -1

    def _consume_token(start: int, end: int, token_kind: int) -> None:
        nonlocal token_count, latin_token_count, code_keyword_hits, anchor_hits
        normalized = text[start:end].lower()
        token_count += 1
        unique_tokens.add(normalized)

        if normalized in ANCHOR_KEYWORDS:
            anchor_hits += 1
        if token_kind == TOKEN_KIND_ASCII:
            latin_token_count += 1
            if normalized in CODE_KEYWORDS:
                code_keyword_hits += 1

    # 单次线性扫描：同时完成字符统计 + token 切分，减少正则二次扫描开销。
    for index, char in enumerate(text):
        if char == "\n":
            line_breaks += 1
        if char in PUNCTUATION_SYMBOLS:
            punctuation_hits += 1
        if char == "`":
            backtick_count += 1
        if not char.isspace():
            non_space_chars += 1

        code = ord(char)
        token_kind = _token_char_kind(code)
        if token_kind == TOKEN_KIND_CJK:
            cjk_chars += 1

        if token_kind == current_token_kind and token_kind != TOKEN_KIND_NONE:
            continue

        if current_token_kind != TOKEN_KIND_NONE and token_start >= 0:
            _consume_token(token_start, index, current_token_kind)

        if token_kind != TOKEN_KIND_NONE:
            token_start = index
        current_token_kind = token_kind

    if current_token_kind != TOKEN_KIND_NONE and token_start >= 0:
        _consume_token(token_start, len(text), current_token_kind)

    code_hint_hits = min(code_keyword_hits, 8) + (2 if backtick_count >= 3 else 1 if backtick_count > 0 else 0)

    complexity_ratio = _clamp(
        min(line_breaks / 10, 1.0) * 0.35
        + min(punctuation_hits / 24, 1.0) * 0.25
        + min(code_hint_hits / 8, 1.0) * 0.40,
        0.0,
        1.0,
    )

    base_tokens = latin_token_count + math.ceil(cjk_chars * 0.9)
    if base_tokens <= 0:
        base_tokens = max(1, math.ceil(non_space_chars / 4))
    complexity_bonus = math.ceil(non_space_chars * 0.06 * complexity_ratio)
    estimated_input_tokens = max(1, base_tokens + complexity_bonus)

    return MessageProfile(
        token_count=token_count,
        unique_token_count=len(unique_tokens),
        anchor_hits=anchor_hits,
        non_space_chars=non_space_chars,
        cjk_chars=cjk_chars,
        line_breaks=line_breaks,
        punctuation_hits=punctuation_hits,
        code_hint_hits=code_hint_hits,
        complexity_ratio=complexity_ratio,
        estimated_input_tokens=estimated_input_tokens,
    )


@lru_cache(maxsize=PROFILE_CACHE_SIZE)
def _build_message_profile_cached(text: str) -> MessageProfile:
    return _compute_message_profile(text)


def _build_message_profile(text: str) -> MessageProfile:
    # 高频短消息走缓存，避免在预算、评分、多次重试中重复计算。
    if len(text) <= PROFILE_CACHE_CHAR_LIMIT:
        return _build_message_profile_cached(text)
    return _compute_message_profile(text)


def _message_complexity_ratio(text: str) -> float:
    return _build_message_profile(text).complexity_ratio


def _estimate_input_tokens(text: str) -> int:
    return _build_message_profile(text).estimated_input_tokens


def _choose_reserved_output_tokens(
    max_output_tokens: int,
    default_reserved_tokens: int,
    max_context_tokens: int,
    profile: MessageProfile,
) -> int:
    # 在“请求上限 / 系统默认 / 上下文压力”之间平衡输出预算。
    reserve_cap = max_context_tokens if max_context_tokens == 1 else max_context_tokens - 1
    requested_cap = max(1, max_output_tokens)
    desired_base = min(requested_cap, default_reserved_tokens)

    # 复杂输入提高输出预算，减少答案被截断概率。
    complexity_factor = 1.0 + 0.25 * profile.complexity_ratio
    desired_tokens = math.ceil(desired_base * complexity_factor)

    input_pressure = profile.estimated_input_tokens / max_context_tokens
    if input_pressure >= 0.85:
        desired_tokens = math.floor(desired_tokens * 0.65)
    elif input_pressure >= 0.65:
        desired_tokens = math.floor(desired_tokens * 0.8)

    floor_by_context = min(128, max(1, max_context_tokens // 16))
    clamped = _clamp(
        desired_tokens,
        low=min(floor_by_context, requested_cap),
        high=min(requested_cap, reserve_cap),
    )
    return int(clamped)


def _build_budget(
    max_output_tokens: int,
    message: str,
    *,
    profile: MessageProfile | None = None,
) -> BudgetMeta:
    profile = profile or _build_message_profile(message)
    max_context_tokens = max(1, settings.DEFAULT_MAX_CONTEXT_TOKENS)
    default_reserved_tokens = max(1, settings.DEFAULT_RESERVED_OUTPUT_TOKENS)

    reserved_output_tokens = _choose_reserved_output_tokens(
        max_output_tokens=max_output_tokens,
        default_reserved_tokens=default_reserved_tokens,
        max_context_tokens=max_context_tokens,
        profile=profile,
    )

    available_input_tokens = max_context_tokens - reserved_output_tokens
    used_input_tokens = min(profile.estimated_input_tokens, available_input_tokens)

    return BudgetMeta(
        max_context_tokens=max_context_tokens,
        reserved_output_tokens=reserved_output_tokens,
        used_input_tokens=used_input_tokens,
    )


def _estimate_retrieval_quality_score(profile: MessageProfile) -> float:
    """无检索后端时，用查询信号质量做占位评分。"""
    if profile.token_count <= 0:
        return 0.2

    unique_ratio = profile.unique_token_count / profile.token_count
    score = (
        0.35
        + unique_ratio * 0.35
        + min(profile.anchor_hits / 4, 1.0) * 0.2
        + profile.complexity_ratio * 0.1
    )
    return round(_clamp(score, 0.0, 1.0), 3)


def _determine_fallback_mode(
    requested_output_tokens: int,
    reserved_output_tokens: int,
    context_growth_ratio: float,
) -> str:
    if reserved_output_tokens < requested_output_tokens:
        return "output_clamped"
    if context_growth_ratio >= 0.92:
        return "input_compacted"
    return "none"


def _determine_balance_mode(
    context_growth_ratio: float,
    requested_output_tokens: int,
    fallback_mode: str,
) -> str:
    if context_growth_ratio >= 0.82:
        return "quality_first"
    if (
        context_growth_ratio <= 0.08
        and requested_output_tokens >= settings.DEFAULT_RESERVED_OUTPUT_TOKENS
        and fallback_mode == "none"
    ):
        return "growth_first"
    return "balanced"


def _estimate_quality_score(
    context_growth_ratio: float,
    retrieval_quality_score: float,
    fallback_mode: str,
    profile: MessageProfile,
) -> float:
    penalty = 0.0
    if fallback_mode == "output_clamped":
        penalty += 0.08
    elif fallback_mode == "input_compacted":
        penalty += 0.12

    score = (
        0.62
        + retrieval_quality_score * 0.22
        + (1 - context_growth_ratio) * 0.12
        + profile.complexity_ratio * 0.08
        - penalty
    )
    return round(_clamp(score, 0.0, 1.0), 3)


def build_chat_response(payload: ChatRequest) -> ChatResponse:
    request_id = f"req_{uuid4().hex[:12]}"
    profile = _build_message_profile(payload.message)
    budget = _build_budget(
        payload.options.max_output_tokens,
        payload.message,
        profile=profile,
    )

    context_growth_ratio = round(
        budget.used_input_tokens / max(1, budget.max_context_tokens),
        3,
    )
    retrieval_quality_score = _estimate_retrieval_quality_score(profile)
    fallback_mode = _determine_fallback_mode(
        requested_output_tokens=payload.options.max_output_tokens,
        reserved_output_tokens=budget.reserved_output_tokens,
        context_growth_ratio=context_growth_ratio,
    )
    balance_mode = _determine_balance_mode(
        context_growth_ratio=context_growth_ratio,
        requested_output_tokens=payload.options.max_output_tokens,
        fallback_mode=fallback_mode,
    )
    quality_score = _estimate_quality_score(
        context_growth_ratio=context_growth_ratio,
        retrieval_quality_score=retrieval_quality_score,
        fallback_mode=fallback_mode,
        profile=profile,
    )

    answer = f"[contextledger:m1] message received: {payload.message}"
    used_memories: list[UsedMemory] = []
    try:
        # memory 写入异常不应阻断主聊天路径，先降级返回结果。
        used_memories = ledger.record_chat_turn(
            project_id=payload.project_id,
            session_id=payload.session_id,
            request_id=request_id,
            user_message=payload.message,
            assistant_answer=answer,
            used_input_tokens=budget.used_input_tokens,
        )
    except Exception:
        used_memories = []

    return ChatResponse(
        answer=answer,
        meta=ChatMeta(
            request_id=request_id,
            continuations=0,
            quality_score=quality_score,
            retrieval_quality_score=retrieval_quality_score,
            context_growth_ratio=context_growth_ratio,
            balance_mode=balance_mode,
            fallback_mode=fallback_mode,
            budget=budget,
        ),
        used_memories=used_memories,
    )


def build_resume_response(payload: ResumeRequest) -> ResumeResponse:
    snapshot = ledger.build_resume(payload.project_id)
    return ResumeResponse(
        project_snapshot=str(snapshot.get("project_snapshot", "")),
        recent_decisions=[str(item) for item in snapshot.get("recent_decisions", [])],
        open_todos=[str(item) for item in snapshot.get("open_todos", [])],
    )


def build_timeline_response(payload: TimelineRequest) -> TimelineResponse:
    timeline = ledger.build_timeline(
        payload.project_id,
        limit=payload.limit,
        cursor=payload.cursor,
    )
    raw_items = timeline["items"]
    return TimelineResponse(
        items=[
            TimelineItem(
                id=item["id"],
                type=item["type"],
                content=item["content"],
                timestamp=item["timestamp"],
            )
            for item in raw_items
        ],
        next_cursor=timeline["next_cursor"],
    )
