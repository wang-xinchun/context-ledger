# Compatibility Strategy v1

## 1. Objective
Ensure ContextLedger works across mainstream LLM usage patterns without forcing users to change workflows.

Core principle:
- Keep client usage unchanged as much as possible.
- Add ContextLedger as a transparent middle layer.

## 2. Integration Modes

## 2.1 OpenAI-Compatible Gateway (Primary)
Expose OpenAI-style endpoints so common SDKs and CLI tools can switch by changing `base_url`.

Target endpoints:
1. `POST /openai/v1/chat/completions`
2. `POST /openai/v1/responses` (compat layer)
3. `POST /openai/v1/embeddings` (for ingestion/indexing clients)
4. `GET /openai/v1/models`

## 2.2 Native Memory API (Project Features)
For full ContextLedger features:
1. `POST /v1/chat`
2. `POST /v1/resume`
3. `GET /v1/timeline`

## 2.3 MCP Server (Agent Tools)
Expose memory operations as MCP tools for agent ecosystems and IDE agents.

## 3. Mainstream Usage Scenarios
1. CLI tools using OpenAI-compatible HTTP APIs.
2. Python/JS SDK applications using OpenAI-like client interfaces.
3. IDE extensions that allow custom OpenAI-compatible endpoints.
4. Agent frameworks using MCP.

## 4. Compatibility Levels
1. `L1 Protocol Compatibility`
   - Endpoint path/method
   - request/response schema
   - streaming framing compatibility

2. `L2 Semantic Compatibility`
   - core fields preserve expected behavior (`model`, `messages`, `temperature`, `max_tokens`)
   - finish reason and usage token fields populated

3. `L3 Behavior Compatibility`
   - retries/timeouts predictable
   - output quality and truncation behavior stable under long sessions

## 5. Provider Compatibility Matrix (Target)
1. `LM Studio` (OpenAI-compatible base URL)
2. `Ollama` (adapter)
3. `OpenAI-compatible cloud provider` (adapter)

Per-provider capability map:
1. max context tokens
2. max output tokens
3. streaming support
4. tool/function-calling support
5. stop-sequence behavior

## 6. Degradation Rules
If provider capability is missing:
1. no tool-calling -> disable tool route, keep plain chat.
2. weak streaming -> fallback to non-stream response.
3. small output limit -> auto-continuation enabled.
4. unstable token accounting -> conservative budget reserve.

All degradation paths must be explicit in response metadata.

## 7. Compatibility Test Matrix
Each release runs compatibility suites:
1. OpenAI protocol conformance tests.
2. Streaming chunk conformance tests.
3. CLI smoke tests (chat + streaming + long session).
4. SDK integration tests (Python + JS minimal clients).
5. MCP tool-call integration tests.

## 8. Release Gate
A release cannot be marked stable unless:
1. L1 protocol tests pass for all supported adapters.
2. L2 semantic tests pass for core parameters.
3. long-session truncation rate within SLO in L3 tests.
4. known degradation paths are tested and documented.

## 9. Non-Goals
1. Perfect feature parity with every vendor-specific extension.
2. Support for proprietary features without public protocol.
3. Unlimited compatibility claims without automated tests.
