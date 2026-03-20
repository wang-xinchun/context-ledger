# MESSAGES

This file is the cross-session operation log for collaboration and handover.

## Logging Rules
1. Add one new entry for each meaningful operation batch.
2. Keep entries append-only (do not rewrite history).
3. Record concrete next actions and blockers.

## Entry Template
```md
## [YYYY-MM-DD HH:MM] Session Note
- Operator:
- Summary:
- Files changed:
  - path/to/file
- Decisions:
  - ...
- Next actions:
  1. ...
- Blockers:
  - None / ...
```

## [2026-03-19 00:00] Session Note
- Operator: Codex
- Summary: Created full v1 documentation baseline and project control README.
- Files changed:
  - README.md
  - docs/README.md
  - docs/PRD-v1.md
  - docs/Architecture-v1.md
  - docs/API-Spec-v1.md
  - docs/Data-Model-v1.md
  - docs/Config-Spec-v1.md
  - docs/Deployment-Guide-v1.md
  - docs/Development-Guide-v1.md
  - docs/Test-Plan-v1.md
  - docs/Roadmap-v1.md
  - docs/ContextLedger-Design-v1.md
  - docs/Extensibility-and-Upgrade-Plan-v1.md
  - docs/Tech-Stack-v1.md
  - docs/Progress-Tracker.md
  - docs/Handover-Guide-v1.md
- Decisions:
  - Keep `LM Studio + Qwen32B` as test profile only.
  - Final architecture remains provider-pluggable.
  - Token budget with output reserve is mandatory.
- Next actions:
  1. Start M1 code scaffold (`FastAPI + SQLAlchemy + Alembic`).
  2. Implement `/v1/health` and minimal `/v1/chat`.
- Blockers:
  - None

## [2026-03-19 00:30] Session Note
- Operator: Codex
- Summary: Performed web research on GitHub community practices and papers, then updated technical documentation details.
- Files changed:
  - README.md
  - docs/README.md
  - docs/Research-Scan-2026-03-19.md
  - docs/PRD-v1.md
  - docs/Architecture-v1.md
  - docs/API-Spec-v1.md
  - docs/Config-Spec-v1.md
  - docs/Deployment-Guide-v1.md
  - docs/Tech-Stack-v1.md
  - docs/Test-Plan-v1.md
  - docs/Roadmap-v1.md
  - docs/ContextLedger-Design-v1.md
  - docs/Progress-Tracker.md
- Decisions:
  - Introduce retrieval quality gate with corrective fallback path.
  - Add position-aware context packing to reduce mid-context information loss.
  - Add async indexing pipeline and explicit file safety guard.
- Next actions:
  1. Implement M1 scaffold with metrics fields for retrieval and continuation.
  2. Keep thresholds configurable for tuning.
- Blockers:
  - None

## [2026-03-19 01:00] Session Note
- Operator: Codex
- Summary: Upgraded technical direction to v2-level architecture and integrated advanced milestones into project control docs.
- Files changed:
  - README.md
  - docs/README.md
  - docs/PRD-v1.md
  - docs/Roadmap-v1.md
  - docs/Progress-Tracker.md
  - docs/Tech-Upgrade-v2.md
- Decisions:
  - Approve v2 capability pack: adaptive retrieval, memory graph, uncertainty-aware flow, policy-as-code, regression CI.
  - Keep rollout staged via U1/U2/U3 after initial M-series baseline.
- Next actions:
  1. Implement M1 scaffold with compatibility hooks for U1 metrics and response fields.
  2. Define first version of uncertainty scoring function and thresholds.
- Blockers:
  - None

## [2026-03-19 01:05] Session Note
- Operator: Codex
- Summary: Synced README control panel completion and immediate action with v2 planning state.
- Files changed:
  - README.md
- Decisions:
  - Keep progress numbers consistent with `docs/Progress-Tracker.md`.
- Next actions:
  1. Begin M1 scaffold with U1-compatible response metadata.
- Blockers:
  - None

