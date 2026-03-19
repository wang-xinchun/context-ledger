# Architecture v1

## 1. High-Level Flow
```text
Client (CLI/Web)
  -> API Gateway (FastAPI)
    -> Session Manager
    -> Context Compiler
      -> Memory Retriever
      -> Retrieval Quality Gate
      -> Position-Aware Context Packer
      -> Budget Planner
    -> Response Orchestrator
      -> Chat Provider Adapter (LM Studio/Ollama/...)
    -> Memory Extractor
      -> Memory Store (SQL + Vector)
      -> Async Index Queue
```

## 2. Key Modules
1. `Session Manager`
- Tracks session and project identity.
- Loads recent turns and runtime policies.

2. `Memory Retriever`
- Hybrid retrieval: vector + keyword + type filter.
- Returns scored memory candidates.

3. `Retrieval Quality Gate`
- Computes retrieval confidence score.
- If below threshold, triggers corrective flow:
  - query rewrite
  - broadened retrieval
  - fallback to snapshot-first response

4. `Context Compiler`
- Applies token budget policy.
- Enforces minimum output reserve.
- Packs high-value evidence at prompt edges (position-aware).
- Produces final prompt package.

5. `Response Orchestrator`
- Runs two-phase generation.
- Detects truncation and triggers auto-continuation.
- Stitches partial outputs into a single final answer.

6. `Memory Extractor`
- Extracts structured units from conversation output.
- Writes memory events and references to source turns.

7. `Async Index Pipeline`
- Uses worker queue for indexing/summarization/compaction.
- Keeps chat critical path low-latency.

8. `Provider Registry`
- Loads configured provider adapters.
- Exposes provider capabilities (window, output, streaming, tools).

9. `Safety Guard`
- Enforces project-root file access allowlist.
- Blocks path traversal and out-of-scope deletion requests.

## 3. Data Paths
1. Read path:
- Client query -> retrieval -> budget compile -> provider generate -> response QA -> return.
2. Write path:
- Input + output -> memory extraction -> SQL write -> async vector indexing -> timeline event.

## 4. Reliability Strategy
1. Degrade before fail on token overflow.
2. Automatic continuation with max retry limit.
3. Idempotent turn writes using request id.
4. Timeout guard for provider calls and retrieval calls.

## 5. Evolvability Strategy
1. API versioning under `/v1`.
2. Provider contracts versioned with `provider_api_version`.
3. Storage backend switch through config and adapter.
4. Schema migration through Alembic only.
