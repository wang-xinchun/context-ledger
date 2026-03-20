# Scripts Directory

Use this directory for repeatable automation scripts only.

Rules:
1. Script names must be verb-first (for example `bootstrap_*.ps1`, `run_*.ps1`).
2. Scripts must be idempotent where possible.
3. Any script that changes external state must log what it changed.

## Available Scripts
1. `run_sql_read_benchmark.py`
   - Purpose: measure SQL read-path latency (`resume` / `timeline`) with uncached vs cached runs.
   - Example:
     - `.\.venv312\Scripts\python scripts/run_sql_read_benchmark.py --turns 800 --resume-runs 200 --timeline-runs 300`
   - Output:
     - JSON report at `output/benchmarks/sql-read-benchmark.json` (default).
2. `run_openai_compat_benchmark.py`
   - Purpose: measure OpenAI-compatible gateway latency (`chat`/`responses` stream and non-stream, plus `embeddings`/`models`).
   - Example:
     - `.\.venv312\Scripts\python scripts/run_openai_compat_benchmark.py --chat-runs 250 --responses-runs 250 --embeddings-runs 250 --models-runs 200`
     - Mixed-load stress:
       - `.\.venv312\Scripts\python scripts/run_openai_compat_benchmark.py --mixed-workers 12 --mixed-cycles 30 --long-prompt-chars 12000 --embedding-batch-size 128 --embedding-text-chars 1024`
     - Isolated DB/memory profile (recommended for stable comparison):
       - ``$env:CONTEXTLEDGER_SQL_DSN='sqlite:///data/bench/compat-bench.db'; $env:CONTEXTLEDGER_MEMORY_LEDGER_PATH='data/bench/compat-bench-memory.jsonl'; .\.venv312\Scripts\python scripts/run_openai_compat_benchmark.py ...``
   - Output:
      - JSON report at `output/benchmarks/openai-compat-benchmark.json` (default), including optional SQL backpressure stats when available.
