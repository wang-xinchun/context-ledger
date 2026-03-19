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
- Last updated: `2026-03-19`
- Stage: `Planning / Documentation`
- Code status: `Not implemented yet`
- Test profile: `LM Studio + local Qwen model`
- Final target: `Provider-pluggable platform (not bound to one runtime)`
- Overall completion: `38%`

## Milestone Status
| Milestone | Status | Notes |
|---|---|---|
| M1 Chat minimal loop | Not Started | Build scaffold + `/v1/health` + `/v1/chat` basic |
| M2 Context budget engine | Not Started | Add overflow degrade and output reserve |
| M3 Response stability | Not Started | Two-phase generation + auto continuation |
| M4 Timeline + regression | Not Started | Timeline endpoint and quality baseline |
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
- [Product Requirements v1](./docs/PRD-v1.md)
- [Architecture v1](./docs/Architecture-v1.md)
- [API Spec v1](./docs/API-Spec-v1.md)
- [Deployment Guide v1](./docs/Deployment-Guide-v1.md)
- [Progress Tracker](./docs/Progress-Tracker.md)
- [Handover Guide](./docs/Handover-Guide-v1.md)
- [Session Messages Log](./MESSAGES.md)

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
1. Scaffold backend project (`FastAPI + SQLAlchemy + Alembic`).
2. Implement `/v1/health`.
3. Implement minimal `/v1/chat` request path with U1 telemetry fields reserved.
4. Implement `Balance Controller` (`quality_score` vs `context_growth_ratio`) with mode switching.
5. Add OpenAI-compatible gateway endpoints and compatibility conformance tests.
6. Keep all new files aligned with `docs/File-Management-Plan-v1.md`.

## License
TBD
