# API Spec v1

Base URL: `/v1`

Compatibility Base URL: `/openai/v1` (OpenAI-compatible gateway)

## 1. POST `/chat`
### Request
```json
{
  "project_id": "proj_001",
  "session_id": "sess_001",
  "message": "继续昨天的重构任务，先修复登录模块",
  "options": {
    "max_output_tokens": 1200,
    "stream": false
  }
}
```

### Response
```json
{
  "answer": "已恢复上下文。建议先处理登录校验分支...",
  "meta": {
    "request_id": "req_123",
    "continuations": 1,
    "quality_score": 0.89,
    "retrieval_quality_score": 0.72,
    "context_growth_ratio": 0.68,
    "balance_mode": "balanced",
    "fallback_mode": "none",
    "budget": {
      "max_context_tokens": 4096,
      "reserved_output_tokens": 900,
      "used_input_tokens": 3012
    }
  },
  "used_memories": [
    {
      "memory_id": "mem_1",
      "type": "decision",
      "score": 0.91,
      "source_ref": "sess_0009:turn_14"
    }
  ]
}
```

## 2. POST `/resume`
### Request
```json
{
  "project_id": "proj_001"
}
```

### Response
```json
{
  "project_snapshot": "当前已完成登录页重构70%，剩余鉴权拦截器。",
  "recent_decisions": [
    "暂不引入Redis缓存，先保证功能稳定。"
  ],
  "open_todos": [
    "修复登录模块异常分支",
    "补充登录集成测试"
  ]
}
```

## 3. GET `/timeline`
Query: `project_id`, `limit`, `cursor`

### Response
```json
{
  "items": [
    {
      "id": "evt_101",
      "type": "decision",
      "content": "登录重构采用中间件方案",
      "timestamp": "2026-03-19T08:33:10Z"
    }
  ],
  "next_cursor": "evt_100"
}
```

## 4. GET `/health`
### Response
```json
{
  "status": "ok",
  "version": "0.1.0",
  "provider": {
    "chat": "lmstudio",
    "embedding": "local"
  }
}
```

## 5. Compatibility Endpoints (OpenAI-style)
1. `POST /openai/v1/chat/completions`
2. `POST /openai/v1/responses`
3. `POST /openai/v1/embeddings`
4. `GET /openai/v1/models`

Notes:
1. ContextLedger-specific metadata is returned in compatible extension fields where possible.
2. If client cannot consume extension fields, core OpenAI-compatible payload remains valid.
3. For provider capability gaps, fallback behavior is surfaced via `finish_reason` and server logs.

## 6. Error Model
```json
{
  "error": {
    "code": "BUDGET_OVERFLOW_GUARD",
    "message": "cannot satisfy minimum output reserve",
    "request_id": "req_123"
  }
}
```

## 7. Error Codes
1. `INVALID_REQUEST`
2. `PROJECT_NOT_FOUND`
3. `SESSION_NOT_FOUND`
4. `PROVIDER_TIMEOUT`
5. `PROVIDER_UNAVAILABLE`
6. `BUDGET_OVERFLOW_GUARD`
7. `MEMORY_WRITE_FAILED`
8. `RETRIEVAL_LOW_CONFIDENCE`
9. `SAFETY_GUARD_BLOCKED`
