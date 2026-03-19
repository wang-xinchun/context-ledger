# Roadmap v1

## Phase M1: Core Loop
1. `/chat` endpoint.
2. Turn persistence and memory extraction.
3. `/resume` endpoint.
4. OpenAI-compatible gateway skeleton (`/openai/v1/chat/completions`).

## Phase M2: Context Engine
1. Hybrid retriever.
2. Budget planner and overflow degrade.
3. Output reserve enforcement.
4. Retrieval quality gate + corrective fallback.
5. Position-aware context packing.

## Phase M3: Response Stability
1. Two-phase generation.
2. Auto-continuation orchestrator.
3. Quality guard and auto-fix.

## Phase M4: Productization
1. Timeline endpoint and event model.
2. Regression suite and baseline dashboard.
3. Deployment hardening docs and release checklist.
4. Safety boundary tests for file operations.
5. Compatibility conformance suite as release gate.

## Phase M5: Evolvability
1. Provider registry expansion.
2. Team deployment profile (Postgres + Qdrant + Redis).
3. MCP server integration.

## Phase U1: Advanced Runtime Control
1. Adaptive retrieval controller (rule-based).
2. Uncertainty-aware response fields (`confidence`, `evidence_coverage`).
3. Telemetry hooks for retrieval/continuation/fallback.

## Phase U2: Hybrid Intelligence Layer
1. Memory graph schema and async graph builder.
2. Vector + graph hybrid reranking.
3. Policy-as-code safety engine (dry-run -> enforce).

## Phase U3: Release-Grade Quality System
1. Memory regression CI gates.
2. Learned context packing prototype.
3. Dashboard-based SLO gates for release.
