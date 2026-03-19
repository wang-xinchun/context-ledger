# Tech Stack v1

## 1. 选型原则
1. 本地可跑，个人可用。
2. 架构可演进到团队部署。
3. Provider 插件化，避免模型绑定。
4. 以工程稳定性优先。

## 2. 最终确定技术栈
## 2.1 后端核心
- Language: `Python 3.12`
- API Framework: `FastAPI`
- ASGI Server: `Uvicorn`
- Background Jobs: `Celery`（后续可选 `RQ`，v1 默认 Celery）
- Validation: `Pydantic v2`
- ORM: `SQLAlchemy 2.x`
- DB Migration: `Alembic`

## 2.2 记忆与检索
- Primary DB (v1): `SQLite`（个人本地）
- Primary DB (team): `PostgreSQL 16`
- Vector Store (v1): `FAISS`（本地文件索引）
- Vector Store (team): `Qdrant`
- Hybrid Retrieval: `BM25 + Vector + Rule Filter`
- Rerank: 可插拔（v1 默认 `cross-encoder` rerank 可选开启）
- Retrieval Quality Gate: 引入检索质量分（低分触发 query rewrite/补检索）
- Context Packing: 位置感知打包（高价值片段优先放在开头/末尾）

## 2.3 LLM / Embedding 接入层
- Provider Abstraction: 自研 `Provider Registry`
- Chat Provider (test): `LM Studio OpenAI-compatible API`
- Chat Provider (optional): `Ollama`
- Embedding Provider (v1 default): 本地 embedding 模型（通过同一 Provider 接口）

## 2.4 网关与协议
- API: `REST (JSON)`
- Streaming: `Server-Sent Events (SSE)`
- OpenAI-Compatible Gateway: `/openai/v1/chat/completions`, `/openai/v1/responses`, `/openai/v1/models`, `/openai/v1/embeddings`
- Agent Integration: `MCP Server`（v1.1）

## 2.5 前端与客户端
- Web UI: `Next.js 15 + TypeScript + Tailwind CSS`
- CLI: `Typer`（Python）

## 2.6 缓存与队列
- Cache: `Redis`（v1 可选，team 推荐）
- Queue Broker: `Redis`
- Async Workers: `Celery Worker + Beat`（索引、摘要、压缩异步化）

## 2.7 观测与日志
- Structured Logging: `structlog`
- Metrics: `Prometheus`
- Dashboards: `Grafana`
- Tracing (phase 2): `OpenTelemetry`
- Key SLO Metrics:
  - `truncated_answer_rate`
  - `continuation_rounds_p95`
  - `retrieval_quality_score`
  - `resume_latency_p95`

## 2.8 质量保障
- Unit/Integration Test: `pytest`
- API Test: `httpx + pytest`
- E2E Test: `Playwright`
- Lint/Format: `ruff + black`（Python）, `eslint + prettier`（TS）
- Type Check: `mypy`（Python）, `tsc`（TS）

## 2.9 部署
- Local: `Docker Compose`
- Team/Prod: `Kubernetes`（Helm）
- Reverse Proxy: `Nginx` 或 `Traefik`
- Security Baseline:
  - 项目根目录路径白名单
  - 禁止越界文件操作
  - 审计日志记录所有 ingestion/delete 请求

## 3. 版本化与可更新策略（技术栈层）
1. API 路由版本：`/v1` 起步。
2. DB 迁移：仅通过 Alembic 管理。
3. Provider 接口：语义化版本（`provider_api_version`）。
4. 发布策略：蓝绿/灰度 + 回滚脚本。

## 4. v1 最小交付依赖（你当前就能跑）
1. `FastAPI + Uvicorn`
2. `SQLite + FAISS`
3. `LM Studio (Qwen32B)` 作为 Chat Provider
4. `Typer CLI`（先于 Web UI）
5. `Docker Compose`

## 5. 暂不采用（避免复杂度失控）
1. LangChain 全家桶（只在需要时局部引入）
2. 微服务拆分（v1 保持单体模块化）
3. 多云托管能力（放到 phase 2）