## [2026-03-19 01:20] Session Note
- Operator: Codex
- Summary: Formalized quality-vs-context-growth balance mechanism into design, config, API, and v2 upgrade docs.
- Files changed:
  - README.md
  - docs/ContextLedger-Design-v1.md
  - docs/Config-Spec-v1.md
  - docs/API-Spec-v1.md
  - docs/Tech-Upgrade-v2.md
- Decisions:
  - Introduce `Balance Controller` with three modes: `quality_first`, `balanced`, `growth_first`.
  - Expose `context_growth_ratio` and `balance_mode` in chat response metadata.
- Next actions:
  1. Implement runtime mode switching logic and metric collection in M1/M2 scaffold.
- Blockers:
  - None

## [2026-03-19 01:40] Session Note
- Operator: Codex
- Summary: Upgraded project compatibility requirements to release-gated standards for mainstream LLM usage scenarios.
- Files changed:
  - README.md
  - docs/README.md
  - docs/Compatibility-Strategy-v1.md
  - docs/API-Spec-v1.md
  - docs/Tech-Stack-v1.md
  - docs/Test-Plan-v1.md
  - docs/Roadmap-v1.md
  - docs/Progress-Tracker.md
- Decisions:
  - OpenAI-compatible gateway is now a primary integration path.
  - Compatibility conformance tests are required release gates.
  - MCP remains required for agent ecosystem compatibility.
- Next actions:
  1. Implement `/openai/v1/chat/completions` gateway skeleton in M1.
  2. Add protocol conformance tests for Python/JS SDK and streaming.
- Blockers:
  - None

## [2026-03-19 01:45] Session Note
- Operator: Codex
- Summary: Aligned README completion percentage with Progress Tracker after compatibility update.
- Files changed:
  - README.md
- Decisions:
  - Keep project control panel values synchronized with tracker after each doc update.
- Next actions:
  1. Start implementation with compatibility-first gateway skeleton.
- Blockers:
  - None

