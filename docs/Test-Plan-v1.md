# Test Plan v1

## 1. Test Scope
1. Chat pipeline correctness.
2. Token budget compiler behavior.
3. Continuation and stitching reliability.
4. Memory extraction and resume quality.
5. Retrieval quality gate and corrective flow.
6. Safety boundary for file/path operations.
7. Protocol and client compatibility conformance.

## 2. Test Types
1. Unit tests
- Budget planner
- Degrade policy
- Quality guard scoring
- Provider capability parsing
- Retrieval quality scoring
- Position-aware packing policy

2. Integration tests
- `/v1/chat`, `/v1/resume`, `/v1/timeline`
- SQL writes + vector indexing
- Continuation trigger and final answer merge
- Query rewrite fallback on low retrieval score
- Path traversal protection checks

3. End-to-end tests
- Long session (100 turns) continuity
- New session resume
- Low token window stress scenario
- Middle-position evidence robustness scenario

4. Compatibility conformance tests
- OpenAI-compatible endpoint contract tests
- Streaming chunk format tests
- Python SDK integration smoke tests
- JS SDK integration smoke tests
- MCP integration smoke tests

## 3. Regression Suite
1. Stable set of long conversation fixtures.
2. Expected outputs with semantic checks.
3. Metrics delta gating (truncation rate, resume hit rate).
4. Long-context case set inspired by LongBench task patterns.

## 4. Acceptance Criteria
1. No hard failure on overflow cases.
2. Truncated answer rate below threshold.
3. Resume output contains decisions and open todos for test projects.
4. Timeline entries are complete and ordered.
5. Retrieval low-score path returns corrected or degraded-safe response.
6. Safety tests block out-of-root destructive file requests.
7. OpenAI-compatible suites pass for supported adapters.

## 5. Tooling
1. `pytest` for unit and integration.
2. `httpx` test client for API.
3. `Playwright` for web E2E (after UI implementation).
