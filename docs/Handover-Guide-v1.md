# Handover Guide v1

## 1. Purpose
This guide ensures the project can be transferred to another engineer with minimal context loss.

## 2. Current Scope Snapshot
1. Stage: `Documentation complete, implementation not started`
2. Runtime target (test): `LM Studio + local Qwen model`
3. Final direction: `Provider-pluggable ContextLedger platform`

## 3. What Is Done
1. Product and architecture definitions are complete.
2. API, data model, config, deployment, and test plans are drafted.
3. Evolvability strategy (versioning, migration, rollback) is defined.

## 4. What Is Not Done
1. Repository code scaffold.
2. Endpoint implementation.
3. DB migration files.
4. Automated tests.

## 5. Immediate Next Tasks (Execution Order)
1. Initialize backend project scaffold (`FastAPI + SQLAlchemy + Alembic`).
2. Implement `/v1/health`.
3. Implement `/v1/chat` minimal loop without retrieval.
4. Add memory write path and `/v1/resume`.
5. Add context budget planner and degrade policy.

## 6. Required Decisions Before Coding
1. Final package manager and project toolchain (`uv` or `poetry`).
2. FAISS vs Qdrant local default for v1.
3. Initial embedding model selection and dimensions.

## 7. Handover Checklist
1. Read [PRD v1](./PRD-v1.md).
2. Read [Architecture v1](./Architecture-v1.md).
3. Read [ContextLedger Design v1](./ContextLedger-Design-v1.md).
4. Confirm acceptance criteria from [Test Plan v1](./Test-Plan-v1.md).
5. Update [Progress Tracker](./Progress-Tracker.md) before and after each development session.

## 8. Operational Notes
1. Keep API and config backward compatible in `v1`.
2. Any schema change must include Alembic migration and doc update.
3. No provider-specific logic in core orchestration.

## 9. Release Readiness Gate (for first runnable version)
1. `/v1/chat` works with local LM Studio.
2. Overflow handling never crashes request path.
3. `/v1/resume` returns valid snapshot within target latency.
4. Logs include request id and token budget summary.
