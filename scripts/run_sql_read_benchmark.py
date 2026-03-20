"""Micro benchmark for SQL read path (`resume` / `timeline`)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core import settings
from app.db.repositories import SqlLedgerRepository
from app.db.session import reset_engine_state
from app.memory.ledger import MemoryLedger


DEFAULT_DB_PATH = Path("data/bench/sql-read-bench.db")
DEFAULT_LEDGER_PATH = Path("data/bench/sql-read-memory.jsonl")
DEFAULT_JSON_OUT = Path("output/benchmarks/sql-read-benchmark.json")


@dataclass(frozen=True, slots=True)
class MetricSummary:
    mean_ms: float
    p50_ms: float
    p95_ms: float
    min_ms: float
    max_ms: float

    def as_dict(self) -> dict[str, float]:
        return {
            "mean_ms": self.mean_ms,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark SQL read path performance.")
    parser.add_argument("--project-id", default="bench_sql_read")
    parser.add_argument("--session-id", default="bench_sess_1")
    parser.add_argument("--turns", type=int, default=800)
    parser.add_argument("--resume-runs", type=int, default=200)
    parser.add_argument("--timeline-runs", type=int, default=300)
    parser.add_argument("--timeline-limit", type=int, default=20)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--ledger-path", type=Path, default=DEFAULT_LEDGER_PATH)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--keep-data", action="store_true")
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _sqlite_dsn(db_path: Path) -> str:
    return f"sqlite:///{db_path.as_posix()}"


def _build_message(index: int) -> str:
    # 循环注入 decision/risk/todo，保证 timeline 和 resume 都有代表性数据。
    head = index % 3
    if head == 0:
        return f"we will choose design option {index % 17} and keep schema stable"
    if head == 1:
        return f"there is risk of migration drift in module {index % 23}"
    return f"next we need to add regression test batch {index % 29}"


def _percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * ratio) - 1))
    return ordered[idx]


def _round3(value: float) -> float:
    return round(value, 3)


def _summarize(values: list[float]) -> MetricSummary:
    if not values:
        return MetricSummary(0.0, 0.0, 0.0, 0.0, 0.0)
    return MetricSummary(
        mean_ms=_round3(sum(values) / len(values)),
        p50_ms=_round3(_percentile(values, 0.50)),
        p95_ms=_round3(_percentile(values, 0.95)),
        min_ms=_round3(min(values)),
        max_ms=_round3(max(values)),
    )


def _measure_ms(fn, runs: int) -> list[float]:
    results: list[float] = []
    for _ in range(max(1, runs)):
        start_ns = time.perf_counter_ns()
        fn()
        end_ns = time.perf_counter_ns()
        results.append((end_ns - start_ns) / 1_000_000.0)
    return results


def _ratio(base: float, optimized: float) -> float:
    if optimized <= 0:
        return 0.0
    return _round3(base / optimized)


def main() -> None:
    args = _parse_args()

    db_path: Path = args.db_path
    ledger_path: Path = args.ledger_path
    json_out: Path = args.json_out

    db_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)

    if not args.keep_data:
        if db_path.exists():
            db_path.unlink()
        if ledger_path.exists():
            ledger_path.unlink()

    settings.SQL_DSN = _sqlite_dsn(db_path)
    reset_engine_state()

    repository = SqlLedgerRepository()
    ledger = MemoryLedger(
        ledger_path,
        sql_write_enabled=True,
        sql_writer=repository,
        sql_read_enabled=False,
    )

    project_id: str = args.project_id
    session_id: str = args.session_id

    for i in range(max(1, args.turns)):
        ledger.record_chat_turn(
            project_id=project_id,
            session_id=session_id,
            request_id=f"bench_req_{i}",
            user_message=_build_message(i),
            assistant_answer="ok",
            used_input_tokens=64,
        )

    # Warm up once.
    first_page = repository.build_timeline(
        project_id=project_id,
        limit=args.timeline_limit,
    )
    repository.build_resume(project_id=project_id)

    # Resume: compare uncached vs cached.
    def _resume_uncached() -> None:
        repository.clear_read_caches(project_id=project_id)
        repository.build_resume(project_id=project_id)

    def _resume_cached() -> None:
        repository.build_resume(project_id=project_id)

    resume_uncached_ms = _measure_ms(_resume_uncached, args.resume_runs)
    resume_cached_ms = _measure_ms(_resume_cached, args.resume_runs)

    # Timeline latest page: compare uncached vs cached.
    def _timeline_latest_uncached() -> None:
        repository.clear_read_caches(project_id=project_id)
        repository.build_timeline(
            project_id=project_id,
            limit=args.timeline_limit,
        )

    def _timeline_latest_cached() -> None:
        repository.build_timeline(
            project_id=project_id,
            limit=args.timeline_limit,
        )

    timeline_latest_uncached_ms = _measure_ms(_timeline_latest_uncached, args.timeline_runs)
    timeline_latest_cached_ms = _measure_ms(_timeline_latest_cached, args.timeline_runs)

    # Timeline cursor page: compare uncached vs cached.
    cursor = first_page.get("next_cursor")
    timeline_cursor_uncached_ms: list[float] = []
    timeline_cursor_cached_ms: list[float] = []
    if cursor:
        def _timeline_cursor_uncached() -> None:
            repository.clear_read_caches(project_id=project_id)
            repository.build_timeline(
                project_id=project_id,
                limit=args.timeline_limit,
                cursor=cursor,
            )

        def _timeline_cursor_cached() -> None:
            repository.build_timeline(
                project_id=project_id,
                limit=args.timeline_limit,
                cursor=cursor,
            )

        timeline_cursor_uncached_ms = _measure_ms(_timeline_cursor_uncached, args.timeline_runs)
        timeline_cursor_cached_ms = _measure_ms(_timeline_cursor_cached, args.timeline_runs)

    resume_uncached = _summarize(resume_uncached_ms)
    resume_cached = _summarize(resume_cached_ms)
    timeline_latest_uncached = _summarize(timeline_latest_uncached_ms)
    timeline_latest_cached = _summarize(timeline_latest_cached_ms)
    timeline_cursor_uncached = _summarize(timeline_cursor_uncached_ms)
    timeline_cursor_cached = _summarize(timeline_cursor_cached_ms)

    payload = {
        "generated_at": _now_iso(),
        "config": {
            "project_id": project_id,
            "session_id": session_id,
            "turns": args.turns,
            "resume_runs": args.resume_runs,
            "timeline_runs": args.timeline_runs,
            "timeline_limit": args.timeline_limit,
            "db_path": str(db_path),
            "ledger_path": str(ledger_path),
            "json_out": str(json_out),
        },
        "metrics": {
            "resume": {
                "uncached": resume_uncached.as_dict(),
                "cached": resume_cached.as_dict(),
                "p95_speedup_ratio": _ratio(resume_uncached.p95_ms, resume_cached.p95_ms),
            },
            "timeline_latest": {
                "uncached": timeline_latest_uncached.as_dict(),
                "cached": timeline_latest_cached.as_dict(),
                "p95_speedup_ratio": _ratio(
                    timeline_latest_uncached.p95_ms,
                    timeline_latest_cached.p95_ms,
                ),
            },
            "timeline_cursor": {
                "cursor_enabled": bool(cursor),
                "uncached": timeline_cursor_uncached.as_dict(),
                "cached": timeline_cursor_cached.as_dict(),
                "p95_speedup_ratio": _ratio(
                    timeline_cursor_uncached.p95_ms,
                    timeline_cursor_cached.p95_ms,
                ),
            },
        },
    }

    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("SQL read benchmark completed")
    print(f"- output: {json_out}")
    print(
        f"- resume p95: uncached={resume_uncached.p95_ms}ms "
        f"cached={resume_cached.p95_ms}ms "
        f"speedup={payload['metrics']['resume']['p95_speedup_ratio']}x"
    )
    print(
        f"- timeline latest p95: uncached={timeline_latest_uncached.p95_ms}ms "
        f"cached={timeline_latest_cached.p95_ms}ms "
        f"speedup={payload['metrics']['timeline_latest']['p95_speedup_ratio']}x"
    )
    if cursor:
        print(
            f"- timeline cursor p95: uncached={timeline_cursor_uncached.p95_ms}ms "
            f"cached={timeline_cursor_cached.p95_ms}ms "
            f"speedup={payload['metrics']['timeline_cursor']['p95_speedup_ratio']}x"
        )
    else:
        print("- timeline cursor benchmark skipped (no next_cursor produced)")


if __name__ == "__main__":
    main()
