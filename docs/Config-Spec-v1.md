# Config Spec v1

## 1. Configuration Sources
Priority order:
1. Environment variables
2. `config.yaml`
3. Internal defaults

## 2. Required Keys
```yaml
app:
  env: "dev"
  log_level: "INFO"

provider:
  chat_provider: "lmstudio"
  embedding_provider: "local"
  provider_api_version: "1.0"

chat:
  base_url: "http://127.0.0.1:1234/v1"
  model_name: "qwen32b"
  timeout_ms: 60000
  max_retries: 2

budget:
  max_context_tokens: 4096
  min_output_reserve: 900
  system_tokens: 400
  snapshot_tokens: 700
  recent_turn_tokens: 900
  retrieved_tokens: 1200
  user_tokens: 300

continuation:
  enabled: true
  max_rounds: 3
  trigger_on_truncation: true

retrieval:
  quality_gate_enabled: true
  min_quality_score: 0.65
  enable_query_rewrite: true
  max_retrieval_items: 12

packing:
  strategy: "position_aware"
  edge_priority_ratio: 0.6

balance:
  mode: "balanced" # quality_first | balanced | growth_first
  target_quality_score: 0.78
  target_context_growth_ratio: 0.72
  mode_switch_window: 3
  hard_growth_cap_ratio: 0.85

quality_guard:
  enabled: true
  min_quality_score: 0.75
  max_fix_rounds: 2

safety:
  project_root: "./"
  path_allowlist_enabled: true
  block_outside_root_delete: true

storage:
  sql_backend: "sqlite"
  sql_dsn: "sqlite:///./data/memory.db"
  vector_backend: "faiss"
  vector_path: "./data/vector.index"
```

## 3. Validation Rules
1. `min_output_reserve` must be >= 512.
2. Sum of fixed input budget parts must not exceed `max_context_tokens - min_output_reserve`.
3. `max_retries` and `max_fix_rounds` must be >= 0.
4. `retrieval.min_quality_score` must be in `[0,1]`.
5. `packing.edge_priority_ratio` must be in `(0,1)`.
6. `balance.target_quality_score` must be in `[0,1]`.
7. `balance.target_context_growth_ratio` must be in `(0,1)`.
8. `balance.hard_growth_cap_ratio` must be `>= target_context_growth_ratio`.
9. Invalid config blocks startup.

## 4. Runtime Reload
1. Safe reload keys: log level, quality thresholds.
2. Restart-required keys: provider backend, DB backend, embedding dimensions, safety root path.