## [2026-03-19 02:10] Session Note
- Operator: Codex
- Summary: Completed file management and repository planning baseline with standardized directory structure, templates, and governance docs.
- Files changed:
  - .gitignore
  - configs/config.example.yaml
  - configs/policies/policy.example.rego
  - docs/File-Management-Plan-v1.md
  - docs/README.md
  - docs/Development-Guide-v1.md
  - docs/Progress-Tracker.md
  - README.md
  - scripts/README.md
  - infra/README.md
  - app/* (directory scaffold)
  - tests/* (directory scaffold)
  - configs/* (directory scaffold)
  - infra/* (directory scaffold)
  - examples/* (directory scaffold)
  - data/.gitkeep
  - logs/.gitkeep
- Decisions:
  - Enforce module boundaries via `docs/File-Management-Plan-v1.md`.
  - Keep runtime artifacts under `data/` and `logs/` out of VCS.
- Next actions:
  1. Begin M1 implementation in `app/` with matching tests in `tests/`.
  2. Keep every future file addition aligned with the new structure.
- Blockers:
  - None

## [2026-03-19 02:30] Session Note
- Operator: Codex
- Summary: Standardized project naming to `ContextLedger` and renamed core design document accordingly.
- Files changed:
  - README.md
  - docs/README.md
  - docs/ContextLedger-Design-v1.md (renamed from `docs/MemoryProxy-Design-v1.md`)
  - docs/Compatibility-Strategy-v1.md
  - docs/Deployment-Guide-v1.md
  - docs/Handover-Guide-v1.md
  - docs/Research-Scan-2026-03-19.md
  - docs/Tech-Upgrade-v2.md
  - docs/Progress-Tracker.md
- Decisions:
  - Official project name: `ContextLedger`.
  - Recommended GitHub repository slug: `context-ledger`.
- Next actions:
  1. Initialize git in project directory and create remote repo `context-ledger`.
  2. Push current documentation baseline.
- Blockers:
  - None

## [2026-03-19 22:26] Session Note
- Operator: Codex
- Summary: Consolidated operational conventions into a single workflow document and linked it from repository indexes for daily execution consistency.
- Files changed:
  - docs/Operational-Workflow-v1.md
  - README.md
  - docs/README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Use `docs/Operational-Workflow-v1.md` as the primary day-to-day execution checklist.
  - Keep `README.md`, `docs/Progress-Tracker.md`, and `MESSAGES.md` synchronized at every session close.
- Next actions:
  1. Start M1 runnable scaffold under `app/`.
  2. Implement `/v1/health` and add corresponding tests.
- Blockers:
  - None

## [2026-03-19 23:09] Session Note
- Operator: Codex
- Summary: Started M1 implementation by adding runnable FastAPI scaffold, `/v1/health`, minimal `/v1/chat` with reserved telemetry metadata, OpenAI-compatible skeleton endpoints, and initial API tests.
- Files changed:
  - app/main.py
  - app/core/settings.py
  - app/api/__init__.py
  - app/api/v1/__init__.py
  - app/api/v1/schemas.py
  - app/api/v1/service.py
  - app/api/v1/router.py
  - app/compatibility/__init__.py
  - app/compatibility/openai_router.py
  - tests/integration/test_v1_health.py
  - tests/integration/test_v1_chat.py
  - tests/compatibility/test_openai_gateway_skeleton.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep compatibility endpoints as explicit `501 NOT_IMPLEMENTED` skeletons for current M1 stage.
  - Reserve telemetry fields in chat response shape now to reduce refactor cost in M2/U1.
- Next actions:
  1. Install dev dependencies and run `pytest`.
  2. Implement `/v1/resume` and memory write placeholder path.
  3. Start SQLAlchemy + Alembic baseline integration.
- Blockers:
  - Python environment missing `pytest`, so automated tests were not executable in this session.

## [2026-03-19 23:27] Session Note
- Operator: Codex
- Summary: Applied immediate code review fixes for compatibility error contract and chat budget consistency, then expanded compatibility and budget regression tests.
- Files changed:
  - app/compatibility/openai_router.py
  - app/api/v1/service.py
  - tests/compatibility/test_openai_gateway_skeleton.py
  - tests/integration/test_v1_chat.py
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Return OpenAI-compatible skeleton errors as top-level `error` payload with `request_id` instead of nested FastAPI `detail`.
  - Enforce budget invariant in scaffold stage: `used_input_tokens + reserved_output_tokens <= max_context_tokens`.
- Next actions:
  1. Set up Python 3.12 + dependencies (`fastapi`, `pytest`) and run tests.
  2. Continue M1 with `/v1/resume` and memory write placeholder.
- Blockers:
  - Runtime/API tests still cannot execute in current environment until required dependencies are installed.

## [2026-03-19 23:36] Session Note
- Operator: Codex
- Summary: Unblocked local test execution by creating `.venv`, installing runtime/dev dependencies, and running full test suite successfully.
- Files changed:
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Use local Python 3.10 `.venv` as temporary fallback for fast verification while Python 3.12 installation is unavailable.
  - Keep README control panel synchronized with Progress Tracker after test unblock.
- Next actions:
  1. Retry Python 3.12 installation and migrate venv to compliant runtime.
  2. Re-run tests on Python 3.12 and continue implementing `/v1/resume`.
- Blockers:
  - `winget` source/network errors (`0x80072efd`) currently block installing Python 3.12.

## [2026-03-19 23:43] Session Note
- Operator: Codex
- Summary: Hardened the implemented M1 scope by improving test reliability and adding budget-focused unit coverage; regression suite now runs cleanly.
- Files changed:
  - tests/conftest.py
  - tests/integration/test_v1_health.py
  - tests/integration/test_v1_chat.py
  - tests/compatibility/test_openai_gateway_skeleton.py
  - tests/unit/test_budget_service.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Use shared `TestClient` fixture to avoid test lifecycle leakage and flaky warning behavior.
  - Keep budget invariants protected with dedicated unit tests, not only integration assertions.
- Next actions:
  1. Retry Python 3.12 installation and rerun suite in compliant runtime.
  2. Continue `/v1/resume` implementation after runtime compliance check.
- Blockers:
  - Python 3.12 installation still blocked by `winget` network/source errors.

## [2026-03-20 00:03] Session Note
- Operator: Codex
- Summary: Retried environment provisioning successfully, installed Python 3.12, created `.venv312`, and validated the project test suite on compliant runtime.
- Files changed:
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Use `.venv312` as the default validation environment for this project going forward.
- Next actions:
  1. Continue M1 implementation with `/v1/resume` minimal path and memory write placeholder.
  2. Keep running regression checks in `.venv312`.
- Blockers:
  - None

## [2026-03-20 00:15] Session Note
- Operator: Codex
- Summary: Optimized existing M1 chat algorithms by introducing complexity-aware token estimation, adaptive output reserve, and heuristic-driven metadata scoring for quality/balance/fallback signals.
- Files changed:
  - app/api/v1/service.py
  - tests/integration/test_v1_chat.py
  - tests/unit/test_budget_service.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep algorithm deterministic and pure-function-based to simplify regression testing before provider telemetry integration.
  - Add moderate Chinese inline comments only around non-obvious algorithm blocks.
- Next actions:
  1. Calibrate heuristic coefficients with real provider/tokenizer observations in subsequent M1 steps.
  2. Preserve current regression suite as baseline guard (`12 passed` on Python 3.12).
- Blockers:
  - None

## [2026-03-20 00:21] Session Note
- Operator: Codex
- Summary: Refactored algorithm implementation for maintainability and lower runtime overhead by replacing repeated text scans with one reusable message profiling pass and clearer strategy boundaries.
- Files changed:
  - app/api/v1/service.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Centralize message-derived signals in `MessageProfile` to reduce duplicated computation and simplify future coefficient tuning.
  - Keep compatibility wrapper functions (`_estimate_input_tokens`, `_message_complexity_ratio`) for test stability and incremental migration.
- Next actions:
  1. Use the refactored strategy layout as the base for provider telemetry integration.
  2. Add benchmark-style regression checks if performance-sensitive workloads increase.
- Blockers:
  - None

## [2026-03-20 00:32] Session Note
- Operator: Codex
- Summary: Applied additional performance tuning by introducing profile reuse path in budget calculation and reducing repeated message-derived computations, then validated with expanded regression tests.
- Files changed:
  - app/api/v1/service.py
  - tests/unit/test_budget_service.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep `_build_budget(..., profile=...)` optional parameter for backward-compatible tests while enabling lower-overhead internal path.
  - Maintain deterministic strategy logic and avoid premature async/multi-thread complexity until real IO hotspots emerge.
- Next actions:
  1. Introduce runtime metrics collection around profile/build-budget latency once provider calls are wired.
  2. Tune heuristic coefficients with observed production-like traces.
- Blockers:
  - None

## [2026-03-20 00:52] Session Note
- Operator: Codex
- Summary: Implemented next M1 block: added `/v1/resume` endpoint and memory-write placeholder pipeline with in-process index + JSONL persistence, then completed regression verification.
- Files changed:
  - app/core/settings.py
  - app/api/v1/schemas.py
  - app/api/v1/service.py
  - app/api/v1/router.py
  - app/memory/__init__.py
  - app/memory/ledger.py
  - tests/conftest.py
  - tests/integration/test_v1_chat.py
  - tests/integration/test_v1_resume.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Use `MemoryLedger` single-load cache to avoid repeated full-file scans on every request.
  - Use batched JSONL append writes per chat turn to reduce file-IO overhead and avoid per-record open/close churn.
- Next actions:
  1. Implement `/v1/timeline` minimal path based on current ledger output.
  2. Introduce SQLAlchemy + Alembic baseline and gradually replace JSONL placeholder persistence.
- Blockers:
  - None

## [2026-03-20 08:23] Session Note
- Operator: Codex
- Summary: Performed algorithm-focused optimization on memory/resume path by reducing repeated work, lowering memory overhead, and tightening data-structure consistency guarantees.
- Files changed:
  - app/memory/ledger.py
  - tests/unit/test_memory_ledger.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Replace eager `split` sentence extraction with streaming iterator to avoid full intermediate list allocation on long inputs.
  - Merge memory type detection from multiple regex scans into a single compiled regex pass per sentence.
  - Keep `todo_set` synchronized with bounded deque eviction to prevent unbounded growth and stale-membership rejection.
- Next actions:
  1. Implement `/v1/timeline` minimal endpoint backed by current ledger state.
  2. Start migration from JSONL placeholder to SQLAlchemy + Alembic persistence baseline.
- Blockers:
  - None

## [2026-03-20 08:29] Session Note
- Operator: Codex
- Summary: Further optimized current M1 code path by replacing regex-based secondary token scan with single-pass linear profiling in chat service, adding short-text profile cache, and reducing resume/write allocation overhead in ledger.
- Files changed:
  - app/api/v1/service.py
  - app/memory/ledger.py
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep profile caching bounded (`maxsize=512`, only for text length `<=4096`) to avoid large-message memory retention.
  - Use tail-window extraction via iterator (`islice(reversed(deque), k)`) instead of full `list(deque)` copy in resume path.
- Next actions:
  1. Add `/v1/timeline` minimal endpoint and reuse optimized ledger iteration utilities.
  2. Introduce lightweight benchmark script for `service._build_message_profile` and ledger resume hot path.
- Blockers:
  - None

## [2026-03-20 08:40] Session Note
- Operator: Codex
- Summary: Implemented the next planned block `/v1/timeline` with cursor pagination, including schema/router/service wiring, bounded in-memory timeline event indexing in `MemoryLedger`, and regression coverage updates.
- Files changed:
  - app/api/v1/schemas.py
  - app/api/v1/router.py
  - app/api/v1/service.py
  - app/memory/ledger.py
  - tests/integration/test_v1_timeline.py
  - tests/unit/test_memory_ledger.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep timeline pagination cursor based on `memory_id` of the last item in the current page for deterministic paging on append-only event sequences.
  - Keep timeline storage bounded in-process (`MAX_TIMELINE_EVENTS_PER_PROJECT`) to control memory growth before DB migration.
- Next actions:
  1. Add SQLAlchemy + Alembic baseline and migrate timeline/memory persistence off JSONL incrementally.
  2. Add benchmark checks for timeline/resume path and message profile hot path.
- Blockers:
  - None

## [2026-03-20 08:48] Session Note
- Operator: Codex
- Summary: Performed algorithm-level optimization for the new timeline module: reduced stored event classes to `decision/risk/todo`, introduced sequence-index cursor mapping, and replaced two-stage cursor scanning with one-pass reverse slicing pagination to improve both latency and memory usage.
- Files changed:
  - app/memory/ledger.py
  - app/api/v1/service.py
  - tests/unit/test_memory_ledger.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep timeline as high-signal stream only (`decision/risk/todo`) to reduce storage churn and pagination payload noise.
  - Keep cursor fallback behavior unchanged: unknown cursor still serves latest page to preserve current API tolerance.
- Next actions:
  1. Introduce DB-backed timeline/events model with SQLAlchemy + Alembic while maintaining existing cursor semantics.
  2. Add micro-benchmark script to track pagination and profile extraction hot-path performance over iterations.
- Blockers:
  - None

## [2026-03-20 09:05] Session Note
- Operator: Codex
- Summary: Completed SQL persistence baseline implementation from project docs by adding SQLAlchemy ORM schema + session infrastructure, Alembic migration scaffold, and initial revision for v1 core tables/indexes; validated with dedicated schema/migration tests.
- Files changed:
  - pyproject.toml
  - app/core/settings.py
  - app/db/__init__.py
  - app/db/base.py
  - app/db/bootstrap.py
  - app/db/models.py
  - app/db/session.py
  - alembic.ini
  - alembic/env.py
  - alembic/script.py.mako
  - alembic/versions/20260320_0001_initial_schema.py
  - tests/unit/test_db_schema.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep DB baseline additive and non-breaking: current runtime still uses JSONL path while SQL schema is introduced for staged migration.
  - Keep Alembic URL sourced from `CONTEXTLEDGER_SQL_DSN` to support environment-specific migrations without code edits.
- Next actions:
  1. Implement repository layer for memory/timeline writes and migrate handler paths from JSONL to SQLAlchemy incrementally.
  2. Add migration + rollback check in CI to guarantee schema evolution safety.
- Blockers:
  - `pip install -e .[dev]` currently fails due multi-top-level package discovery in setuptools configuration; dependency install used direct package install as a temporary workaround.

## [2026-03-20 09:12] Session Note
- Operator: Codex
- Summary: Performed time/space optimization on the newly added DB baseline by tuning SQLite engine behavior, removing unnecessary local pre-ping overhead, and adding engine-cache reset control plus targeted DB session regression tests.
- Files changed:
  - app/db/session.py
  - app/db/__init__.py
  - tests/unit/test_db_session.py
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep `pool_pre_ping` enabled for non-SQLite backends only; disable it for local SQLite to cut per-checkout overhead.
  - Enable SQLite PRAGMA defaults (`foreign_keys=ON`, `journal_mode=WAL`, `synchronous=NORMAL`) for better local throughput while preserving integrity constraints.
- Next actions:
  1. Migrate memory/timeline write path from JSONL placeholder to SQLAlchemy repositories.
  2. Add benchmark checks for SQL write/read latency after repository integration.
- Blockers:
  - None

## [2026-03-20 09:29] Session Note
- Operator: Codex
- Summary: Completed the next migration step by integrating SQL dual-write into `MemoryLedger` write path: chat turn ingestion now writes to both JSONL/in-memory ledger and SQLAlchemy repository with request-level idempotency guard and non-blocking failure fallback.
- Files changed:
  - app/core/settings.py
  - app/db/__init__.py
  - app/db/repositories.py
  - app/memory/ledger.py
  - tests/unit/test_db_repository.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep dual-write enabled by default via `CONTEXTLEDGER_SQL_WRITE_ENABLED` while preserving JSONL path as the compatibility-safe baseline.
  - Keep SQL write failures isolated (swallow with fallback) so API availability is not coupled to SQL runtime readiness.
- Next actions:
  1. Add SQL-backed read repositories for `/v1/resume` and `/v1/timeline`.
  2. Introduce read cutover flag and consistency verification tests between JSONL and SQL views.
- Blockers:
  - None

## [2026-03-20 09:35] Session Note
- Operator: Codex
- Summary: Optimized the SQL dual-write hot path for performance by removing per-request dynamic conversion overhead in ledger, reducing temporary allocations during JSONL append, and switching SQL persistence to batched Core insert operations instead of per-row ORM add objects.
- Files changed:
  - app/db/repositories.py
  - app/memory/ledger.py
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep SQL write path non-blocking and idempotent while prioritizing lower write amplification in the hot path.
  - Keep feature behavior unchanged; optimization is internal-only and protected by existing regression suite.
- Next actions:
  1. Implement SQL-backed read path for resume/timeline.
  2. Add consistency checks between JSONL projection and SQL query results.
- Blockers:
  - None

## [2026-03-20 10:10] Session Note
- Operator: Codex
- Summary: Completed the documented next step by adding SQL-backed read repositories for resume/timeline, introducing read-path cutover flag, wiring SQL-read-first fallback in `MemoryLedger`, and adding consistency + fallback tests.
- Files changed:
  - app/core/settings.py
  - app/db/repositories.py
  - app/memory/ledger.py
  - tests/unit/test_db_repository.py
  - tests/unit/test_memory_ledger.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep SQL read cutover controlled by `CONTEXTLEDGER_SQL_READ_ENABLED` (default `false`) to preserve low-risk rollout.
  - Keep SQL read failures non-blocking by falling back to in-memory/JSONL projection path.
- Next actions:
  1. Add benchmark checks for SQL read latency and parity under larger datasets.
  2. Start staged runtime cutover validation with `CONTEXTLEDGER_SQL_READ_ENABLED=true`.
- Blockers:
  - None

## [2026-03-20 10:35] Session Note
- Operator: Codex
- Summary: Optimized SQL read-path performance by adding resume snapshot cache and timeline cursor-position cache in repository layer, with project-level cache invalidation after successful writes.
- Files changed:
  - app/db/repositories.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep resume cache keyed by latest user `request_id` to avoid stale reads while reducing repeated aggregation queries.
  - Keep timeline cursor cache bounded per project to lower repeated pagination cursor-lookup overhead with controlled memory usage.
- Next actions:
  1. Add benchmark script for SQL read p95 latency and cache-hit ratio.
  2. Evaluate staged cutover with `CONTEXTLEDGER_SQL_READ_ENABLED=true` under larger dataset.
- Blockers:
  - None

## [2026-03-20 11:05] Session Note
- Operator: Codex
- Summary: Implemented the next documented block by adding SQL read-path benchmark tooling and another round of cache optimization (timeline latest-page cache), with correctness guards and benchmark baseline output.
- Files changed:
  - .gitignore
  - app/db/repositories.py
  - scripts/run_sql_read_benchmark.py
  - scripts/README.md
  - tests/unit/test_db_repository.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Add public `clear_read_caches(...)` in repository for deterministic benchmark control and troubleshooting.
  - Keep all read caches bounded (`resume`, `timeline cursor`, `timeline latest`) and invalidate per-project immediately after successful write.
- Next actions:
  1. Stage runtime read cutover (`CONTEXTLEDGER_SQL_READ_ENABLED=true`) and compare parity/p95 with this benchmark baseline.
  2. Continue next feature block: replace placeholder chat response with provider adapter call path.
- Blockers:
  - `git push` still blocked by current network connectivity to GitHub.

## [2026-03-20 11:30] Session Note
- Operator: Codex
- Summary: Performed another algorithm/performance hardening pass on SQL read path with lower cache invalidation complexity and index-backed query acceleration, then validated by benchmark and full regression.
- Files changed:
  - app/db/repositories.py
  - app/db/models.py
  - alembic/versions/20260320_0002_read_path_indexes.py
  - tests/unit/test_db_schema.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Replace global key-scan invalidation for timeline latest cache with per-project bucket invalidation to keep write-path cache maintenance O(1).
  - Introduce migration-managed read indexes for `resume` and `timeline` hot queries instead of relying only on model metadata defaults.
- Next actions:
  1. Run staged runtime SQL-read cutover validation and record p95 parity in tracker.
  2. Continue implementation of provider adapter path for `/v1/chat`.
- Blockers:
  - `git push` still blocked by current network connectivity to GitHub.

## [2026-03-20 11:50] Session Note
- Operator: Codex
- Summary: Implemented the next code block from docs by replacing `/v1/chat` placeholder answer path with provider-adapter invocation (contract + registry + deterministic provider), and added provider-focused unit tests.
- Files changed:
  - app/api/v1/service.py
  - app/core/settings.py
  - app/providers/__init__.py
  - app/providers/base.py
  - app/providers/deterministic_provider.py
  - app/providers/registry.py
  - tests/unit/test_provider_registry.py
  - README.md
  - docs/Progress-Tracker.md
  - MESSAGES.md
- Decisions:
  - Keep deterministic provider as default-safe adapter baseline so regression and local runs stay stable without external dependencies.
  - Cache provider instances in registry (`lru_cache`) to avoid per-request reconstruction overhead.
- Next actions:
  1. Add real network adapters (LM Studio/Ollama HTTP) with timeout/retry and fallback policy.
  2. Continue OpenAI-compatible endpoint expansion from `501` skeleton toward contract-compliant responses.
- Blockers:
  - `git push` still blocked by current network connectivity to GitHub.
