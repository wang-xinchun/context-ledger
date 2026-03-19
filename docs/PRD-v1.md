# PRD v1

## 1. Product Positioning
ContextLedger is a local-first memory orchestration layer for AI conversations in long-running projects.  
It improves continuity when model context windows are limited.

## 2. Target Users
1. Individual developers using local LLM runtime.
2. Small teams doing long project conversations with AI.
3. Users who need resumable project context without repeating history.

## 3. User Problem
1. Context drops in long sessions.
2. New session means repeating project background.
3. Model response quality decreases when available output tokens shrink.
4. Important decisions and risks are hard to track over time.

## 4. Product Goals
1. Deliver near-unlimited context experience under small context windows.
2. Keep output quality stable even under strict token constraints.
3. Preserve project memory in structured, queryable form.
4. Enable long-term evolvability (providers, storage, deployment).

## 5. Non-Goals (v1)
1. Multi-tenant org permission model.
2. Native multimodal memory (image/audio/video).
3. Full enterprise workflow orchestration.

## 6. Core User Stories
1. As a user, I can continue project conversation in a new session with a fast summary and open todos.
2. As a user, I receive complete answers even when model window is only `4096` tokens.
3. As a user, I can inspect timeline of decisions and risks by project.
4. As a user, I can switch model providers without rewriting core logic.

## 7. Functional Requirements (v1)
1. Chat proxy endpoint with automatic memory retrieval.
2. Context compiler with strict token budgeting.
3. Output reserve enforcement.
4. Two-phase generation (`outline -> expansion`).
5. Auto-continuation and final answer stitching.
6. Memory extraction by type (`fact`, `decision`, `constraint`, `todo`, `risk`).
7. Resume endpoint for project state reconstruction.
8. Timeline endpoint for memory events.
9. Retrieval quality gate with corrective fallback.
10. Position-aware context packing for long prompts.
11. Safety guard for project-root scoped file operations.

## 8. Non-Functional Requirements
1. Availability for local runtime: single-node stable operation.
2. Performance:
   - P50 chat pipeline overhead <= 800ms (excluding LLM generation).
   - Resume response <= 3s for medium project memory size.
3. Reliability:
   - No hard failure on context overflow.
   - Auto-degrade always returns a valid answer.
4. Observability:
   - Structured logs for each turn.
   - Continuation count and quality guard metrics.

## 9. KPIs
1. Context loss complaint rate.
2. Truncated answer rate.
3. Resume usefulness score (manual user rating).
4. Retrieval relevance score.

## 10. Milestones
1. `M1`: End-to-end chat + memory write + resume.
2. `M2`: Context compiler and budget degrade policy.
3. `M3`: Two-phase generation + continuation + quality guard.
4. `M4`: Timeline + reliability tests + docs freeze.

## 11. v2 Upgrade Backlog (Approved Direction)
1. Adaptive retrieval controller.
2. Memory graph + vector hybrid retrieval.
3. Uncertainty-aware response and fallback.
4. Policy-as-code safety enforcement.
5. Memory regression CI release gate.
