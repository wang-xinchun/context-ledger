# ContextLedger

ContextLedger is a local-first memory layer for long-running AI work.  
It provides near-unlimited context experience by combining retrieval, context budgeting, continuation orchestration, and persistent memory logs.

## Why This Project
- Long chats lose context when model windows are small (for example `4096` tokens).
- Users repeat project background across sessions.
- Local setups (LM Studio / Ollama) usually have no strong memory orchestration.

ContextLedger solves this with a middle layer:

`UI -> ContextLedger -> LLM -> ContextLedger -> UI`

## Project Control Panel
- Last updated: `2026-03-20`
- Stage: `M1 Implementation (In Progress)`
- Code status: M1 health/chat/resume/timeline minimal path is runnable; `/v1/chat` runs through provider-adapter registry, and OpenAI compatibility layer now supports `/openai/v1/chat/completions`, `/openai/v1/responses`, `/openai/v1/embeddings`, `/openai/v1/models` with hot-path optimizations (reverse early-stop prompt extraction, lightweight runtime pipeline call, cached model payload, deterministic embedding cache); SQL read-path optimization + index migration (`20260320_0002`) validated on Python 3.12 runtime
- Test profile: `LM Studio + local Qwen model`
- Final target: `Provider-pluggable platform (not bound to one runtime)`
- Overall completion: `99%`

## Milestone Status
| Milestone | Status | Notes |
|---|---|---|
| M1 Chat minimal loop | In Progress | `/v1/health` + `/v1/chat` + `/v1/resume` + `/v1/timeline` minimal path implemented; SQL dual-write + SQL read repository baseline is available (read cutover controlled by flag) |
| M2 Context budget engine | Not Started | Add overflow degrade and output reserve |
| M3 Response stability | Not Started | Two-phase generation + auto continuation |
| M4 Timeline + regression | In Progress | Timeline endpoint is live; regression expansion and quality baseline still pending |
| M5 Evolvability extension | Not Started | Provider expansion and team deployment profile |
| U1 Advanced runtime control | Planned | Adaptive retrieval + uncertainty fields + telemetry |
| U2 Hybrid intelligence layer | Planned | Memory graph + policy-as-code + hybrid retrieval |
| U3 Release-grade quality system | Planned | Regression CI gate + learned packing + SLO release |

## Quick Links
- [Documentation Index](./docs/README.md)
- [Research Scan 2026-03-19](./docs/Research-Scan-2026-03-19.md)
- [Tech Upgrade v2](./docs/Tech-Upgrade-v2.md)
- [Compatibility Strategy v1](./docs/Compatibility-Strategy-v1.md)
- [File Management Plan v1](./docs/File-Management-Plan-v1.md)
- [Operational Workflow v1](./docs/Operational-Workflow-v1.md)
- [Product Requirements v1](./docs/PRD-v1.md)
- [Architecture v1](./docs/Architecture-v1.md)
- [API Spec v1](./docs/API-Spec-v1.md)
- [Deployment Guide v1](./docs/Deployment-Guide-v1.md)
- [Progress Tracker](./docs/Progress-Tracker.md)
- [Handover Guide](./docs/Handover-Guide-v1.md)
- [Session Messages Log](./MESSAGES.md)

## Database Migration Baseline
- Alembic config: [`alembic.ini`](./alembic.ini)
- Migration scripts: [`alembic/`](./alembic)
- Initial revision: [`20260320_0001_initial_schema.py`](./alembic/versions/20260320_0001_initial_schema.py)

## Core Capabilities (v1 Scope)
- Auto memory ingestion from chat turns
- Hybrid retrieval for project context
- Strict token budget compiler with output reserve
- Two-phase generation and auto-continuation
- Resume by project in new sessions
- Timeline for decisions, risks, and todos

## Handover Standard
1. Every session must update [Progress Tracker](./docs/Progress-Tracker.md).
2. Any architecture or API changes must update related docs in `docs/`.
3. Any schema change must include migration plan and test impact.
4. Before transfer, verify [Handover Guide](./docs/Handover-Guide-v1.md) checklist.

## Immediate Next Action
1. Start staged runtime validation for SQL read cutover (`CONTEXTLEDGER_SQL_READ_ENABLED=true`) using benchmark baseline and parity checks.
2. Add streaming compatibility conformance tests and performance checks for OpenAI-compatible endpoints.
3. Extend provider registry with real network adapters and timeout/retry guards behind feature flags.
4. Extend benchmark checks for profile extraction and chat budget hot paths.
5. Fix packaging so `pip install -e .[dev]` works without manual dependency fallbacks.

## License
TBD
