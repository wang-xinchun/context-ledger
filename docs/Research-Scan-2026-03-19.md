# Research Scan (GitHub + Papers) - 2026-03-19

## 1. Goal
Update ContextLedger technical details using:
1. Current open-source community practice (GitHub projects/issues).
2. Research-backed approaches (papers).
3. Practical anti-patterns to avoid repeated mistakes.

## 2. Community Signals (GitHub)

## 2.1 Reusable implementation patterns
1. `langmem` emphasizes split memory paths:
   - "hot path" memory tools during active chat.
   - background manager for extraction/consolidation.
   - Source: <https://github.com/langchain-ai/langmem>

2. `redis/agent-memory-server` shows a production memory service shape:
   - two-tier memory (`working` + `long-term`)
   - dual interface (`REST` + `MCP`)
   - separate API/worker deployment model.
   - Source: <https://github.com/redis/agent-memory-server>

3. `microsoft/graphrag` highlights operational realities:
   - indexing cost can be high; start small.
   - explicit config/version migration guidance.
   - Source: <https://github.com/microsoft/graphrag>

4. `letta` confirms memory-first/stateful agent direction.
   - Source: <https://github.com/letta-ai/letta>

5. `mem0` confirms demand for self-host + provider-flex memory layer.
   - Source: <https://github.com/mem0ai/mem0>

## 2.2 Community pain points (must avoid)
1. Auto-summary may cause context loss in long coding sessions.
   - Source: <https://github.com/microsoft/vscode/issues/251250>
2. RAG systems can expose file/path security vulnerabilities if ingestion/deletion APIs are not hardened.
   - Source: <https://github.com/HKUDS/LightRAG/issues/2110>
3. Large-document indexing may fail without robust async pipeline and observability.
   - Source: <https://github.com/HKUDS/LightRAG/issues/1001>

## 3. Paper Signals (Research)

1. RAG foundation: explicit non-parametric memory improves factual generation.
   - Retrieval-Augmented Generation (NeurIPS 2020)
   - <https://arxiv.org/abs/2005.11401>

2. Long context risk: models are often weaker on middle-position information.
   - Lost in the Middle
   - <https://arxiv.org/abs/2307.03172>

3. Adaptive retrieval and self-critique are valuable.
   - Self-RAG
   - <https://arxiv.org/abs/2310.11511>

4. Retrieval quality gating and corrective fallback are important.
   - CRAG
   - <https://arxiv.org/abs/2401.15884>

5. Multi-level abstraction retrieval helps long documents.
   - RAPTOR
   - <https://arxiv.org/abs/2401.18059>

6. Graph-enhanced memory retrieval can improve multi-hop reasoning efficiency.
   - HippoRAG
   - <https://arxiv.org/abs/2405.14831>

7. Long-context benchmarks are required for realistic evaluation.
   - LongBench
   - <https://arxiv.org/abs/2308.14508>

8. Hierarchical/virtual context management is a practical framing for long sessions.
   - MemGPT
   - <https://arxiv.org/abs/2310.08560>

## 4. Technical Updates Adopted for ContextLedger

1. Introduce explicit memory tiers:
   - L0: turn buffer
   - L1: working memory (session)
   - L2: long-term memory (project)
   - L3: snapshot/summary index

2. Add retrieval quality gate:
   - score retrieval quality first.
   - fallback path: query rewrite or external retrieval when below threshold.

3. Add position-aware context packing:
   - place highest-value evidence at prompt edges to reduce "lost in the middle" effects.

4. Add async indexing pipeline:
   - ingestion/index/summarization run in worker queues.
   - API path remains bounded-latency.

5. Add safety hardening for local file operations:
   - strict path allowlist.
   - no delete/write outside project root.

6. Add benchmark-aware evaluation:
   - include long-context regression suite inspired by LongBench task shapes.

## 5. Deliberate Non-Goals (to avoid duplicate products)
1. Not building a generic memory SDK-only product.
2. Not building a graph-only RAG platform first.
3. Not relying on auto-summary alone as the primary continuity mechanism.

## 6. Decision
This scan confirms the project direction is still valid, but v1 should explicitly include:
1. retrieval quality gating,
2. position-aware packing,
3. async pipeline and safety boundaries,
4. long-context regression tests.
