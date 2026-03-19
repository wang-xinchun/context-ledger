# Tech Upgrade v2

## 1. Upgrade Goal
Move ContextLedger from a functional v1 memory layer to an advanced, verifiable memory operating layer.

Upgrade focus:
1. Better answer quality under long-horizon sessions.
2. Stronger safety/governance guarantees.
3. Measurable and regressible system behavior.

## 2. v2 Capability Pack

## 2.1 Adaptive Retrieval Controller (Must)
Replace fixed retrieval with policy-driven adaptive retrieval.

Core behavior:
1. Classify query complexity (`simple`, `multi-step`, `decision-heavy`, `code-history`).
2. Dynamically allocate retrieval budget by class.
3. Run corrective retrieval rounds when quality score is low.

Key outputs:
- `retrieval_plan`
- `retrieval_rounds`
- `retrieval_quality_score`

## 2.2 Memory Graph + Vector Hybrid Retrieval (Must)
Introduce graph-augmented memory retrieval:
1. Vector retrieval finds semantic neighbors.
2. Graph traversal links decisions, constraints, risks, and files.
3. Final ranking merges vector score + graph proximity + recency.

Graph node types:
- `decision`, `constraint`, `risk`, `todo`, `fact`, `file_ref`, `commit_ref`

## 2.3 Uncertainty-Aware Response Flow (Must)
Every response includes:
1. confidence score
2. evidence coverage score
3. fallback mode if confidence is below threshold

Low-confidence actions:
1. force second retrieval round
2. run contradiction scan
3. answer in guarded mode if still low confidence

## 2.4 Learned Context Packing (Should)
Upgrade from static packing rules to feedback-driven packing.

Mechanism:
1. Start with rule-based edge-priority packing.
2. Collect response quality telemetry.
3. Train lightweight ranker to improve segment placement.

## 2.5 Memory Regression CI (Must)
Build release gate for memory quality:
1. long-session replay suite
2. context-loss benchmark cases
3. truncation and continuation budget checks
4. quality score delta gate

Release is blocked when regressions exceed threshold.

## 2.6 Policy-as-Code Safety Layer (Must)
Externalize runtime controls as policies:
1. file path rules
2. budget safety rules
3. deletion/write restrictions
4. provider usage controls

Recommended engines:
- OPA/Rego or Cedar-like policy schema

## 2.7 Event-Driven Memory Pipeline (Should)
Split request critical path and heavy memory jobs.

Critical path:
- query -> compile -> generate -> return

Async path:
- extraction -> graph update -> compaction -> conflict detection

## 2.8 Advanced Observability (Must)
Add first-class metrics:
1. `retrieval_quality_score_p50/p95`
2. `confidence_score_p50/p95`
3. `evidence_coverage_p50/p95`
4. `truncation_rate`
5. `continuation_rounds_p95`
6. `resume_latency_p95`
7. `policy_block_rate`
8. `context_growth_ratio_p50/p95`
9. `quality_growth_balance_index`

## 2.9 Quality-Growth Optimizer (Must)
Define an explicit objective:
- maximize `quality_score`
- minimize `context_growth_ratio`
- keep `continuation_rounds` bounded

Use weighted control:
`score = wq * quality_score - wg * context_growth_ratio - wc * continuation_penalty`

Weights are mode-dependent:
1. `quality_first`: `wq` high, `wg` low
2. `balanced`: `wq ~= wg`
3. `growth_first`: `wg` high, enforce tighter growth cap

## 3. Architecture Delta (v1 -> v2)
New components:
1. `Adaptive Retrieval Controller`
2. `Memory Graph Service`
3. `Uncertainty Estimator`
4. `Policy Engine`
5. `Regression Evaluator`
6. `Telemetry Aggregator`

## 4. API Delta (v2 fields)
`POST /v1/chat` response additions:
1. `confidence_score`
2. `evidence_coverage_score`
3. `retrieval_plan`
4. `fallback_mode`
5. `policy_hits`

## 5. Delivery Plan

## Phase U1 (Immediate, 1-2 weeks)
1. Adaptive retrieval controller (rule-driven).
2. Uncertainty score skeleton.
3. API field extension and telemetry hooks.

## Phase U2 (2-4 weeks)
1. Memory graph schema + builder pipeline.
2. Hybrid retrieval ranker.
3. Policy-as-code first rule set.

## Phase U3 (4-6 weeks)
1. Memory regression CI gates.
2. Learned packing prototype.
3. Dashboard and release criteria finalization.

## 6. Acceptance Criteria
1. Long-session regression set passes with lower context-loss rate than v1 baseline.
2. Low-confidence responses correctly trigger fallback flows.
3. Policy violations are blocked and auditable.
4. Release pipeline blocks known quality regressions.

## 7. Risk and Mitigation
1. Risk: graph complexity increases latency.
   - Mitigation: asynchronous graph updates + cache hot edges.
2. Risk: uncertainty scoring may be noisy.
   - Mitigation: combine heuristic + calibration from replay labels.
3. Risk: policy rollout blocks too many requests.
   - Mitigation: dry-run mode before enforcement.
