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
